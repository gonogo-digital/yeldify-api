from __future__ import annotations
from datetime import date, timedelta
from src.domain.budgeting.budget import Budget
from src.domain.budgeting.money import Money
from src.domain.budgeting.cpf import CPF
from src.infrastructure.persistence.repositories import IBudgetRepository
from src.infrastructure.persistence.user_registry import get_user_registry


class CriarOrcamentoUseCase:
    def __init__(self, budget_repository: IBudgetRepository):
        self.budget_repository = budget_repository

    def execute(
        self,
        nome: str,
        categoria: str,
        valor: float,
        validade_meses: int,
        user_id: str,
        cpf: str,
    ) -> Budget:
        """
        Cria um novo orçamento.

        Args:
            nome: nome do orçamento (ex: "Alimentação")
            categoria: categoria do orçamento (ex: "Essencial")
            valor: limite do orçamento (em BRL)
            validade_meses: deve ser um de [1, 2, 3, 6, 9, 12]
            user_id: ID do usuário logado
            cpf: CPF do usuário (será validado)

        Returns:
            Budget: o orçamento criado
        """
        # 1. Validate inputs
        if not nome or not isinstance(nome, str):
            raise ValueError("nome must be a non-empty string")
        if not categoria or not isinstance(categoria, str):
            raise ValueError("categoria must be a non-empty string")
        if valor <= 0:
            raise ValueError("valor must be positive")
        if validade_meses not in [1, 2, 3, 6, 9, 12]:
            raise ValueError("validade_meses must be one of [1, 2, 3, 6, 9, 12]")
        if not user_id or not isinstance(user_id, str):
            raise ValueError("user_id must be a non-empty string")

        # 1.5 Validate CPF
        try:
            cpf_obj = CPF(cpf)
            cpf_normalizado = cpf_obj.valor
        except ValueError as exc:
            raise ValueError(f"CPF inválido: {exc}")

        # 1.6 Check if CPF is already registered to another user
        registry = get_user_registry()
        existing_user = registry.get_by_cpf(cpf_normalizado)
        if existing_user and existing_user.user_id != user_id:
            raise ValueError("CPF já cadastrado para outro usuário")

        # 1.7 Check duplicate name per user (active or archived)
        if self._budget_with_same_name_exists(user_id=user_id, nome=nome.strip()):
            raise ValueError("Já existe um orçamento com este nome")

        # 2. Calculate dates
        start_date = date.today()
        # Approximate month as 30 days; for production use relativedelta or calendar
        end_date = start_date + timedelta(days=30 * validade_meses)

        # 3. Create Budget entity
        budget = Budget(
            id=self._generate_id(),
            user_id=user_id,
            nome=nome,
            categoria=categoria,
            start_date=start_date,
            end_date=end_date,
            limite=Money(valor, "BRL"),  # assuming BRL for now
        )

        # 4. Persist
        self.budget_repository.save(budget)

        return budget

    def _budget_with_same_name_exists(self, user_id: str, nome: str) -> bool:
        """
        Check if there is already a budget (active or archived) with the
        same name for the user. Spec: "Não pode haver 2 orçamentos com mesmo nome".
        """
        for b in self.budget_repository.list_by_user_id(user_id, ativo=None):
            if b.nome == nome:
                return True
        return False

    @staticmethod
    def _generate_id() -> str:
        import uuid
        return str(uuid.uuid4())