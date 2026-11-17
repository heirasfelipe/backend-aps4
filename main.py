"""
Aplicação Principal - API de Gerenciamento de Eventos Acadêmicos
Avaliação Parcial 04 — Autenticação e Segurança em uma API RESTful
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import SessionLocal, criar_tabelas
from controller import (
    auth_router,
    usuario_router,
    evento_router,
    participante_router,
    inscricao_router,
    relatorio_router,
)
from service.usuario_service import UsuarioService

tags_metadata = [
    {
        "name": "Autenticação",
        "description": "Login por e-mail/senha com emissão de token JWT Bearer e consulta do usuário atual (/auth/me).",
    },
    {
        "name": "Usuários",
        "description": "Cadastro seguro de usuários com hash Argon2 e gerenciamento controlado de administradores.",
    },
    {
        "name": "Eventos",
        "description": "Consulta pública e administração (CRUD) restrita a administradores.",
    },
    {
        "name": "Participantes",
        "description": "Gerenciamento de participantes protegido por autenticação JWT e perfil de acesso.",
    },
    {
        "name": "Inscrições",
        "description": "Inscrição de participantes em eventos disponível para usuários autenticados.",
    },
    {
        "name": "Relatórios",
        "description": "Relatórios consolidados via SQLAlchemy restritos a administradores.",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Cria tabelas no SQLite e executa bootstrap controlado do admin (se configurado no .env)."""
    criar_tabelas()
    db = SessionLocal()
    try:
        UsuarioService.inicializar_admin_por_env(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="API de Gerenciamento de Eventos Acadêmicos (APS 4)",
    description=(
        "Evolução da API RESTful com **autenticação JWT (PyJWT)**, **hash seguro de senhas com Argon2 (pwdlib)**, "
        "**proteção de rotas via Bearer Token** e **controle de acesso baseado em perfis (RBAC)**, "
        "mantendo toda a persistência em **SQLite/SQLAlchemy** e os **relatórios consolidados** da APS 3.\n\n"
        "### Como testar rotas protegidas no Swagger:\n"
        "1. Cadastre um usuário em `POST /usuarios` (ou utilize o administrador configurado).\n"
        "2. Faça login em `POST /auth/login` e copie o valor de `access_token`.\n"
        "3. Clique no botão **Authorize** (cadeado no topo direito), cole o token e confirme.\n"
    ),
    version="3.0.0",
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro dos controladores (Arquitetura MVC)
app.include_router(auth_router)
app.include_router(usuario_router)
app.include_router(evento_router)
app.include_router(participante_router)
app.include_router(inscricao_router)
app.include_router(relatorio_router)


@app.get("/", tags=["Início"], summary="Página inicial da API [Público]")
def raiz():
    """Endpoint raiz público com informações gerais e links para a documentação."""
    return {
        "mensagem": "Bem-vindo à API de Gerenciamento de Eventos Acadêmicos (APS 4 - JWT + RBAC)!",
        "documentacao_swagger": "/docs",
        "documentacao_redoc": "/redoc",
        "status": "online",
        "versao": "3.0.0",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

