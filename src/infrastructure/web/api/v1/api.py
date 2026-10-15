from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from src.infrastructure.web.api.v1.routes.auth import router as auth_router
from src.infrastructure.web.api.v1.routes.despesas import router as despesas_router
from src.infrastructure.web.api.v1.routes.orcamentos import router as orcamentos_router
from src.infrastructure.web.api.v1.routes.receitas import router as receitas_router
from src.infrastructure.web.api.v1.routes.transacoes import router as transacoes_router
from src.infrastructure.web.api.v1.routes.dashboard import router as dashboard_router
from src.infrastructure.web.api.v1.routes.usuarios import router as usuarios_router


def _maybe_seed_demo_data() -> None:
    """Popula dados de demonstração no startup se SEED_DEMO=true (dev)."""
    if os.getenv("SEED_DEMO", "false").lower() != "true":
        return
    from src.infrastructure.persistence.repository_factory import create_repository
    from src.infrastructure.persistence.seed import DEFAULT_USER_ID, seed_demo

    repo = create_repository()
    if seed_demo(repo, user_id=DEFAULT_USER_ID):
        print(f"[seed] Dados de demonstração aplicados para {DEFAULT_USER_ID}.")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Yeldify API",
        version="0.1.0",
        description="API for personal finance manager (budget + portfolio)",
    )
    _cors_origins = [
        o.strip()
        for o in os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ).split(",")
        if o.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(auth_router)
    app.include_router(despesas_router)
    app.include_router(orcamentos_router)
    app.include_router(receitas_router)
    app.include_router(transacoes_router)
    app.include_router(dashboard_router)
    app.include_router(usuarios_router)
    _maybe_seed_demo_data()
    return app


app = create_app()