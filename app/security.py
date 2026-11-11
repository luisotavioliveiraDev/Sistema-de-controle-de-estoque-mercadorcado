import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Usuario

load_dotenv()
SECRET_KEY = os.environ["SECRET_KEY"]  # sem valor padrão: se faltar, o servidor não sobe
ALGORITMO = "HS256"
EXPIRA_MINUTOS = 60 * 8  # o token vale 8 horas

senha_hasher = PasswordHash.recommended()
oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")


def gerar_hash(senha: str) -> str:
    return senha_hasher.hash(senha)


def verificar_senha(senha: str, senha_hash: str) -> bool:
    return senha_hasher.verify(senha, senha_hash)


def criar_token(usuario: Usuario) -> str:
    expira = datetime.now(timezone.utc) + timedelta(minutes=EXPIRA_MINUTOS)
    dados = {"sub": str(usuario.id), "perfil": usuario.perfil, "exp": expira}
    return jwt.encode(dados, SECRET_KEY, algorithm=ALGORITMO)


def usuario_atual(
    token: str = Depends(oauth2), db: Session = Depends(get_db)
) -> Usuario:
    erro = HTTPException(
        401, "Token inválido ou expirado", headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        dados = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITMO])
        usuario_id = int(dados["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise erro

    usuario = db.get(Usuario, usuario_id)
    if not usuario or not usuario.ativo:
        raise erro
    return usuario


def exigir_perfil(*perfis: str):
    """Uso nas rotas: Depends(exigir_perfil("gerente"))"""

    def verificador(usuario: Usuario = Depends(usuario_atual)) -> Usuario:
        if usuario.perfil not in perfis:
            raise HTTPException(403, "Seu perfil não tem permissão para isso")
        return usuario

    return verificador