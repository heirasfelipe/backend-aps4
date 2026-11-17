"""Camada de serviço responsável pelas regras de negócio e persistência de Inscrições."""
from typing import List, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from model.evento import Evento
from model.participante import Participante
from model.inscricao import Inscricao


class InscricaoService:
    """Serviço responsável pelo gerenciamento de inscrições de participantes em eventos."""

    @classmethod
    def inscrever_participante(
        cls,
        db: Session,
        evento_id: int,
        participante_id: int,
    ) -> Dict[str, Any]:
        evento = db.query(Evento).filter(Evento.id == evento_id).first()
        if not evento:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evento não encontrado.",
            )

        participante = db.query(Participante).filter(Participante.id == participante_id).first()
        if not participante:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Participante não encontrado.",
            )

        inscricao_existente = (
            db.query(Inscricao)
            .filter(
                Inscricao.evento_id == evento_id,
                Inscricao.participante_id == participante_id,
            )
            .first()
        )
        if inscricao_existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Participante já está inscrito neste evento.",
            )

        total_inscritos = (
            db.query(func.count(Inscricao.id))
            .filter(Inscricao.evento_id == evento_id)
            .scalar()
            or 0
        )
        if total_inscritos >= evento.capacidade:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Não existem vagas disponíveis para este evento.",
            )

        nova_inscricao = Inscricao(
            evento_id=evento_id,
            participante_id=participante_id,
        )

        try:
            db.add(nova_inscricao)
            db.commit()
            db.refresh(nova_inscricao)
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Participante já está inscrito neste evento.",
            )
        except SQLAlchemyError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno ao registrar a inscrição no banco de dados.",
            )

        return {
            "id": nova_inscricao.id,
            "evento_id": nova_inscricao.evento_id,
            "participante_id": nova_inscricao.participante_id,
            "data_inscricao": nova_inscricao.data_inscricao,
            "mensagem": "Inscrição realizada com sucesso!",
        }

    @classmethod
    def listar_inscritos_por_evento(cls, db: Session, evento_id: int) -> List[Inscricao]:
        evento = db.query(Evento).filter(Evento.id == evento_id).first()
        if not evento:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evento não encontrado.",
            )

        return (
            db.query(Inscricao)
            .options(joinedload(Inscricao.participante))
            .filter(Inscricao.evento_id == evento_id)
            .order_by(Inscricao.id)
            .all()
        )

    @classmethod
    def cancelar_inscricao(cls, db: Session, evento_id: int, participante_id: int) -> None:
        evento = db.query(Evento).filter(Evento.id == evento_id).first()
        if not evento:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evento não encontrado.",
            )

        participante = db.query(Participante).filter(Participante.id == participante_id).first()
        if not participante:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Participante não encontrado.",
            )

        inscricao = (
            db.query(Inscricao)
            .filter(
                Inscricao.evento_id == evento_id,
                Inscricao.participante_id == participante_id,
            )
            .first()
        )
        if not inscricao:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inscrição não encontrada para este participante neste evento.",
            )

        try:
            db.delete(inscricao)
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno ao cancelar a inscrição no banco de dados.",
            )

