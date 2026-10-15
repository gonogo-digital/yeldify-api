"""User routes for CPF validation."""
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from src.infrastructure.persistence.user_registry import get_user_registry, InMemoryUserRegistry
from src.domain.budgeting.cpf import CPF

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.get(
    "/cpf/{cpf}/existe",
    status_code=status.HTTP_200_OK,
    summary="Verifica se CPF já está cadastrado",
    description="Retorna true se o CPF já está associado a um usuário, false caso contrário.",
)
def verificar_cpf_existe(
    cpf: str = Path(..., description="CPF a ser verificado (apenas números ou formatado)"),
    registry: InMemoryUserRegistry = Depends(get_user_registry),
):
    """
    Verifica se um CPF já está cadastrado no sistema.

    Args:
        cpf: CPF a ser verificado (ex: "12345678901" ou "123.456.789-01")

    Returns:
        {"existe": true/false, "cpf": "12345678901"}
    """
    # Valida e normaliza o CPF
    try:
        cpf_obj = CPF(cpf)
        cpf_normalizado = cpf_obj.valor
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    existe = registry.cpf_exists(cpf_normalizado)

    return {
        "existe": existe,
        "cpf": cpf_normalizado,
    }


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Registra um novo usuário com CPF",
    description="Cria um novo usuário associando CPF. Retorna erro se CPF já existe.",
)
def registrar_usuario(
    user_id: str = Query(..., description="ID do usuário"),
    username: str = Query(..., description="Nome de usuário"),
    cpf: str = Query(..., description="CPF do usuário"),
    registry: InMemoryUserRegistry = Depends(get_user_registry),
):
    """
    Registra um novo usuário com CPF.

    Args:
        user_id: ID único do usuário
        username: Nome de usuário
        cpf: CPF do usuário

    Returns:
        Dados do usuário criado
    """
    try:
        cpf_obj = CPF(cpf)
        cpf_normalizado = cpf_obj.valor
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    try:
        user = registry.register_user(user_id=user_id, username=username, cpf=cpf_normalizado)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return {
        "user_id": user.user_id,
        "username": user.username,
        "cpf": user.cpf,
    }