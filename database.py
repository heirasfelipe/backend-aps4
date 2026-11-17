"""
Módulo de configuração do banco de dados SQLite com SQLAlchemy ORM.
Responsável por:
- Configurar a conexão com o banco de dados SQLite;
- Habilitar integridade referencial (PRAGMA foreign_keys=ON);
- Criar e gerenciar sessões de acesso;
- Disponibilizar sessões para as rotas/serviços via injeção de dependência;
- Criar as tabelas a partir dos modelos ORM (incluindo tabela de usuários).
"""
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "eventos.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)


@event.listens_for(engine, "connect")
def _habilitar_foreign_keys_sqlite(dbapi_connection, connection_record):
    """Garante que o SQLite aplique restrições de chave estrangeira e ON DELETE CASCADE."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Classe base declarativa para os modelos ORM do SQLAlchemy."""
    pass


def get_db() -> Generator[Session, None, None]:
    """Dependência FastAPI para abrir e encerrar uma sessão de banco por requisição."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def criar_tabelas() -> None:
    """Cria todas as tabelas definidas nos modelos SQLAlchemy, caso ainda não existam."""
    from model import Evento, Participante, Inscricao, Usuario  # noqa: F401
    Base.metadata.create_all(bind=engine)

