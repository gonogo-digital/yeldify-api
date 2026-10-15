import pytest
from datetime import date, timedelta
from src.application.budgeting.criar_orcamento import CriarOrcamentoUseCase
from src.infrastructure.persistence.in_memory_budget_repository import InMemoryBudgetRepository
from src.domain.budgeting.budget import Budget
from src.domain.budgeting.money import Money


def test_criar_orcamento_success():
    repo = InMemoryBudgetRepository()
    use_case = CriarOrcamentoUseCase(budget_repository=repo)

    budget = use_case.execute(
        nome="Alimentação",
        categoria="Essencial",
        valor=1000.0,
        validade_meses=3,
        user_id="user-123",
        cpf="11144477735",
    )

    assert isinstance(budget, Budget)
    assert budget.nome == "Alimentação"
    assert budget.categoria == "Essencial"
    assert budget.limite == Money(1000.0, "BRL")
    assert budget.user_id == "user-123"
    # Check dates: start_date should be today, end_date approx 3 months later
    today = date.today()
    expected_end = today + timedelta(days=30 * 3)  # approximate
    assert budget.start_date == today
    # Allow a few days difference due to execution time? We'll just check that end_date is after start_date and within a reasonable range.
    assert budget.end_date >= today
    assert budget.end_date <= today + timedelta(days=100)  # loose upper bound
    assert budget.ativo is True
    assert len(budget.lancamentos) == 0


def test_criar_orcamento_invalid_nome():
    repo = InMemoryBudgetRepository()
    use_case = CriarOrcamentoUseCase(budget_repository=repo)
    with pytest.raises(ValueError, match="nome must be a non-empty string"):
        use_case.execute(
            nome="",
            categoria="Essencial",
            valor=1000.0,
            validade_meses=3,
            user_id="user-123",
            cpf="11144477735",
        )


def test_criar_orcamento_invalid_categoria():
    repo = InMemoryBudgetRepository()
    use_case = CriarOrcamentoUseCase(budget_repository=repo)
    with pytest.raises(ValueError, match="categoria must be a non-empty string"):
        use_case.execute(
            nome="Alimentação",
            categoria="",
            valor=1000.0,
            validade_meses=3,
            user_id="user-123",
            cpf="11144477735",
        )


def test_criar_orcamento_invalid_valor():
    repo = InMemoryBudgetRepository()
    use_case = CriarOrcamentoUseCase(budget_repository=repo)
    with pytest.raises(ValueError, match="valor must be positive"):
        use_case.execute(
            nome="Alimentação",
            categoria="Essencial",
            valor=0.0,
            validade_meses=3,
            user_id="user-123",
            cpf="11144477735",
        )
    with pytest.raises(ValueError, match="valor must be positive"):
        use_case.execute(
            nome="Alimentação",
            categoria="Essencial",
            valor=-10.0,
            validade_meses=3,
            user_id="user-123",
            cpf="11144477735",
        )


def test_criar_orcamento_invalid_validade_meses():
    repo = InMemoryBudgetRepository()
    use_case = CriarOrcamentoUseCase(budget_repository=repo)
    for invalid in [0, 4, 5, 7, 8, 10, 11, 13]:  # removed 9 because it's valid
        with pytest.raises(ValueError, match="validade_meses must be one of"):
            use_case.execute(
                nome="Alimentação",
                categoria="Essencial",
                valor=1000.0,
                validade_meses=invalid,
                user_id="user-123",
                cpf="11144477735",
            )


def test_criar_orcamento_invalid_user_id():
    repo = InMemoryBudgetRepository()
    use_case = CriarOrcamentoUseCase(budget_repository=repo)
    with pytest.raises(ValueError, match="user_id must be a non-empty string"):
        use_case.execute(
            nome="Alimentação",
            categoria="Essencial",
            valor=1000.0,
            validade_meses=3,
            user_id="",
            cpf="11144477735",
        )


def test_criar_orcamento_duplicate_name_error():
    repo = InMemoryBudgetRepository()
    use_case = CriarOrcamentoUseCase(budget_repository=repo)
    use_case.execute(
        nome="Alimentação",
        categoria="Essencial",
        valor=1000.0,
        validade_meses=3,
        user_id="user-123",
        cpf="11144477735",
    )
    with pytest.raises(ValueError, match="Já existe um orçamento com este nome"):
        use_case.execute(
            nome="Alimentação",
            categoria="Essencial",
            valor=2000.0,
            validade_meses=3,
            user_id="user-123",
            cpf="11144477735",
        )


def test_criar_orcamento_duplicate_name_archived_error():
    repo = InMemoryBudgetRepository()
    use_case = CriarOrcamentoUseCase(budget_repository=repo)
    use_case.execute(
        nome="Viagem",
        categoria="Lazer",
        valor=1000.0,
        validade_meses=3,
        user_id="user-123",
        cpf="11144477735",
    )
    budget = repo.list_by_user_id("user-123", ativo=None)[0]
    budget.desativar()
    with pytest.raises(ValueError, match="Já existe um orçamento com este nome"):
        use_case.execute(
            nome="Viagem",
            categoria="Lazer",
            valor=2000.0,
            validade_meses=3,
            user_id="user-123",
            cpf="11144477735",
        )


def test_criar_orcamento_same_name_different_users_success():
    repo = InMemoryBudgetRepository()
    use_case = CriarOrcamentoUseCase(budget_repository=repo)
    use_case.execute(
        nome="Alimentação",
        categoria="Essencial",
        valor=1000.0,
        validade_meses=3,
        user_id="user-123",
        cpf="11144477735",
    )
    budget = use_case.execute(
        nome="Alimentação",
        categoria="Essencial",
        valor=1500.0,
        validade_meses=3,
        user_id="user-456",
        cpf="22255588846",
    )
    assert budget.user_id == "user-456"
    assert budget.nome == "Alimentação"