"""Schemas Pydantic para os relatórios consolidados da API."""
from pydantic import BaseModel, Field


class RelatorioOcupacaoEventoResponse(BaseModel):
    """Item do relatório de ocupação de vagas por evento."""

    evento_id: int = Field(..., description="Identificador único do evento")
    titulo: str = Field(..., description="Título do evento")
    capacidade: int = Field(..., description="Capacidade total do evento")
    total_inscritos: int = Field(..., description="Quantidade de participantes inscritos")
    vagas_disponiveis: int = Field(..., description="Quantidade de vagas restantes")
    percentual_ocupacao: float = Field(..., description="Percentual de ocupação das vagas (0.0 a 100.0)")


class RelatorioCategoriaEventoResponse(BaseModel):
    """Item do relatório consolidado de eventos por categoria."""

    categoria: str = Field(..., description="Nome da categoria")
    total_eventos: int = Field(..., description="Quantidade de eventos cadastrados nessa categoria")
    capacidade_total: int = Field(..., description="Soma das capacidades dos eventos da categoria")
    total_inscricoes: int = Field(..., description="Total de inscrições realizadas nos eventos da categoria")


class RelatorioParticipacaoCursoResponse(BaseModel):
    """Item do relatório consolidado de participação por curso."""

    curso: str = Field(..., description="Nome do curso")
    total_participantes: int = Field(..., description="Quantidade única de participantes cadastrados no curso")
    total_inscricoes: int = Field(..., description="Total de inscrições realizadas por participantes desse curso")

