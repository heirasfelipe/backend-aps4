"""Camada de serviço responsável pela autenticação de usuários e emissão de tokens JWT."""
from typing import Dict
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from model.usuario import Usuario
from schema.usuario_schema import LoginRequest
from security.security import criar_token_acesso, verificar_senha


class AuthService:
    """Serviço de login e verificação segura de credenciais."""

    @classmethod
    def autenticar_usuario(cls, db: Session, credenciais: LoginRequest) -> Dict[str, str]:
        """
        Autentica o usuário por e-mail e senha verificando o hash Argon2.
        Retorna 401 Unauthorized genérico caso o e-mail não exista ou a senha esteja incorreta,
        sem revelar qual dos campos falhou.
        """
        email_normalizado = str(credenciais.email).lower().strip()
        usuario = (
            db.query(Usuario)
            .filter(func.lower(Usuario.email) == email_normalizado)
            .first()
        )

        if not usuario or not verificar_senha(credenciais.senha, usuario.senha_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="E-mail ou senha inválidos.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = criar_token_acesso(usuario)
        return {
            "access_token": token,
            "token_type": "bearer",
        }

