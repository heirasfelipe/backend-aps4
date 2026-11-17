"""Camada de serviço responsável pelas regras de negócio e persistência de Participantes."""
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from model.participante import Participante
from schema.participante_schema import ParticipanteCreate, ParticipanteUpdate


class ParticipanteService:
    """Serviço com operações CRUD e regras de negócio de Participantes usando SQLAlchemy."""

    @classmethod
    def criar_participante(cls, db: Session, dados: ParticipanteCreate) -> Participante:
        email_normalizado = str(dados.email).lower().strip()

        existente = (
            db.query(Participante)
            .filter(func.lower(Participante.email) == email_normalizado)
            .first()
        )
        if existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe um participante cadastrado com este e-mail.",
            )

        novo_participante = Participante(
            nome=dados.nome,
            email=email_normalizado,
            curso=dados.curso,
        )

        try:
            db.add(novo_participante)
            db.commit()
            db.refresh(novo_participante)
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe um participante cadastrado com este e-mail.",
            )
        except SQLAlchemyError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno ao cadastrar o participante no banco de dados.",
            )

        return novo_participante

    @classmethod
    def listar_participantes(cls, db: Session, curso: Optional[str] = None) -> List[Participante]:
        consulta = db.query(Participante)
        if curso:
            consulta = consulta.filter(func.lower(Participante.curso) == curso.strip().lower())
        return consulta.order_by(Participante.id).all()

    @classmethod
    def buscar_por_id(cls, db: Session, participante_id: int) -> Participante:
        participante = db.query(Participante).filter(Participante.id == participante_id).first()
        if not participante:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Participante não encontrado.",
            )
        return participante

    @classmethod
    def atualizar_participante(
        cls,
        db: Session,
        participante_id: int,
        dados: ParticipanteUpdate,
    ) -> Participante:
        participante = db.query(Participante).filter(Participante.id == participante_id).first()
        if not participante:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Participante não encontrado.",
            )

        dados_dict = dados.model_dump(exclude_unset=True)

        if "email" in dados_dict:
            novo_email = str(dados_dict["email"]).lower().strip()
            duplicado = (
                db.query(Participante)
                .filter(
                    Participante.id != participante_id,
                    func.lower(Participante.email) == novo_email,
                )
                .first()
            )
            if duplicado:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Já existe um participante cadastrado com este e-mail.",
                )
            dados_dict["email"] = novo_email

        for campo, valor in dados_dict.items():
            setattr(participante, campo, valor)

        try:
            db.commit()
            db.refresh(participante)
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe um participante cadastrado com este e-mail.",
            )
        except SQLAlchemyError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno ao atualizar o participante no banco de dados.",
            )

        return participante

    @classmethod
    def excluir_participante(cls, db: Session, participante_id: int) -> None:
        participante = db.query(Participante).filter(Participante.id == participante_id).first()
        if not participante:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Participante não encontrado.",
            )

        try:
            db.delete(participante)
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno ao excluir o participante no banco de dados.",
            )

