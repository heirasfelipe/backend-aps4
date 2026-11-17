"""Controller responsável pelas rotas HTTP de Cadastro e Gerenciamento de Usuários."""
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from model.usuario import Usuario
from schema.usuario_schema import UsuarioCreate, UsuarioResponse
from security.security import exigir_administrador
from service.usuario_service import UsuarioService

router = APIRouter(prefix="/usuarios", tags=["Usuários"])


@router.post(
    "",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar um novo usuário comum [Público]",
    description=(
        "Rota pública para cadastro de usuários. A senha é armazenada apenas como hash Argon2 "
        "e nunca é retornada na resposta. O perfil é sempre atribuído como 'usuario' no servidor."
    ),
)
def cadastrar_usuario(dados: UsuarioCreate, db: Session = Depends(get_db)):
    return UsuarioService.criar_usuario_comum(db, dados)


@router.post(
    "/admin",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar um novo administrador [Admin]",
    description=(
        "Procedimento controlado para criação de novos usuários administradores. "
        "Restrito a administradores já autenticados."
    ),
)
def cadastrar_administrador(
    dados: UsuarioCreate,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(exigir_administrador),
):
    return UsuarioService.criar_administrador(db, dados)


@router.get(
    "",
    response_model=List[UsuarioResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar usuários cadastrados [Admin]",
    description="Restrito a administradores. Retorna todos os usuários sem expor senhas ou hashes.",
)
def listar_usuarios(
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(exigir_administrador),
):
    return UsuarioService.listar_usuarios(db)

