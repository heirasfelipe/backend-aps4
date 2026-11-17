"""Controller responsável pelas rotas HTTP de Relatórios Consolidados (restritas a Admin)."""
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from model.usuario import Usuario
from schema.relatorio_schema import (
    RelatorioOcupacaoEventoResponse,
    RelatorioCategoriaEventoResponse,
    RelatorioParticipacaoCursoResponse,
)
from security.security import exigir_administrador
from service.relatorio_service import RelatorioService

router = APIRouter(prefix="/relatorios", tags=["Relatórios"])


@router.get(
    "/eventos/ocupacao",
    response_model=List[RelatorioOcupacaoEventoResponse],
    status_code=status.HTTP_200_OK,
    summary="Relatório de ocupação dos eventos [Admin]",
    description="Restrito a administradores. Consolida capacidade, inscritos, vagas e percentual por evento.",
)
def relatorio_ocupacao_eventos(
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(exigir_administrador),
):
    return RelatorioService.relatorio_ocupacao_eventos(db)


@router.get(
    "/eventos/categorias",
    response_model=List[RelatorioCategoriaEventoResponse],
    status_code=status.HTTP_200_OK,
    summary="Relatório de eventos por categoria [Admin]",
    description="Restrito a administradores. Consolida quantidade de eventos, capacidade e inscrições por categoria.",
)
def relatorio_eventos_por_categoria(
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(exigir_administrador),
):
    return RelatorioService.relatorio_eventos_por_categoria(db)


@router.get(
    "/participantes/cursos",
    response_model=List[RelatorioParticipacaoCursoResponse],
    status_code=status.HTTP_200_OK,
    summary="Relatório de participação por curso [Admin]",
    description="Restrito a administradores. Consolida participantes únicos e inscrições agrupados por curso.",
)
def relatorio_participacao_por_curso(
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(exigir_administrador),
):
    return RelatorioService.relatorio_participacao_por_curso(db)

