"""Modelo ORM SQLAlchemy para a entidade Participante."""
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database import Base


class Participante(Base):
    """Entidade relacional que representa um participante de eventos acadêmicos."""

    __tablename__ = "participantes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome = Column(String(150), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    curso = Column(String(100), nullable=False, index=True)

    inscricoes = relationship(
        "Inscricao",
        back_populates="participante",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

