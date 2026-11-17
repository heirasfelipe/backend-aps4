"""Controller responsável pelas rotas HTTP de Eventos Acadêmicos (com proteção RBAC)."""
from typing import List, Optional
from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from database import get_db
from model.usuario import Usuario
from schema.evento_schema import EventoCreate, EventoUpdate, EventoResponse
from security.security import exigir_administrador
from service.evento_service import EventoService

router = APIRouter(prefix="/eventos", tags=["Eventos"])


@router.post(
    "",
    response_model=EventoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar um novo evento acadêmico [Admin]",
    description="Restrito a administradores. Recebe os dados de um evento, valida e persiste no SQLite.",
)
def cadastrar_evento(
    evento: EventoCreate,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(exigir_administrador),
):
    return EventoService.criar_evento(db, evento)


@router.get(
    "",
    response_model=List[EventoResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar todos os eventos [Público]",
    description="Rota pública. Retorna todos os eventos cadastrados, com filtro opcional por categoria.",
)
def listar_eventos(
    categoria: Optional[str] = Query(
        None,
        description="Filtrar eventos por categoria (ex: Palestra, Workshop)",
    ),
    db: Session = Depends(get_db),
):
    return EventoService.listar_eventos(db, categoria=categoria)


@router.get(
    "/{id}",
    response_model=EventoResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar evento por ID [Público]",
    description="Rota pública. Retorna os dados de um evento específico ou 404 caso não exista.",
)
def consultar_evento(
    id: int = Path(..., description="ID único do evento", gt=0),
    db: Session = Depends(get_db),
):
    return EventoService.buscar_por_id(db, id)


@router.put(
    "/{id}",
    response_model=EventoResponse,
    status_code=status.HTTP_200_OK,
    summary="Atualizar dados de um evento [Admin]",
    description="Restrito a administradores. Atualiza campos de um evento validando regras de capacidade.",
)
def atualizar_evento(
    id: int = Path(..., description="ID único do evento", gt=0),
    dados: EventoUpdate = ...,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(exigir_administrador),
):
    return EventoService.atualizar_evento(db, id, dados)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir um evento [Admin]",
    description="Restrito a administradores. Remove o evento e suas inscrições associadas em cascata.",
)
def excluir_evento(
    id: int = Path(..., description="ID único do evento", gt=0),
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(exigir_administrador),
):
    EventoService.excluir_evento(db, id)
    return None

