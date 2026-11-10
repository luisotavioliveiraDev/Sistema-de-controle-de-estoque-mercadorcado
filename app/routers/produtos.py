from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Categoria, ConversaoUnidade, Produto
from app.schemas import ProdutoCreate, ProdutoOut

router = APIRouter(prefix="/produtos", tags=["Produtos"])


@router.post("", response_model=ProdutoOut, status_code=201)
def criar_produto(dados: ProdutoCreate, db: Session = Depends(get_db)):
    categoria = db.get(Categoria, dados.categoria_id)
    if not categoria or not categoria.ativo:
        raise HTTPException(404, "Categoria não encontrada")

    if dados.codigo_barras:
        existe = db.scalar(
            select(Produto).where(Produto.codigo_barras == dados.codigo_barras)
        )
        if existe:
            raise HTTPException(409, "Código de barras já cadastrado")

    produto = Produto(
        nome=dados.nome,
        codigo_barras=dados.codigo_barras,
        categoria_id=dados.categoria_id,
        unidade_base=dados.unidade_base,
        preco_venda=dados.preco_venda,
        conversoes=[
            ConversaoUnidade(nome=c.nome, fator=c.fator) for c in dados.conversoes
        ],
    )
    db.add(produto)
    db.commit()
    db.refresh(produto)
    return produto


@router.get("", response_model=list[ProdutoOut])
def listar_produtos(categoria_id: int | None = None, db: Session = Depends(get_db)):
    consulta = select(Produto).where(Produto.ativo == True)
    if categoria_id:
        consulta = consulta.where(Produto.categoria_id == categoria_id)
    return db.scalars(consulta).all()


@router.get("/{produto_id}", response_model=ProdutoOut)
def buscar_produto(produto_id: int, db: Session = Depends(get_db)):
    produto = db.get(Produto, produto_id)
    if not produto or not produto.ativo:
        raise HTTPException(404, "Produto não encontrado")
    return produto


@router.delete("/{produto_id}", status_code=204)
def excluir_produto(produto_id: int, db: Session = Depends(get_db)):
    produto = db.get(Produto, produto_id)
    if not produto:
        raise HTTPException(404, "Produto não encontrado")
    produto.ativo = False  # soft delete
    db.commit()