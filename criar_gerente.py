from getpass import getpass

from app.database import SessionLocal
from app.models import Usuario
from app.security import gerar_hash

nome = input("Nome: ")
email = input("E-mail: ")
senha = getpass("Senha (mínimo 6 caracteres): ")

with SessionLocal() as db:
    db.add(
        Usuario(
            nome=nome,
            email=email,
            senha_hash=gerar_hash(senha),
            perfil="gerente",
        )
    )
    db.commit()

print("Gerente criado com sucesso.")