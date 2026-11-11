from sqlalchemy import update

from app.database import SessionLocal
from app.models import Usuario

with SessionLocal() as db:
    resultado = db.execute(
        update(Usuario)
        .where(Usuario.perfil.in_(["caixa", "estoquista"]))
        .values(perfil="funcionario")
    )
    db.commit()
    print(f"{resultado.rowcount} usuário(s) convertido(s) para funcionario.")