"""Inter text-PDF adapter. Parsing never persists budget transactions."""

import hashlib
import re
from dataclasses import replace
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PyPdfError

from src.domain.billing.statement import MovementKind, Statement, StatementItem


MONEY = r"\d+(?:\.\d{3})*,\d{2}"
DATE = re.compile(r"^(\d{1,2}) de (\w+)\. (\d{4}) (.+)$")
CARD = re.compile(r"^CART\u00c3O \d{4}\*{4}(\d{4})$")
VALUE = re.compile(r"(?:^| )- (\+ )?R\$ (" + MONEY + r")$")
MONTHS = {name: i for i, name in enumerate(
    ("jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"), 1
)}


def decimal_br(value: str) -> Decimal:
    return Decimal(value.replace(".", "").replace(",", "."))


class InterStatementParser:
    version = "inter-v1"

    def parse(self, pdf: bytes) -> Statement:
        if not pdf.startswith(b"%PDF-"):
            raise ValueError("Arquivo PDF invalido.")
        try:
            reader = PdfReader(BytesIO(pdf))
            if reader.is_encrypted:
                raise ValueError("PDF protegido por senha nao suportado.")
            pages = tuple(page.extract_text() or "" for page in reader.pages)
        except (PyPdfError, OSError) as exc:
            raise ValueError("Nao foi possivel ler o PDF.") from exc
        return self.parse_pages(pages, hashlib.sha256(pdf).hexdigest())

    def parse_pages(self, pages: tuple[str, ...], file_sha256: str) -> Statement:
        pages = tuple("\n".join(" ".join(line.split()) for line in page.splitlines()) for page in pages)
        if not pages or not any(page.strip() for page in pages):
            raise ValueError("PDF sem texto extraivel; OCR necessario.")
        if not re.search(r"bancointer\.com\.br|Banco Inter|BANCO INTER", "\n".join(pages)):
            raise ValueError("Documento nao reconhecido como fatura do Banco Inter.")
        total = re.search(r"Total da sua fatura\s+R\$ (" + MONEY + ")", pages[0])
        due = re.search(r"Data de Vencimento\s+(\d{2}/\d{2}/\d{4})", pages[0])
        if not total or not due:
            raise ValueError("Resumo da fatura nao reconhecido.")
        items = []
        for page_number, text in enumerate(pages, 1):
            if "Despesas da fatura" not in text:
                continue
            card = None
            pending = []
            for line in text.split("Despesas da fatura", 1)[1].splitlines():
                if not line:
                    continue
                card_match = CARD.fullmatch(line)
                if card_match or line.startswith(("Total CART", "Pr\u00f3xima fatura")):
                    if pending:
                        raise ValueError(f"Movimentacao incompleta na pagina {page_number}.")
                    card = card_match[1] if card_match else None
                    if line.startswith("Pr\u00f3xima fatura"):
                        break
                    continue
                if line == "Data Movimenta\u00e7\u00e3o Benefici\u00e1rio Valor":
                    continue
                if DATE.match(line):
                    if pending:
                        raise ValueError(f"Movimentacao incompleta na pagina {page_number}.")
                    if card is None:
                        raise ValueError(f"Cartao ausente na pagina {page_number}.")
                    pending = [line]
                elif pending:
                    pending.append(line)
                else:
                    raise ValueError(f"Linha nao reconhecida na pagina {page_number}.")
                if VALUE.search(line):
                    items.append(self._item(pending, card, page_number))
                    pending = []
            if pending:
                raise ValueError(f"Movimentacao incompleta na pagina {page_number}.")
        if not items:
            raise ValueError("Nenhuma movimentacao reconhecida.")
        statement = Statement(
            bank="inter", parser_version=self.version, file_sha256=file_sha256,
            due_date=datetime.strptime(due[1], "%d/%m/%Y").date(),
            total=decimal_br(total[1]), items=tuple(items),
        )
        if not statement.reconciled:
            statement = replace(statement, warnings=(
                "Total das movimentacoes diverge da fatura; revisao obrigatoria.",
            ))
        return statement

    def _item(self, lines: list[str], card: str, page: int) -> StatementItem:
        start = DATE.fullmatch(lines[0])
        value = VALUE.search(lines[-1])
        try:
            purchase_date = date(int(start[3]), MONTHS[start[2]], int(start[1]))
        except (KeyError, ValueError) as exc:
            raise ValueError(f"Data invalida na pagina {page}.") from exc
        description = VALUE.sub("", start[4]).strip()
        extra_description = []
        original_amount = original_currency = exchange_rate = None
        for line in lines[1:]:
            if line.startswith("Valor e s\u00edmbolo da moeda de origem:"):
                match = re.fullmatch(r"Valor e s\u00edmbolo da moeda de origem: (" + MONEY + r") ([A-Z]{3})", line)
                if not match:
                    raise ValueError(f"Moeda de origem invalida na pagina {page}.")
                original_amount, original_currency = decimal_br(match[1]), match[2]
            elif line.startswith("Cota\u00e7\u00e3o do d\u00f3lar americano:"):
                match = re.fullmatch(r"Cota\u00e7\u00e3o do d\u00f3lar americano: R\$ (\d+,\d+)", line)
                if not match:
                    raise ValueError(f"Cotacao invalida na pagina {page}.")
                exchange_rate = decimal_br(match[1])
            elif not line.startswith("Valor em d\u00f3lar americano:"):
                continuation = VALUE.sub("", line).strip()
                if continuation:
                    extra_description.append(continuation)
        description = " ".join([description, *extra_description])
        installment = re.search(r"\(Parcela (\d+) de (\d+)\)", description)
        number, count = (int(installment[1]), int(installment[2])) if installment else (None, None)
        if installment and not 1 <= number <= count:
            raise ValueError(f"Parcela invalida na pagina {page}.")
        kind = MovementKind.CREDIT if value[1] else MovementKind.DEBIT
        if description in ("PAGAMENTO ON LINE", "PAGTO DEBITO AUTOMATICO"):
            if kind != MovementKind.CREDIT:
                raise ValueError(f"Sinal de pagamento inesperado na pagina {page}.")
            kind = MovementKind.PAYMENT
        return StatementItem(
            purchase_date=purchase_date, description=description,
            amount=decimal_br(value[2]), kind=kind, card_last_four=card,
            page=page, source_text="\n".join(lines),
            installment_number=number, installment_count=count,
            original_amount=original_amount, original_currency=original_currency,
            exchange_rate=exchange_rate,
        )
