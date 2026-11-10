from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Lote, Movimentacao
from app.schemas import PerdaCreate, PerdaOut, PerdaVencidosOut

router = APIRouter(prefix="/perdas", tags=["Perdas"])

CENTAVOS = Decimal("0.01")


def baixar_perda(db: Session, lote: Lote, quantidade: Decimal, motivo: str) -> Decimal:
    """Tira a quantidade do lote e registra a perda. Retorna o custo perdido."""
    lote.quantidade = Decimal(lote.quantidade) - quantidade
    db.add(
        Movimentacao(
            tipo="perda",
            produto_id=lote.produto_id,
            lote_id=lote.id,
            quantidade=quantidade,
            custo_unitario=lote.custo_unitario,
            motivo=motivo,
        )
    )
    return quantidade * Decimal(lote.custo_unitario)


@router.post("", response_model=PerdaOut, status_code=201)
def registrar_perda(dados: PerdaCreate, db: Session = Depends(get_db)):
    """Registra perda de um lote (avaria, quebra, furto...). Sem quantidade = lote inteiro."""
    lote = db.get(Lote, dados.lote_id)
    if not lote or not lote.ativo or Decimal(lote.quantidade) <= 0:
        raise HTTPException(404, "Lote não encontrado ou sem estoque")

    quantidade = Decimal(lote.quantidade) if dados.quantidade is None else dados.quantidade
    if quantidade > Decimal(lote.quantidade):
        raise HTTPException(
            409, f"O lote tem apenas {lote.quantidade} na unidade base"
        )

    custo = baixar_perda(db, lote, quantidade, dados.motivo)
    db.commit()
    return PerdaOut(
        lote_id=lote.id,
        produto_id=lote.produto_id,
        quantidade=quantidade,
        custo_total=custo.quantize(CENTAVOS, rounding=ROUND_HALF_UP),
    )


@router.post("/vencidos", response_model=PerdaVencidosOut)
def baixar_vencidos(db: Session = Depends(get_db)):
    """Dá baixa, como perda, em todos os lotes com validade anterior a hoje."""
    lotes = db.scalars(
        select(Lote).where(
            Lote.ativo == True,
            Lote.quantidade > 0,
            Lote.validade < date.today(),
        )
    ).all()

    quantidade_total = Decimal(0)
    custo_total = Decimal(0)
    for lote in lotes:
        qtd = Decimal(lote.quantidade)
        custo_total += baixar_perda(db, lote, qtd, "vencido")
        quantidade_total += qtd

    db.commit()
    return PerdaVencidosOut(
        lotes_baixados=len(lotes),
        quantidade_total=quantidade_total,
        custo_total=custo_total.quantize(CENTAVOS, rounding=ROUND_HALF_UP),
    )