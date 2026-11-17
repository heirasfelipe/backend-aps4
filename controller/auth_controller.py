"""Controller responsável pelas rotas de Autenticação JWT (/auth/login e /auth/me)."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from model.usuario import Usuario
from schema.usuario_schema import LoginRequest, TokenResponse, UsuarioResponse
from security.security import obter_usuario_atual
from service.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Autenticar usuário e obter token JWT [Público]",
    description=(
        "Valida e-mail e senha utilizando o hash Argon2 armazenado no SQLite. "
        "Em caso de sucesso, retorna um token JWT Bearer com prazo de validade configurado."
    ),
)
def login(credenciais: LoginRequest, db: Session = Depends(get_db)):
    return AuthService.autenticar_usuario(db, credenciais)


@router.get(
    "/me",
    response_model=UsuarioResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar dados do usuário autenticado [Autenticado]",
    description=(
        "Identifica o usuário exclusivamente a partir do token JWT validado no servidor "
        "e retorna suas informações sem expor senha ou hash."
    ),
)
def consultar_usuario_atual(usuario_atual: Usuario = Depends(obter_usuario_atual)):
    return usuario_atual

