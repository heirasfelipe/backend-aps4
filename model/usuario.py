"""Modelo ORM SQLAlchemy para a entidade Usuario (autenticação e controle de acesso)."""
from sqlalchemy import CheckConstraint, Column, Integer, String
from database import Base

PERFIL_USUARIO = "usuario"
PERFIL_ADMINISTRADOR = "administrador"


class Usuario(Base):
    """Entidade relacional que representa um usuário autenticado da API."""

    __tablename__ = "usuarios"
    __table_args__ = (
        CheckConstraint(
            "perfil IN ('usuario', 'administrador')",
            name="ck_usuarios_perfil_valido",
        ),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome = Column(String(150), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    senha_hash = Column(String(255), nullable=False)
    perfil = Column(String(30), nullable=False, default=PERFIL_USUARIO)

