"""Camada de serviço responsável pelas regras de negócio e persistência de Eventos."""
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from model.evento import Evento
from model.inscricao import Inscricao
from schema.evento_schema import EventoCreate, EventoUpdate


class EventoService:
    """Serviço com operações CRUD e regras de negócio de Eventos usando SQLAlchemy."""

    @staticmethod
    def _montar_resposta_evento(evento: Evento, total_inscritos: int) -> Dict[str, Any]:
        vagas_disponiveis = max(0, evento.capacidade - total_inscritos)
        return {
            "id": evento.id,
            "titulo": evento.titulo,
            "descricao": evento.descricao,
            "data": evento.data,
            "horario": evento.horario,
            "local": evento.local,
            "capacidade": evento.capacidade,
            "categoria": evento.categoria,
            "total_inscritos": total_inscritos,
            "vagas_disponiveis": vagas_disponiveis,
        }

    @classmethod
    def criar_evento(cls, db: Session, dados: EventoCreate) -> Dict[str, Any]:
        novo_evento = Evento(
            titulo=dados.titulo,
            descricao=dados.descricao,
            data=dados.data,
            horario=dados.horario,
            local=dados.local,
            capacidade=dados.capacidade,
            categoria=dados.categoria,
        )
        try:
            db.add(novo_evento)
            db.commit()
            db.refresh(novo_evento)
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Não foi possível cadastrar o evento devido a um conflito de integridade dos dados.",
            )
        except SQLAlchemyError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno ao persistir o evento no banco de dados.",
            )

        return cls._montar_resposta_evento(novo_evento, total_inscritos=0)

    @classmethod
    def listar_eventos(cls, db: Session, categoria: Optional[str] = None) -> List[Dict[str, Any]]:
        consulta = (
            db.query(Evento, func.count(Inscricao.id).label("total_inscritos"))
            .outerjoin(Inscricao, Evento.id == Inscricao.evento_id)
        )

        if categoria:
            consulta = consulta.filter(func.lower(Evento.categoria) == categoria.strip().lower())

        resultados = consulta.group_by(Evento.id).order_by(Evento.id).all()
        return [cls._montar_resposta_evento(evento, int(total)) for evento, total in resultados]

    @classmethod
    def buscar_por_id(cls, db: Session, evento_id: int) -> Dict[str, Any]:
        resultado = (
            db.query(Evento, func.count(Inscricao.id).label("total_inscritos"))
            .outerjoin(Inscricao, Evento.id == Inscricao.evento_id)
            .filter(Evento.id == evento_id)
            .group_by(Evento.id)
            .first()
        )
        if not resultado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evento não encontrado.",
            )

        evento, total_inscritos = resultado
        return cls._montar_resposta_evento(evento, int(total_inscritos))

    @classmethod
    def atualizar_evento(cls, db: Session, evento_id: int, dados: EventoUpdate) -> Dict[str, Any]:
        evento = db.query(Evento).filter(Evento.id == evento_id).first()
        if not evento:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evento não encontrado.",
            )

        dados_dict = dados.model_dump(exclude_unset=True)
        total_inscritos = (
            db.query(func.count(Inscricao.id))
            .filter(Inscricao.evento_id == evento_id)
            .scalar()
            or 0
        )

        if "capacidade" in dados_dict and dados_dict["capacidade"] < total_inscritos:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"A nova capacidade ({dados_dict['capacidade']}) não pode ser inferior "
                    f"ao número de inscritos atuais ({total_inscritos})."
                ),
            )

        for campo, valor in dados_dict.items():
            setattr(evento, campo, valor)

        try:
            db.commit()
            db.refresh(evento)
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Não foi possível atualizar o evento devido a um conflito de integridade.",
            )
        except SQLAlchemyError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno ao atualizar o evento no banco de dados.",
            )

        return cls._montar_resposta_evento(evento, int(total_inscritos))

    @classmethod
    def excluir_evento(cls, db: Session, evento_id: int) -> None:
        evento = db.query(Evento).filter(Evento.id == evento_id).first()
        if not evento:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evento não encontrado.",
            )

        try:
            db.delete(evento)
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno ao excluir o evento no banco de dados.",
            )

