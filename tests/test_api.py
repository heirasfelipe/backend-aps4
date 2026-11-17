"""
Suíte de testes automatizados da APS 4 (Autenticação JWT, Hash Argon2, RBAC + APS 3).
Cobre todos os 12 cenários exigidos na Seção 13 da avaliação.
"""
from datetime import timedelta
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from main import app
from model import Evento, Participante, Inscricao, Usuario  # noqa: F401
from schema.usuario_schema import UsuarioCreate
from security.security import criar_token_acesso, verificar_senha
from service.usuario_service import UsuarioService


@pytest.fixture(autouse=True)
def configurar_ambiente_jwt(monkeypatch):
    """Configura uma chave secreta temporária apenas durante a execução dos testes."""
    monkeypatch.setenv("JWT_SECRET_KEY", "chave-secreta-exclusiva-para-testes-automatizados-aps4")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    monkeypatch.delenv("ADMIN_EMAIL", raising=False)
    monkeypatch.delenv("ADMIN_SENHA", raising=False)


@pytest.fixture()
def db_session_factory(tmp_path):
    """Cria um banco SQLite isolado por teste com foreign keys habilitadas."""
    db_path = tmp_path / "test_aps4.db"
    engine = create_engine(f"sqlite:///{db_path.as_posix()}", connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _enable_fk(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    yield TestingSessionLocal
    engine.dispose()


@pytest.fixture()
def client(db_session_factory):
    """TestClient conectado ao banco SQLite isolado do teste."""
    def override_get_db():
        db = db_session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _criar_admin_no_banco(db_session_factory, email="admin@instituicao.edu.br", senha="admin_password_123"):
    """Helper controlado para criar um administrador diretamente via serviço no banco de testes."""
    db = db_session_factory()
    try:
        return UsuarioService.criar_administrador(
            db,
            UsuarioCreate(nome="Admin Inicial", email=email, senha=senha),
        )
    finally:
        db.close()


def _login_obter_header(client: TestClient, email: str, senha: str) -> dict:
    res = client.post("/auth/login", json={"email": email, "senha": senha})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ==============================================================================
# CENÁRIOS 1, 2 e 3: CADASTRO DE USUÁRIO, HASH ARGON2 NO BANCO E E-MAIL DUPLICADO
# ==============================================================================

def test_cadastro_usuario_hash_argon2_e_bloqueios(client, db_session_factory):
    # Cenário 1: Cadastro de usuário comum
    payload = {
        "nome": "Aluno Exemplo",
        "email": "aluno@exemplo.com",
        "senha": "senha_segura",
    }
    res = client.post("/usuarios", json=payload)
    assert res.status_code == 201
    body = res.json()
    assert body["id"] == 1
    assert body["nome"] == "Aluno Exemplo"
    assert body["email"] == "aluno@exemplo.com"
    assert body["perfil"] == "usuario"
    # Resposta nunca expõe senha ou hash
    assert "senha" not in body
    assert "senha_hash" not in body

    # Cenário 2: Verificação direta no SQLite de que a senha foi armazenada como hash Argon2
    db = db_session_factory()
    try:
        usuario_db = db.query(Usuario).filter(Usuario.email == "aluno@exemplo.com").first()
        assert usuario_db is not None
        assert usuario_db.senha_hash != "senha_segura"
        assert usuario_db.senha_hash.startswith("$argon2")
        assert verificar_senha("senha_segura", usuario_db.senha_hash) is True
        assert verificar_senha("senha_errada", usuario_db.senha_hash) is False
    finally:
        db.close()

    # Cenário 3: Tentativa de cadastro com e-mail duplicado -> 409 Conflict
    res_dup = client.post(
        "/usuarios",
        json={"nome": "Outro", "email": "ALUNO@exemplo.com", "senha": "outra_senha"},
    )
    assert res_dup.status_code == 409
    assert res_dup.json()["detail"] == "Já existe um usuário cadastrado com este e-mail."

    # Tentativa de auto-elevação enviando perfil='administrador' -> 422 Unprocessable Entity
    res_priv = client.post(
        "/usuarios",
        json={
            "nome": "Atacante",
            "email": "atacante@exemplo.com",
            "senha": "senha_segura",
            "perfil": "administrador",
        },
    )
    assert res_priv.status_code == 422

    # Validações de nome, e-mail inválido e senha curta/vazia -> 422
    assert client.post("/usuarios", json={"nome": "   ", "email": "a@b.com", "senha": "senha_segura"}).status_code == 422
    assert client.post("/usuarios", json={"nome": "A", "email": "invalido", "senha": "senha_segura"}).status_code == 422
    assert client.post("/usuarios", json={"nome": "A", "email": "a@b.com", "senha": "123"}).status_code == 422
    assert client.post("/usuarios", json={"nome": "A", "email": "a@b.com", "senha": "      "}).status_code == 422


# ==============================================================================
# CENÁRIOS 4, 5, 6, 7, 8 e 11: LOGIN, TOKENS INVÁLIDOS/EXPIRADOS E /auth/me
# ==============================================================================

def test_autenticacao_tokens_e_auth_me(client, db_session_factory):
    client.post(
        "/usuarios",
        json={"nome": "Aluno Teste", "email": "aluno@uni.edu.br", "senha": "minha_senha_123"},
    )

    # Cenário 4: Login com credenciais válidas
    res_login = client.post(
        "/auth/login",
        json={"email": "aluno@uni.edu.br", "senha": "minha_senha_123"},
    )
    assert res_login.status_code == 200
    token_data = res_login.json()
    assert token_data["token_type"] == "bearer"
    assert isinstance(token_data["access_token"], str) and len(token_data["access_token"]) > 20

    # Cenário 5: Credenciais inválidas (e-mail inexistente e senha incorreta retornam mesma mensagem)
    res_email_errado = client.post(
        "/auth/login",
        json={"email": "naoexiste@uni.edu.br", "senha": "minha_senha_123"},
    )
    res_senha_errada = client.post(
        "/auth/login",
        json={"email": "aluno@uni.edu.br", "senha": "senha_incorreta"},
    )
    assert res_email_errado.status_code == 401
    assert res_senha_errada.status_code == 401
    assert res_email_errado.json()["detail"] == "E-mail ou senha inválidos."
    assert res_senha_errada.json()["detail"] == "E-mail ou senha inválidos."

    # Cenário 6: Acesso a rota protegida sem token -> 401
    res_sem_token = client.get("/auth/me")
    assert res_sem_token.status_code == 401
    assert res_sem_token.json()["detail"] == "Não foi possível validar as credenciais."
    assert client.post("/participantes", json={"nome": "X", "email": "x@x.com", "curso": "ADS"}).status_code == 401
    assert client.get("/relatorios/eventos/ocupacao").status_code == 401

    # Cenário 7 e 11: Acesso com token válido em /auth/me
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    res_me = client.get("/auth/me", headers=headers)
    assert res_me.status_code == 200
    me = res_me.json()
    assert me == {
        "id": 1,
        "nome": "Aluno Teste",
        "email": "aluno@uni.edu.br",
        "perfil": "usuario",
    }
    assert "senha" not in me and "senha_hash" not in me

    # Cenário 8a: Token inválido / adulterado -> 401
    res_invalido = client.get("/auth/me", headers={"Authorization": "Bearer token.adulterado.invalido"})
    assert res_invalido.status_code == 401
    assert res_invalido.json()["detail"] == "Não foi possível validar as credenciais."

    # Cenário 8b: Token expirado -> 401
    db = db_session_factory()
    try:
        usuario_db = db.query(Usuario).filter(Usuario.email == "aluno@uni.edu.br").first()
        token_expirado = criar_token_acesso(usuario_db, expires_delta=timedelta(seconds=-10))
    finally:
        db.close()

    res_expirado = client.get("/auth/me", headers={"Authorization": f"Bearer {token_expirado}"})
    assert res_expirado.status_code == 401
    assert res_expirado.json()["detail"] == "Não foi possível validar as credenciais."


# ==============================================================================
# CENÁRIOS 9, 10 e 12: RBAC (ADMIN VS USUÁRIO) + CONTINUIDADE DA APS 3
# ==============================================================================

def test_rbac_admin_vs_usuario_e_continuidade_aps3(client, db_session_factory):
    # Cria administrador controlado e usuário comum
    _criar_admin_no_banco(db_session_factory, email="admin@uni.edu.br", senha="admin_password_123")
    client.post(
        "/usuarios",
        json={"nome": "Usuário Comum", "email": "comum@uni.edu.br", "senha": "user_password_123"},
    )

    headers_admin = _login_obter_header(client, "admin@uni.edu.br", "admin_password_123")
    headers_user = _login_obter_header(client, "comum@uni.edu.br", "user_password_123")

    payload_evento = {
        "titulo": "Workshop de Segurança e JWT",
        "descricao": "Boas práticas com FastAPI, Argon2 e PyJWT.",
        "data": "2026-12-10",
        "horario": "19:00",
        "local": "Auditório 1",
        "capacidade": 2,
        "categoria": "Workshop",
    }

    # Cenário 9: Usuário comum tenta operações administrativas -> 403 Forbidden
    res_user_post_ev = client.post("/eventos", json=payload_evento, headers=headers_user)
    assert res_user_post_ev.status_code == 403
    assert res_user_post_ev.json()["detail"] == "Você não possui permissão para executar esta operação."

    assert client.get("/relatorios/eventos/ocupacao", headers=headers_user).status_code == 403
    assert client.get("/relatorios/eventos/categorias", headers=headers_user).status_code == 403
    assert client.get("/relatorios/participantes/cursos", headers=headers_user).status_code == 403
    assert client.get("/usuarios", headers=headers_user).status_code == 403
    assert (
        client.post(
            "/usuarios/admin",
            json={"nome": "Fake Admin", "email": "fake@uni.edu.br", "senha": "password123"},
            headers=headers_user,
        ).status_code
        == 403
    )

    # Cenário 10: Administrador executa operações administrativas com sucesso
    res_ev = client.post("/eventos", json=payload_evento, headers=headers_admin)
    assert res_ev.status_code == 201
    evento = res_ev.json()

    # Usuário comum tenta atualizar ou excluir evento -> 403 Forbidden
    assert client.put(f"/eventos/{evento['id']}", json={"titulo": "Hack"}, headers=headers_user).status_code == 403
    assert client.delete(f"/eventos/{evento['id']}", headers=headers_user).status_code == 403

    # Administrador consegue atualizar evento e listar usuários sem expor senhas/hashes
    assert client.put(f"/eventos/{evento['id']}", json={"capacidade": 2}, headers=headers_admin).status_code == 200
    res_usuarios = client.get("/usuarios", headers=headers_admin)
    assert res_usuarios.status_code == 200
    assert len(res_usuarios.json()) == 2
    for u in res_usuarios.json():
        assert "senha" not in u and "senha_hash" not in u

    # Cenário 12: Continuidade completa da APS 3 (eventos públicos, participantes, inscrições e relatórios)
    # Consulta de eventos é pública (sem token) e também acessível para usuário comum
    assert len(client.get("/eventos").json()) == 1
    assert client.get(f"/eventos/{evento['id']}").status_code == 200

    # Usuário comum autenticado cadastra participante e realiza inscrição
    p1 = client.post(
        "/participantes",
        json={"nome": "Alice", "email": "alice@uni.edu.br", "curso": "Engenharia de Software"},
        headers=headers_user,
    ).json()
    p2 = client.post(
        "/participantes",
        json={"nome": "Bob", "email": "bob@uni.edu.br", "curso": "ADS"},
        headers=headers_user,
    ).json()

    assert client.post(f"/eventos/{evento['id']}/inscricoes/{p1['id']}", headers=headers_user).status_code == 201
    # Inscrição duplicada continua retornando 409 Conflict
    assert client.post(f"/eventos/{evento['id']}/inscricoes/{p1['id']}", headers=headers_user).status_code == 409
    assert client.post(f"/eventos/{evento['id']}/inscricoes/{p2['id']}", headers=headers_user).status_code == 201

    # Usuário comum consulta inscritos
    inscritos = client.get(f"/eventos/{evento['id']}/inscricoes", headers=headers_user).json()
    assert len(inscritos) == 2

    # Usuário comum não pode excluir participante (403); admin pode
    assert client.delete(f"/participantes/{p2['id']}", headers=headers_user).status_code == 403

    # Administrador consulta os 3 relatórios consolidados da APS 3
    rel_ocup = client.get("/relatorios/eventos/ocupacao", headers=headers_admin)
    assert rel_ocup.status_code == 200
    assert rel_ocup.json()[0]["total_inscritos"] == 2
    assert rel_ocup.json()[0]["percentual_ocupacao"] == 100.0

    rel_cat = client.get("/relatorios/eventos/categorias", headers=headers_admin)
    assert rel_cat.status_code == 200
    assert rel_cat.json()[0] == {
        "categoria": "Workshop",
        "total_eventos": 1,
        "capacidade_total": 2,
        "total_inscricoes": 2,
    }

    rel_cursos = client.get("/relatorios/participantes/cursos", headers=headers_admin)
    assert rel_cursos.status_code == 200
    cursos = {c["curso"]: c for c in rel_cursos.json()}
    assert cursos["Engenharia de Software"]["total_participantes"] == 1
    assert cursos["ADS"]["total_inscricoes"] == 1

    # Administrador exclui participante e evento sem erro
    assert client.delete(f"/participantes/{p2['id']}", headers=headers_admin).status_code == 204
    assert client.delete(f"/eventos/{evento['id']}", headers=headers_admin).status_code == 204

