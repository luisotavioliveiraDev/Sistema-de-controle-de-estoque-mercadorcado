from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Usuario
from app.schemas import TokenOut, UsuarioCreate, UsuarioOut
from app.security import (
    criar_token,
    exigir_perfil,
    gerar_hash,
    usuario_atual,
    verificar_senha,
)

router = APIRouter(tags=["Autenticação"])


@router.post("/auth/login", response_model=TokenOut)
def login(
    form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """No campo 'username' vai o e-mail do usuário."""
    usuario = db.scalar(select(Usuario).where(Usuario.email == form.username))
    if (
        not usuario
        or not usuario.ativo
        or not verificar_senha(form.password, usuario.senha_hash)
    ):
        raise HTTPException(401, "E-mail ou senha incorretos")
    return TokenOut(access_token=criar_token(usuario))


@router.get("/auth/eu", response_model=UsuarioOut)
def meus_dados(usuario: Usuario = Depends(usuario_atual)):
    return usuario


@router.post(
    "/usuarios",
    response_model=UsuarioOut,
    status_code=201,
    dependencies=[Depends(exigir_perfil("gerente"))],
)
def criar_usuario(dados: UsuarioCreate, db: Session = Depends(get_db)):
    if db.scalar(select(Usuario).where(Usuario.email == dados.email)):
        raise HTTPException(409, "E-mail já cadastrado")
    usuario = Usuario(
        nome=dados.nome,
        email=dados.email,
        senha_hash=gerar_hash(dados.senha),
        perfil=dados.perfil,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.get(
    "/usuarios",
    response_model=list[UsuarioOut],
    dependencies=[Depends(exigir_perfil("gerente"))],
)
def listar_usuarios(db: Session = Depends(get_db)):
    return db.scalars(select(Usuario).where(Usuario.ativo == True)).all()