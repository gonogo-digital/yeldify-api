"""CPF Value Object."""
from __future__ import annotations
import re


class CPF:
    """CPF value object with validation."""

    def __init__(self, valor: str) -> None:
        self._valor = self._validate(valor)

    @staticmethod
    def _validate(cpf: str) -> str:
        if not cpf:
            raise ValueError("CPF não pode ser vazio")

        # Remove formatação
        cpf_limpo = re.sub(r"[^\d]", "", cpf)

        if len(cpf_limpo) != 11:
            raise ValueError("CPF deve ter 11 dígitos")

        # Verifica dígitos repetidos (ex: 111.111.111-11)
        if len(set(cpf_limpo)) == 1:
            raise ValueError("CPF inválido")

        # Valida dígitos verificadores
        if not CPF._validar_digitos(cpf_limpo):
            raise ValueError("CPF inválido")

        return cpf_limpo

    @staticmethod
    def _validar_digitos(cpf: str) -> bool:
        """Valida os dois dígitos verificadores do CPF."""
        # Primeiro dígito
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        resto = (soma * 10) % 11
        if resto == 10:
            resto = 0
        if resto != int(cpf[9]):
            return False

        # Segundo dígito
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        resto = (soma * 10) % 11
        if resto == 10:
            resto = 0
        if resto != int(cpf[10]):
            return False

        return True

    @property
    def valor(self) -> str:
        return self._valor

    def formatado(self) -> str:
        """Retorna CPF formatado (XXX.XXX.XXX-XX)."""
        c = self._valor
        return f"{c[:3]}.{c[3:6]}.{c[6:9]}-{c[9:]}"

    def __str__(self) -> str:
        return self._valor

    def __repr__(self) -> str:
        return f"CPF('{self.formatado()}')"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CPF):
            return False
        return self._valor == other._valor

    def __hash__(self) -> int:
        return hash(self._valor)