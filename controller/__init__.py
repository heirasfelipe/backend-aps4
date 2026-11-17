from .evento_controller import router as evento_router
from .participante_controller import router as participante_router
from .inscricao_controller import router as inscricao_router
from .relatorio_controller import router as relatorio_router
from .usuario_controller import router as usuario_router
from .auth_controller import router as auth_router

__all__ = [
    "evento_router",
    "participante_router",
    "inscricao_router",
    "relatorio_router",
    "usuario_router",
    "auth_router",
]

