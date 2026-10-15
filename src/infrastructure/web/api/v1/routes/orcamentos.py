from fastapi import APIRouter, Depends, HTTPException, Query, status, Header
from src.infrastructure.web.api.v1.schemas.orcamento_schema import OrcamentoResponse, OrcamentoListResponse
from src.infrastructure.web.api.v1.schemas.orcamento_update_schema import OrcamentoUpdate
from src.infrastructure.web.api.v1.schemas.orcamento_create_schema import OrcamentoCreate
from src.application.budgeting.list_orcamentos import ListarOrcamentosUseCase
from src.application.budgeting.editar_orcamento import EditarOrcamentoUseCase
from src.application.budgeting.criar_orcamento import CriarOrcamentoUseCase
from src.infrastructure.web.api.v1.dependencies import get_listar_orcamentos_use_case, get_editar_orcamento_use_case, get_criar_orcamento_use_case
from src.infrastructure.web.api.v1.auth.jwt_auth import get_user_id_from_token_or_query

router = APIRouter(prefix="/orcamentos", tags=["orcamentos"])

def _to_response(budget) -> OrcamentoResponse:
    return OrcamentoResponse(
        id=budget.id,
        nome=budget.nome,
        categoria=budget.categoria,
        valor_restante=float(budget.saldo.amount),
        valor_planejado=float(budget.limite.amount),
        gasto=float(budget.gasto.amount),
        data_criacao=budget.created_at,
        ativo=budget.ativo,
        nota_governanca=budget.nota_governanca,
    )

@router.post(
    "/",
    response_model=OrcamentoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo orçamento",
)
def criar_orcamento(
    payload: OrcamentoCreate,
    authorization: str = Header(None, alias="Authorization"),
    user_id: str = Query(None, description="ID do usuário (dev only, prefer Authorization header)"),
    use_case: CriarOrcamentoUseCase = Depends(get_criar_orcamento_use_case),
):
    # Extract user_id from JWT token or query param
    effective_user_id = get_user_id_from_token_or_query(authorization, user_id)
    
    try:
        budget = use_case.execute(
            nome=payload.nome,
            categoria=payload.categoria,
            valor=payload.valor,
            validade_meses=payload.validade_meses,
            user_id=effective_user_id,
            cpf=payload.cpf,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from exc

    return _to_response(budget)


@router.get(
    "/",
    response_model=OrcamentoListResponse,
    status_code=status.HTTP_200_OK,
    summary="Lista orçamentos de um usuário com ordenação e paginação",
)
def listar_orcamentos(
    authorization: str = Header(None, alias="Authorization"),
    user_id: str = Query(None, description="ID do usuário (dev only, prefer Authorization header)"),
    sort_by: str = Query("nome", description="Campo para ordenação: nome, valor_restante, valor_planejado, data_criacao"),
    pasta: str = Query("ativos", description="Filtro pelo status: ativos (padrão), arquivados ou todos"),
    page: int = Query(1, ge=1, description="Número da página (começando em 1)"),
    page_size: int = Query(10, ge=1, description="Itens por página"),
    use_case: ListarOrcamentosUseCase = Depends(get_listar_orcamentos_use_case),
):
    # Extract user_id from JWT token or query param
    effective_user_id = get_user_id_from_token_or_query(authorization, user_id)

    ativo_map = {"ativos": True, "arquivados": False, "todos": None}
    if pasta not in ativo_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="pasta must be one of: ativos, arquivados, todos",
        )
    ativo = ativo_map[pasta]

    try:
        result = use_case.execute(
            user_id=effective_user_id,
            sort_by=sort_by,
            ativo=ativo,
            page=page,
            page_size=page_size,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from exc

    # Map Budget objects to response schema
    return OrcamentoListResponse(
        items=[_to_response(b) for b in result.items],
        total=result.total,
        page=page,
        page_size=page_size,
    )


@router.put(
    "/{budget_id}",
    response_model=OrcamentoResponse,
    status_code=status.HTTP_200_OK,
    summary="Edita um orçamento existente",
)
def editar_orcamento(
    budget_id: str,
    payload: OrcamentoUpdate,
    authorization: str = Header(None, alias="Authorization"),
    user_id: str = Query(None, description="ID do usuário (dev only, prefer Authorization header)"),
    use_case: EditarOrcamentoUseCase = Depends(get_editar_orcamento_use_case),
):
    # Extract user_id from JWT token or query param
    effective_user_id = get_user_id_from_token_or_query(authorization, user_id)
    
    try:
        budget = use_case.execute(
            budget_id=budget_id,
            user_id=effective_user_id,
            nome=payload.nome,
            valor=payload.valor,
            validade_meses=payload.validade_meses,
            ativo=payload.ativo,
            nota_governanca=payload.nota_governanca,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from exc

    return _to_response(budget)