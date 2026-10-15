from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum


class MovementKind(str, Enum):
    DEBIT = "debito"
    CREDIT = "credito"
    PAYMENT = "pagamento_fatura"


@dataclass(frozen=True)
class StatementItem:
    purchase_date: date
    description: str
    amount: Decimal
    kind: MovementKind
    card_last_four: str
    page: int
    source_text: str
    installment_number: int | None = None
    installment_count: int | None = None
    original_amount: Decimal | None = None
    original_currency: str | None = None
    exchange_rate: Decimal | None = None


@dataclass(frozen=True)
class Statement:
    bank: str
    parser_version: str
    file_sha256: str
    due_date: date
    total: Decimal
    items: tuple[StatementItem, ...]
    warnings: tuple[str, ...] = ()
    currency: str = "BRL"

    @property
    def calculated_total(self) -> Decimal:
        return sum(
            (i.amount if i.kind == MovementKind.DEBIT else -i.amount
             for i in self.items if i.kind != MovementKind.PAYMENT),
            Decimal("0.00"),
        )

    @property
    def reconciled(self) -> bool:
        return self.total == self.calculated_total
