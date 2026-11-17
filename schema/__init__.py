from .evento_schema import EventoBase, EventoCreate, EventoUpdate, EventoResponse
from .participante_schema import (
    ParticipanteBase,
    ParticipanteCreate,
    ParticipanteUpdate,
    ParticipanteResponse,
)
from .inscricao_schema import InscricaoResponse, DetalhesInscricaoResponse
from .relatorio_schema import (
    RelatorioOcupacaoEventoResponse,
    RelatorioCategoriaEventoResponse,
    RelatorioParticipacaoCursoResponse,
)
from .usuario_schema import (
    UsuarioCreate,
    UsuarioResponse,
    LoginRequest,
    TokenResponse,
)

__all__ = [
    "EventoBase",
    "EventoCreate",
    "EventoUpdate",
    "EventoResponse",
    "ParticipanteBase",
    "ParticipanteCreate",
    "ParticipanteUpdate",
    "ParticipanteResponse",
    "InscricaoResponse",
    "DetalhesInscricaoResponse",
    "RelatorioOcupacaoEventoResponse",
    "RelatorioCategoriaEventoResponse",
    "RelatorioParticipacaoCursoResponse",
    "UsuarioCreate",
    "UsuarioResponse",
    "LoginRequest",
    "TokenResponse",
]

