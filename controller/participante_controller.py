"""Controller responsável pelas rotas HTTP de Participantes (protegidas por JWT e RBAC)."""
from typing import List, Optional
from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from database import get_db
from model.usuario import Usuario
from schema.participante_schema import (
    ParticipanteCreate,
    ParticipanteUpdate,
    ParticipanteResponse,
)
from security.security import exigir_administrador, obter_usuario_atual
from service.participante_service import ParticipanteService

router = APIRouter(prefix="/participantes", tags=["Participantes"])


@router.post(
    "",
    response_model=ParticipanteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar um novo participante [Autenticado]",
    description="Requer autenticação (Bearer JWT). Valida e persiste um novo participante com e-mail único.",
)
def cadastrar_participante(
    participante: ParticipanteCreate,
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(obter_usuario_atual),
):
    return ParticipanteService.criar_participante(db, participante)


@router.get(
    "",
    response_model=List[ParticipanteResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar todos os participantes [Autenticado]",
    description="Requer autenticação (Bearer JWT). Retorna participantes com filtro opcional por curso.",
)
def listar_participantes(
    curso: Optional[str] = Query(
        None,
        description="Filtrar participantes por curso (ex: Engenharia de Software)",
    ),
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(obter_usuario_atual),
):
    return ParticipanteService.listar_participantes(db, curso=curso)


@router.get(
    "/{id}",
    response_model=ParticipanteResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar participante por ID [Autenticado]",
    description="Requer autenticação (Bearer JWT). Retorna os dados cadastrais de um participante.",
)
def consultar_participante(
    id: int = Path(..., description="ID único do participante", gt=0),
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(obter_usuario_atual),
):
    return ParticipanteService.buscar_por_id(db, id)


@router.put(
    "/{id}",
    response_model=ParticipanteResponse,
    status_code=status.HTTP_200_OK,
    summary="Atualizar dados do participante [Autenticado]",
    description="Requer autenticação (Bearer JWT). Atualiza dados cadastrais mantendo e-mail único.",
)
def atualizar_participante(
    id: int = Path(..., description="ID único do participante", gt=0),
    dados: ParticipanteUpdate = ...,
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(obter_usuario_atual),
):
    return ParticipanteService.atualizar_participante(db, id, dados)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir participante [Admin]",
    description="Restrito a administradores. Remove o participante e suas inscrições associadas em cascata.",
)
def excluir_participante(
    id: int = Path(..., description="ID único do participante", gt=0),
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(exigir_administrador),
):
    ParticipanteService.excluir_participante(db, id)
    return None

