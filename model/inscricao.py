"""Modelo ORM SQLAlchemy para a entidade Inscricao."""
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base


class Inscricao(Base):
    """Entidade associativa que relaciona Participante e Evento."""

    __tablename__ = "inscricoes"
    __table_args__ = (
        UniqueConstraint("evento_id", "participante_id", name="uq_evento_participante"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    evento_id = Column(
        Integer,
        ForeignKey("eventos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    participante_id = Column(
        Integer,
        ForeignKey("participantes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    data_inscricao = Column(DateTime, nullable=False, default=datetime.now)

    evento = relationship("Evento", back_populates="inscricoes")
    participante = relationship("Participante", back_populates="inscricoes")

