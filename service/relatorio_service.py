"""Camada de serviço responsável pelas consultas consolidadas e relatórios com SQLAlchemy."""
from typing import List, Dict, Any
from sqlalchemy import func
from sqlalchemy.orm import Session

from model.evento import Evento
from model.participante import Participante
from model.inscricao import Inscricao


class RelatorioService:
    """Serviço de agregação e consolidação de dados diretamente no SQLite via SQLAlchemy."""

    @classmethod
    def relatorio_ocupacao_eventos(cls, db: Session) -> List[Dict[str, Any]]:
        resultados = (
            db.query(
                Evento.id.label("evento_id"),
                Evento.titulo.label("titulo"),
                Evento.capacidade.label("capacidade"),
                func.count(Inscricao.id).label("total_inscritos"),
            )
            .outerjoin(Inscricao, Evento.id == Inscricao.evento_id)
            .group_by(Evento.id, Evento.titulo, Evento.capacidade)
            .order_by(Evento.id)
            .all()
        )

        relatorio = []
        for linha in resultados:
            capacidade = int(linha.capacidade)
            total_inscritos = int(linha.total_inscritos)
            vagas_disponiveis = max(0, capacidade - total_inscritos)
            percentual_ocupacao = (
                round((total_inscritos / capacidade) * 100.0, 2) if capacidade > 0 else 0.0
            )
            relatorio.append(
                {
                    "evento_id": linha.evento_id,
                    "titulo": linha.titulo,
                    "capacidade": capacidade,
                    "total_inscritos": total_inscritos,
                    "vagas_disponiveis": vagas_disponiveis,
                    "percentual_ocupacao": percentual_ocupacao,
                }
            )
        return relatorio

    @classmethod
    def relatorio_eventos_por_categoria(cls, db: Session) -> List[Dict[str, Any]]:
        inscricoes_por_evento = (
            db.query(
                Inscricao.evento_id.label("evento_id"),
                func.count(Inscricao.id).label("qtd_inscricoes"),
            )
            .group_by(Inscricao.evento_id)
            .subquery()
        )

        resultados = (
            db.query(
                Evento.categoria.label("categoria"),
                func.count(Evento.id).label("total_eventos"),
                func.coalesce(func.sum(Evento.capacidade), 0).label("capacidade_total"),
                func.coalesce(
                    func.sum(func.coalesce(inscricoes_por_evento.c.qtd_inscricoes, 0)), 0
                ).label("total_inscricoes"),
            )
            .outerjoin(inscricoes_por_evento, Evento.id == inscricoes_por_evento.c.evento_id)
            .group_by(Evento.categoria)
            .order_by(Evento.categoria)
            .all()
        )

        return [
            {
                "categoria": linha.categoria,
                "total_eventos": int(linha.total_eventos),
                "capacidade_total": int(linha.capacidade_total),
                "total_inscricoes": int(linha.total_inscricoes),
            }
            for linha in resultados
        ]

    @classmethod
    def relatorio_participacao_por_curso(cls, db: Session) -> List[Dict[str, Any]]:
        resultados = (
            db.query(
                Participante.curso.label("curso"),
                func.count(func.distinct(Participante.id)).label("total_participantes"),
                func.count(Inscricao.id).label("total_inscricoes"),
            )
            .outerjoin(Inscricao, Participante.id == Inscricao.participante_id)
            .group_by(Participante.curso)
            .order_by(Participante.curso)
            .all()
        )

        return [
            {
                "curso": linha.curso,
                "total_participantes": int(linha.total_participantes),
                "total_inscricoes": int(linha.total_inscricoes),
            }
            for linha in resultados
        ]

