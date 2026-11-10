from getpass import getpass

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Usuario
from app.security import gerar_hash

email = input("E-mail: ")
senha = getpass("Nova senha (mínimo 6 caracteres): ")

with SessionLocal() as db:
    usuario = db.scalar(select(Usuario).where(Usuario.email == email))
    if not usuario:
        print("Usuário não encontrado.")
    else:
        usuario.senha_hash = gerar_hash(senha)
        db.commit()
        print("Senha redefinida com sucesso.")
        