# 🔐 API RESTful de Gerenciamento de Eventos Acadêmicos — APS 4
> **Avaliação Parcial 04 — Autenticação e Segurança em uma API RESTful**  
> Disciplina: Engenharia de Software / Desenvolvimento Back-End

Evolução da API desenvolvida na APS 3, adicionando **cadastro seguro de usuários**, **armazenamento de senhas com hash Argon2 (`pwdlib`)**, **autenticação via tokens JWT (`PyJWT`)**, **proteção centralizada de rotas com Bearer Token** e **controle de acesso baseado em perfis (RBAC)** — mantendo toda a persistência em **SQLite/SQLAlchemy** e os **relatórios consolidados**.

---

## 📋 Sumário
1. [Descrição do Projeto](#-descrição-do-projeto)
2. [Tecnologias Utilizadas](#-tecnologias-utilizadas)
3. [Estrutura do Projeto (MVC + Security)](#-estrutura-do-projeto-mvc--security)
4. [Instalação](#-instalação)
5. [Configuração da Chave Secreta e Variáveis de Ambiente](#-configuração-da-chave-secreta-e-variáveis-de-ambiente)
6. [Como Executar a Aplicação](#-como-executar-a-aplicação)
7. [Perfis de Acesso e Permissões (RBAC)](#-perfis-de-acesso-e-permissões-rbac)
8. [Principais Rotas da API](#-principais-rotas-da-api)
9. [Como Cadastrar Usuários, Criar Administrador e Obter Tokens](#-como-cadastrar-usuários-criar-administrador-e-obter-tokens)
10. [Exemplos de Utilização (JSON)](#-exemplos-de-utilização-json)
11. [Como Reproduzir os Testes](#-como-reproduzir-os-testes)
12. [Publicação no GitHub](#-publicação-no-github)

---

## 🚀 Descrição do Projeto

A API gerencia eventos acadêmicos, participantes, inscrições e relatórios consolidados de uma instituição de ensino, agora com uma camada completa de **autenticação** e **autorização**:

- **Hash seguro de senhas**: utiliza **`pwdlib` com Argon2** (`PasswordHash.recommended()`). A senha original nunca é salva no banco e nem a senha nem o hash são retornados em nenhuma resposta da API.
- **Autenticação JWT**: rota `POST /auth/login` que valida e-mail e senha e emite um token assinado com **PyJWT** contendo prazo de validade (`exp`), emissão (`iat`) e identificação do usuário (`sub`).
- **Proteção centralizada**: dependências do FastAPI (`obter_usuario_atual` e `exigir_administrador`) em `security/security.py` validam o cabeçalho `Authorization: Bearer <token>` e o perfil do usuário diretamente no servidor.
- **Perfis de acesso (`administrador` e `usuario`)**: impede que usuários comuns executem operações administrativas (`403 Forbidden`) e impede auto-elevação de privilégios no cadastro público.
- **Continuidade da APS 3**: mantém o banco SQLite + SQLAlchemy ORM, relacionamentos com exclusão em cascata, validações Pydantic e os 3 relatórios consolidados.

---

## 🛠 Tecnologias Utilizadas

- **Python 3.10+**
- **FastAPI** — API RESTful com OpenAPI / Swagger UI integrado ao esquema `BearerAuth`.
- **SQLite** + **SQLAlchemy ORM (v2+)** — Persistência relacional e consultas agregadas.
- **Pydantic v2** (`email-validator`) — Validação de entrada e controle de saída.
- **pwdlib (`[argon2]`)** — Geração e verificação segura de hashes de senhas com Argon2.
- **PyJWT** — Geração, assinatura e verificação de tokens JWT.
- **python-dotenv** — Carregamento seguro da chave secreta via arquivo `.env` local (ignorado pelo Git).
- **Uvicorn**, **Pytest** e **HTTPX** — Servidor ASGI e testes automatizados.

---

## 🏛 Estrutura do Projeto (MVC + Security)

```text
aps4/
│
├── main.py                      # Inicialização do FastAPI, lifespan e registro dos routers
├── database.py                  # Conexão SQLite, PRAGMA foreign_keys, SessionLocal e get_db()
├── criar_admin.py               # Procedimento controlado via CLI para criar administrador inicial
├── .env.example                 # Modelo de variáveis de ambiente (sem segredos reais)
├── .gitignore                   # Garante que .env e *.db nunca sejam enviados ao GitHub
├── requirements.txt             # Dependências completas do projeto
├── README.md                    # Documentação completa
│
├── security/                    # Camada de Segurança (hash Argon2, JWT e dependências RBAC)
│   ├── __init__.py
│   └── security.py
│
├── model/                       # Camada Model (entidades SQLAlchemy ORM)
│   ├── __init__.py
│   ├── evento.py
│   ├── participante.py
│   ├── inscricao.py
│   └── usuario.py               # Tabela usuarios (id, nome, email, senha_hash, perfil)
│
├── schema/                      # Camada Schema (contratos Pydantic de entrada e saída)
│   ├── __init__.py
│   ├── evento_schema.py
│   ├── participante_schema.py
│   ├── inscricao_schema.py
│   ├── relatorio_schema.py
│   └── usuario_schema.py        # UsuarioCreate (extra='forbid'), UsuarioResponse, LoginRequest, TokenResponse
│
├── service/                     # Camada Service (regras de negócio, persistência e autenticação)
│   ├── __init__.py
│   ├── evento_service.py
│   ├── participante_service.py
│   ├── inscricao_service.py
│   ├── relatorio_service.py
│   ├── usuario_service.py
│   └── auth_service.py
│
├── controller/                  # Camada Controller (rotas HTTP e aplicação das dependências de segurança)
│   ├── __init__.py
│   ├── auth_controller.py       # POST /auth/login, GET /auth/me
│   ├── usuario_controller.py    # POST /usuarios, POST /usuarios/admin, GET /usuarios
│   ├── evento_controller.py
│   ├── participante_controller.py
│   ├── inscricao_controller.py
│   └── relatorio_controller.py
│
└── tests/                       # Testes automatizados cobrindo todos os 12 cenários da APS 4
    ├── __init__.py
    └── test_api.py
```

---

## 💻 Instalação

```bash
# 1. Acessar a pasta do projeto
cd aps4

# 2. Criar e ativar o ambiente virtual (Windows PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# (No Linux/macOS: python3 -m venv .venv && source .venv/bin/activate)

# 3. Instalar todas as dependências
pip install -r requirements.txt
```

---

## 🔑 Configuração da Chave Secreta e Variáveis de Ambiente

> **Importante:** Nenhuma chave secreta real é publicada no código-fonte ou no repositório GitHub. A aplicação lê `JWT_SECRET_KEY` exclusivamente das variáveis de ambiente (ou do arquivo local `.env`, listado no `.gitignore`).

### Passo 1: Copiar o arquivo de exemplo
- **Windows (PowerShell):**
  ```powershell
  Copy-Item .env.example .env
  ```
- **Linux/macOS:**
  ```bash
  cp .env.example .env
  ```

### Passo 2: Gerar uma chave secreta forte
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Passo 3: Preencher o arquivo `.env`
```env
JWT_SECRET_KEY=cole_aqui_a_chave_gerada_acima
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# (Opcional) Bootstrap controlado do administrador inicial ao iniciar a API:
ADMIN_NOME=Administrador do Sistema
ADMIN_EMAIL=admin@instituicao.edu.br
ADMIN_SENHA=sua_senha_admin_forte
```

---

## ▶️ Como Executar a Aplicação

Com o arquivo `.env` configurado, inicie o servidor:
```bash
python main.py
```
ou:
```bash
python -m uvicorn main:app --reload --port 8000
```

Acesse a documentação interativa no navegador:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 👥 Perfis de Acesso e Permissões (RBAC)

A autorização é sempre validada no servidor a partir do registro do usuário no SQLite associado ao token JWT:

| Perfil | Permissões |
|---|---|
| **Público (sem token)** | Cadastrar usuário comum (`POST /usuarios`), fazer login (`POST /auth/login`), consultar eventos disponíveis (`GET /eventos`, `GET /eventos/{id}`) e status (`GET /`). |
| **`usuario` (Usuário comum autenticado)** | Tudo do acesso público + consultar próprios dados (`GET /auth/me`), listar/consultar/cadastrar/atualizar participantes, realizar/consultar/cancelar inscrições em eventos. **Recebe `403 Forbidden`** ao tentar criar/editar/excluir eventos, excluir participantes, consultar relatórios ou gerenciar usuários/admins. |
| **`administrador`** | Acesso completo: cadastrar, atualizar e excluir eventos; gerenciar e excluir participantes; realizar e consultar inscrições; consultar os 3 relatórios consolidados; listar usuários e criar novos administradores (`POST /usuarios/admin`). |

---

## 📡 Principais Rotas da API

### Autenticação e Usuários
| Método | Rota | Acesso | Descrição |
|---|---|---|---|
| `POST` | `/usuarios` | **Público** | Cadastra usuário comum (`perfil="usuario"` fixo no servidor; bloqueia tentativa de enviar `perfil`). |
| `POST` | `/auth/login` | **Público** | Valida e-mail/senha (Argon2) e retorna token JWT Bearer. |
| `GET` | `/auth/me` | **Autenticado** | Retorna dados do usuário autenticado pelo token (sem senha/hash). |
| `POST` | `/usuarios/admin` | **Administrador** | Cadastra um novo administrador de forma controlada. |
| `GET` | `/usuarios` | **Administrador** | Lista usuários cadastrados (sem senha/hash). |

### Eventos, Participantes, Inscrições e Relatórios (APS 3 protegida)
| Método | Rota | Acesso | Descrição |
|---|---|---|---|
| `GET` | `/eventos` e `/eventos/{id}` | **Público** | Consulta eventos disponíveis e vagas restantes. |
| `POST`, `PUT`, `DELETE` | `/eventos` e `/eventos/{id}` | **Administrador** | Cadastra, atualiza e exclui eventos acadêmicos. |
| `GET`, `POST`, `PUT` | `/participantes` e `/participantes/{id}` | **Autenticado** | Consulta, cadastra e atualiza participantes. |
| `DELETE` | `/participantes/{id}` | **Administrador** | Exclui participante e suas inscrições em cascata. |
| `POST`, `GET`, `DELETE` | `/eventos/{evento_id}/inscricoes...` | **Autenticado** | Inscreve participante, consulta inscritos e cancela inscrição. |
| `GET` | `/relatorios/eventos/ocupacao` | **Administrador** | Relatório de ocupação e percentual por evento. |
| `GET` | `/relatorios/eventos/categorias` | **Administrador** | Relatório consolidado de eventos por categoria. |
| `GET` | `/relatorios/participantes/cursos` | **Administrador** | Relatório de participação única por curso. |

---

## 🛡 Como Cadastrar Usuários, Criar Administrador e Obter Tokens

### 1. Criar o Administrador Inicial (Estratégia Controlada)
Como a rota pública `POST /usuarios` **não permite** criar administradores (rejeita o campo `perfil`), utilize uma das duas estratégias seguras:
- **Via `.env` (automático no startup):** preencha `ADMIN_NOME`, `ADMIN_EMAIL` e `ADMIN_SENHA` no `.env` e inicie a API.
- **Via script CLI controlado:**
  ```bash
  python criar_admin.py --nome "Admin" --email "admin@instituicao.edu.br" --senha "sua_senha_segura"
  ```
- Depois de autenticado como administrador, também é possível cadastrar outros administradores via `POST /usuarios/admin`.

### 2. Cadastrar um Usuário Comum
Envie `POST /usuarios` com `nome`, `email` e `senha` (mínimo 6 caracteres). O perfil será sempre `"usuario"`.

### 3. Obter o Token JWT e Autenticar no Swagger
1. Envie `POST /auth/login` com `email` e `senha`.
2. Copie o valor retornado em `access_token`.
3. No Swagger (`/docs`), clique no botão **Authorize**, cole o token JWT e clique em **Authorize** novamente. Todas as requisições seguintes enviarão automaticamente o cabeçalho:
   ```http
   Authorization: Bearer <token_jwt_gerado>
   ```

---

## 💡 Exemplos de Utilização (JSON)

### Cadastrar Usuário — `POST /usuarios`
Requisição:
```json
{
  "nome": "Aluno Exemplo",
  "email": "aluno@exemplo.com",
  "senha": "senha_segura"
}
```
Resposta (`201 Created` — sem senha nem hash):
```json
{
  "id": 1,
  "nome": "Aluno Exemplo",
  "email": "aluno@exemplo.com",
  "perfil": "usuario"
}
```

### Login — `POST /auth/login`
Requisição:
```json
{
  "email": "aluno@exemplo.com",
  "senha": "senha_segura"
}
```
Resposta (`200 OK`):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Consultar Usuário Autenticado — `GET /auth/me`
Cabeçalho: `Authorization: Bearer <access_token>`  
Resposta (`200 OK`):
```json
{
  "id": 1,
  "nome": "Aluno Exemplo",
  "email": "aluno@exemplo.com",
  "perfil": "usuario"
}
```

### Exemplos de Respostas de Erro
- **Credenciais inválidas (`401 Unauthorized`):**
  ```json
  { "detail": "E-mail ou senha inválidos." }
  ```
- **Token ausente, inválido ou expirado (`401 Unauthorized`):**
  ```json
  { "detail": "Não foi possível validar as credenciais." }
  ```
- **Usuário autenticado sem permissão (`403 Forbidden`):**
  ```json
  { "detail": "Você não possui permissão para executar esta operação." }
  ```
- **E-mail já cadastrado (`409 Conflict`):**
  ```json
  { "detail": "Já existe um usuário cadastrado com este e-mail." }
  ```

---

## 🧪 Como Reproduzir os Testes

### 1. Suíte Automatizada (Pytest)
A partir da pasta `aps4/`:
```bash
python -m pytest tests/ -v
```

Os testes cobrem todos os **12 cenários exigidos pela avaliação**:
1. Cadastro de usuário comum (`201`) e bloqueio de tentativa de envio de `perfil: "administrador"` (`422`);
2. Verificação direta no banco SQLite de que a senha está gravada como hash Argon2 (`$argon2...`);
3. Cadastro com e-mail duplicado (`409 Conflict`);
4. Autenticação com credenciais válidas (`200 OK` + JWT Bearer);
5. Autenticação com e-mail inexistente ou senha incorreta (`401 Unauthorized` genérico);
6. Acesso a rotas protegidas sem token (`401 Unauthorized`);
7. Acesso a rotas protegidas com token válido (`200`/`201`);
8. Acesso com token adulterado e com token expirado (`401 Unauthorized`);
9. Tentativa de operações administrativas por usuário comum (`403 Forbidden`);
10. Execução de operações administrativas por administrador (`200`/`201`/`204`);
11. Consulta dos próprios dados via `GET /auth/me` sem expor senha/hash;
12. Continuidade completa das operações CRUD, inscrições e dos 3 relatórios consolidados da APS 3.

### 2. Testes no Swagger (`/docs`)
1. Inicie a API com `python main.py` e abra `http://127.0.0.1:8000/docs`.
2. Teste `POST /usuarios`, `POST /auth/login` e autentique com o botão **Authorize**.
3. Teste `GET /auth/me`, tente `POST /eventos` como usuário comum (`403`), faça login como administrador e repita `POST /eventos` (`201`) e os relatórios em `/relatorios/...` (`200`).

---

## 📦 Publicação no GitHub

> Antes de dar `git push`, verifique com `git status` que o arquivo `.env` **não** aparece listado (ele já está ignorado pelo `.gitignore`).

```bash
cd aps4
git init
git add .
git commit -m "feat: implementa APS 4 com autenticacao JWT, hash Argon2 e controle de acesso RBAC"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/NOME_DO_REPOSITORIO.git
git push -u origin main
```

