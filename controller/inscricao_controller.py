"""Controller responsável pelas rotas HTTP de Inscrições em Eventos (protegidas por JWT)."""
from typing import List
from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session

from database import get_db
from model.usuario import Usuario
from schema.inscricao_schema import InscricaoResponse, DetalhesInscricaoResponse
from security.security import obter_usuario_atual
from service.inscricao_service import InscricaoService

router = APIRouter(prefix="/eventos", tags=["Inscrições"])


@router.post(
    "/{evento_id}/inscricoes/{participante_id}",
    response_model=InscricaoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Inscrever participante em um evento [Autenticado]",
    description=(
        "Requer autenticação (Bearer JWT). Disponível para usuários autenticados "
        "(comum ou administrador) respeitando todas as regras de vagas e duplicidade."
    ),
)
def inscrever_participante(
    evento_id: int = Path(..., description="ID do evento acadêmico", gt=0),
    participante_id: int = Path(..., description="ID do participante", gt=0),
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(obter_usuario_atual),
):
    return InscricaoService.inscrever_participante(db, evento_id, participante_id)


@router.get(
    "/{evento_id}/inscricoes",
    response_model=List[DetalhesInscricaoResponse],
    status_code=status.HTTP_200_OK,
    summary="Consultar participantes inscritos no evento [Autenticado]",
    description="Requer autenticação (Bearer JWT). Lista inscritos utilizando relacionamentos SQLAlchemy.",
)
def listar_inscritos(
    evento_id: int = Path(..., description="ID do evento acadêmico", gt=0),
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(obter_usuario_atual),
):
    return InscricaoService.listar_inscritos_por_evento(db, evento_id)


@router.delete(
    "/{evento_id}/inscricoes/{participante_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancelar inscrição de um participante [Autenticado]",
    description="Requer autenticação (Bearer JWT). Cancela a inscrição e libera a vaga no evento.",
)
def cancelar_inscricao(
    evento_id: int = Path(..., description="ID do evento acadêmico", gt=0),
    participante_id: int = Path(..., description="ID do participante", gt=0),
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(obter_usuario_atual),
):
    InscricaoService.cancelar_inscricao(db, evento_id, participante_id)
    return None

