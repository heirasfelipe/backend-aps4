"""Camada de serviço responsável pelo cadastro e gerenciamento seguro de Usuários."""
import os
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from model.usuario import PERFIL_ADMINISTRADOR, PERFIL_USUARIO, Usuario
from schema.usuario_schema import UsuarioCreate
from security.security import gerar_hash_senha


class UsuarioService:
    """Serviço de usuários com hashing Argon2 e controle seguro de perfis."""

    @classmethod
    def _criar_usuario_com_perfil(
        cls,
        db: Session,
        dados: UsuarioCreate,
        perfil: str,
    ) -> Usuario:
        """Método interno para criar usuário com perfil controlado pelo servidor."""
        email_normalizado = str(dados.email).lower().strip()

        existente = (
            db.query(Usuario)
            .filter(func.lower(Usuario.email) == email_normalizado)
            .first()
        )
        if existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe um usuário cadastrado com este e-mail.",
            )

        novo_usuario = Usuario(
            nome=dados.nome,
            email=email_normalizado,
            senha_hash=gerar_hash_senha(dados.senha),
            perfil=perfil,
        )

        try:
            db.add(novo_usuario)
            db.commit()
            db.refresh(novo_usuario)
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe um usuário cadastrado com este e-mail.",
            )
        except SQLAlchemyError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno ao cadastrar o usuário no banco de dados.",
            )

        return novo_usuario

    @classmethod
    def criar_usuario_comum(cls, db: Session, dados: UsuarioCreate) -> Usuario:
        """
        Cadastra um usuário pela rota pública POST /usuarios.
        Força sempre perfil='usuario', impedindo auto-elevação de privilégios.
        """
        return cls._criar_usuario_com_perfil(db, dados, perfil=PERFIL_USUARIO)

    @classmethod
    def criar_administrador(cls, db: Session, dados: UsuarioCreate) -> Usuario:
        """
        Cadastra um novo administrador por meio de procedimento controlado
        (rota restrita a administradores já autenticados ou script criar_admin.py).
        """
        return cls._criar_usuario_com_perfil(db, dados, perfil=PERFIL_ADMINISTRADOR)

    @classmethod
    def listar_usuarios(cls, db: Session) -> List[Usuario]:
        """Lista todos os usuários cadastrados (restrito a administradores)."""
        return db.query(Usuario).order_by(Usuario.id).all()

    @classmethod
    def inicializar_admin_por_env(cls, db: Session) -> Optional[Usuario]:
        """
        Estratégia controlada de bootstrap do administrador inicial:
        Cria o administrador apenas se ADMIN_EMAIL e ADMIN_SENHA estiverem definidos
        no ambiente/.env e o e-mail ainda não existir no banco.
        """
        admin_email = os.getenv("ADMIN_EMAIL", "").strip().lower()
        admin_senha = os.getenv("ADMIN_SENHA", "").strip()
        admin_nome = os.getenv("ADMIN_NOME", "Administrador do Sistema").strip() or "Administrador do Sistema"

        if not admin_email or not admin_senha or len(admin_senha) < 6:
            return None

        existente = db.query(Usuario).filter(func.lower(Usuario.email) == admin_email).first()
        if existente:
            return existente

        admin = Usuario(
            nome=admin_nome,
            email=admin_email,
            senha_hash=gerar_hash_senha(admin_senha),
            perfil=PERFIL_ADMINISTRADOR,
        )
        try:
            db.add(admin)
            db.commit()
            db.refresh(admin)
            return admin
        except SQLAlchemyError:
            db.rollback()
            return None

