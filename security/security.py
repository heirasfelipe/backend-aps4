"""
Módulo de segurança da API:
- Hashing seguro de senhas com pwdlib (Argon2);
- Geração e validação de tokens JWT com PyJWT;
- Carregamento seguro da chave secreta via variável de ambiente (.env);
- Dependências FastAPI para autenticação (Bearer) e autorização por perfil (RBAC).
"""
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from database import get_db
from model.usuario import PERFIL_ADMINISTRADOR, Usuario

# Carrega variáveis de ambiente do arquivo .env local (se existir; nunca versionado no Git)
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH)

# Instância recomendada da biblioteca pwdlib (usa Argon2 por padrão)
_password_hash = PasswordHash.recommended()

# Esquema HTTP Bearer integrado ao Swagger UI (auto_error=False para retornar 401 padronizado)
bearer_scheme = HTTPBearer(
    auto_error=False,
    scheme_name="BearerAuth",
    description="Informe o token JWT obtido na rota POST /auth/login.",
)

_ERRO_CREDENCIAIS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Não foi possível validar as credenciais.",
    headers={"WWW-Authenticate": "Bearer"},
)


def obter_chave_secreta() -> str:
    """
    Obtém a chave secreta JWT exclusivamente a partir da variável de ambiente JWT_SECRET_KEY.
    Nenhuma chave secreta fixa é mantida no código-fonte.
    """
    chave = os.getenv("JWT_SECRET_KEY", "").strip()
    if not chave:
        raise RuntimeError(
            "Variável de ambiente 'JWT_SECRET_KEY' não configurada. "
            "Configure-a no ambiente ou crie o arquivo '.env' a partir de '.env.example'."
        )
    return chave


def obter_algoritmo() -> str:
    """Retorna o algoritmo de assinatura JWT configurado (padrão: HS256)."""
    return os.getenv("JWT_ALGORITHM", "HS256").strip() or "HS256"


def obter_expiracao_minutos() -> int:
    """Retorna o tempo padrão de validade do token JWT em minutos (padrão: 60)."""
    try:
        minutos = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
        return minutos if minutos > 0 else 60
    except ValueError:
        return 60


def gerar_hash_senha(senha: str) -> str:
    """Gera um hash seguro (Argon2) para a senha fornecida."""
    return _password_hash.hash(senha)


def verificar_senha(senha_plana: str, senha_hash: str) -> bool:
    """Verifica se a senha informada corresponde ao hash armazenado no banco."""
    try:
        return _password_hash.verify(senha_plana, senha_hash)
    except Exception:
        return False


def criar_token_acesso(
    usuario: Usuario,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Gera um token JWT assinado contendo identificador, e-mail, perfil e expiração."""
    agora = datetime.now(timezone.utc)
    expiracao = agora + (expires_delta or timedelta(minutes=obter_expiracao_minutos()))

    payload: Dict[str, Any] = {
        "sub": str(usuario.id),
        "email": usuario.email,
        "perfil": usuario.perfil,
        "iat": agora,
        "exp": expiracao,
    }
    return jwt.encode(payload, obter_chave_secreta(), algorithm=obter_algoritmo())


def decodificar_token_acesso(token: str) -> Dict[str, Any]:
    """Valida a assinatura e a expiração de um token JWT e retorna seu payload."""
    try:
        payload = jwt.decode(
            token,
            obter_chave_secreta(),
            algorithms=[obter_algoritmo()],
        )
        return payload
    except (ExpiredSignatureError, InvalidTokenError):
        raise _ERRO_CREDENCIAIS


def obter_usuario_atual(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    """
    Dependência FastAPI para autenticar requisições via cabeçalho Authorization: Bearer <token>.
    Identifica o usuário no banco a partir do token validado.
    """
    if credentials is None or credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise _ERRO_CREDENCIAIS

    payload = decodificar_token_acesso(credentials.credentials)
    sub = payload.get("sub")
    if sub is None:
        raise _ERRO_CREDENCIAIS

    try:
        usuario_id = int(sub)
    except (TypeError, ValueError):
        raise _ERRO_CREDENCIAIS

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise _ERRO_CREDENCIAIS

    return usuario


def exigir_administrador(
    usuario_atual: Usuario = Depends(obter_usuario_atual),
) -> Usuario:
    """
    Dependência FastAPI que garante que o usuário autenticado possua perfil 'administrador'.
    Valida a permissão no servidor (registro do banco) e retorna 403 Forbidden caso contrário.
    """
    if usuario_atual.perfil != PERFIL_ADMINISTRADOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não possui permissão para executar esta operação.",
        )
    return usuario_atual

