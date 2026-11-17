"""Schemas Pydantic para cadastro de usuários, autenticação e tokens JWT."""
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UsuarioCreate(BaseModel):
    """
    Schema para cadastro público de usuário.
    Usa extra='forbid' para impedir que o cliente tente enviar 'perfil' arbitrariamente
    (ex.: tentar se autodeclarar 'administrador').
    """

    model_config = ConfigDict(extra="forbid")

    nome: str = Field(..., description="Nome completo do usuário", min_length=1, max_length=150, examples=["Aluno Exemplo"])
    email: EmailStr = Field(..., description="E-mail utilizado para autenticação", examples=["aluno@exemplo.com"])
    senha: str = Field(
        ...,
        description="Senha de acesso (mínimo de 6 caracteres, não pode conter apenas espaços)",
        min_length=6,
        max_length=128,
        examples=["senha_segura"],
    )

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, valor: str) -> str:
        if not valor or not valor.strip():
            raise ValueError("O nome do usuário não pode ser vazio.")
        return valor.strip()

    @field_validator("senha")
    @classmethod
    def validar_senha(cls, valor: str) -> str:
        if not valor or not valor.strip():
            raise ValueError("A senha não pode ser vazia ou conter apenas espaços.")
        if len(valor.strip()) < 6:
            raise ValueError("A senha deve possuir no mínimo 6 caracteres válidos.")
        return valor


class UsuarioResponse(BaseModel):
    """
    Schema de retorno público de um usuário.
    Garante que nem a senha original nem o hash da senha sejam expostos nas respostas da API.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Identificador único do usuário")
    nome: str = Field(..., description="Nome do usuário")
    email: EmailStr = Field(..., description="E-mail do usuário")
    perfil: str = Field(..., description="Perfil de acesso ('usuario' ou 'administrador')")


class LoginRequest(BaseModel):
    """Schema de credenciais para autenticação na rota POST /auth/login."""

    email: EmailStr = Field(..., description="E-mail cadastrado do usuário", examples=["aluno@exemplo.com"])
    senha: str = Field(..., description="Senha do usuário", min_length=1, examples=["senha_segura"])


class TokenResponse(BaseModel):
    """Schema de resposta contendo o token JWT gerado na autenticação."""

    access_token: str = Field(..., description="Token JWT assinado para uso no cabeçalho Authorization: Bearer")
    token_type: str = Field(default="bearer", description="Tipo do token de autenticação")

