from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Categoria
from app.schemas import CategoriaCreate, CategoriaOut
from app.routers import estoque, perdas, produtos, relatorios

app = FastAPI(title="Controle de Estoque")
app.include_router(produtos.router)
app.include_router(estoque.router)
app.include_router(perdas.router)
app.include_router(relatorios.router)

@app.post("/categorias", response_model=CategoriaOut, status_code=201)
def criar_categoria(dados: CategoriaCreate, db: Session = Depends(get_db)):
    existe = db.scalar(select(Categoria).where(Categoria.nome == dados.nome))
    if existe:
        raise HTTPException(409, "Categoria já existe")
    categoria = Categoria(nome=dados.nome)
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return categoria


@app.get("/categorias", response_model=list[CategoriaOut])
def listar_categorias(db: Session = Depends(get_db)):
    return db.scalars(select(Categoria).where(Categoria.ativo == True)).all()


@app.delete("/categorias/{categoria_id}", status_code=204)
def excluir_categoria(categoria_id: int, db: Session = Depends(get_db)):
    categoria = db.get(Categoria, categoria_id)
    if not categoria:
        raise HTTPException(404, "Categoria não encontrada")
    categoria.ativo = False  # soft delete
    db.commit()