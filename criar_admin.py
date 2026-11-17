"""
Procedimento controlado via linha de comando para criação de um usuário administrador inicial.
Evita que qualquer usuário se torne administrador pela rota pública POST /usuarios e
não mantém senhas fixas no código-fonte.

Uso:
    python criar_admin.py
    python criar_admin.py --nome "Admin" --email "admin@instituicao.edu.br" --senha "sua_senha_segura"
"""
import argparse
import getpass
import sys

from database import SessionLocal, criar_tabelas
from schema.usuario_schema import UsuarioCreate
from service.usuario_service import UsuarioService


def main():
    parser = argparse.ArgumentParser(description="Cria um usuário administrador no banco SQLite.")
    parser.add_argument("--nome", help="Nome completo do administrador")
    parser.add_argument("--email", help="E-mail do administrador")
    parser.add_argument("--senha", help="Senha do administrador (mínimo 6 caracteres)")
    args = parser.parse_args()

    nome = args.nome or input("Nome do administrador: ").strip()
    email = args.email or input("E-mail do administrador: ").strip()
    senha = args.senha or getpass.getpass("Senha (mínimo 6 caracteres): ").strip()

    try:
        dados = UsuarioCreate(nome=nome, email=email, senha=senha)
    except Exception as exc:
        print(f"Erro de validação: {exc}")
        sys.exit(1)

    criar_tabelas()
    db = SessionLocal()
    try:
        admin = UsuarioService.criar_administrador(db, dados)
        print(
            f"Administrador criado com sucesso! "
            f"ID={admin.id} | Nome='{admin.nome}' | E-mail='{admin.email}' | Perfil='{admin.perfil}'"
        )
    except Exception as exc:
        detalhe = getattr(exc, "detail", str(exc))
        print(f"Não foi possível criar o administrador: {detalhe}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

