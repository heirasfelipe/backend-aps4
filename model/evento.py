"""Modelo ORM SQLAlchemy para a entidade Evento."""
from sqlalchemy import CheckConstraint, Column, Integer, String, Text
from sqlalchemy.orm import relationship
from database import Base


class Evento(Base):
    """Entidade relacional que representa um evento acadêmico."""

    __tablename__ = "eventos"
    __table_args__ = (
        CheckConstraint("capacidade > 0", name="ck_eventos_capacidade_positiva"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    titulo = Column(String(150), nullable=False)
    descricao = Column(Text, nullable=False)
    data = Column(String(10), nullable=False)
    horario = Column(String(5), nullable=False)
    local = Column(String(200), nullable=False)
    capacidade = Column(Integer, nullable=False)
    categoria = Column(String(80), nullable=False, index=True)

    inscricoes = relationship(
        "Inscricao",
        back_populates="evento",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

