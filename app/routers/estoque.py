from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Lote, Movimentacao, Produto
from app.schemas import (
    BaixaLote,
    LoteCreate,
    LoteOut,
    LoteVencimentoOut,
    VendaCreate,
    VendaOut,
)
from app.services import desconto_sugerido, dias_para_vencer, status_validade

router = APIRouter(tags=["Estoque"])

CENTAVOS = Decimal("0.01")


def aplicar_desconto(preco: Decimal, desconto: int) -> Decimal:
    return (preco * (100 - desconto) / 100).quantize(CENTAVOS, rounding=ROUND_HALF_UP)


def converter_para_base(produto: Produto, quantidade: Decimal, unidade: str | None) -> Decimal:
    """Converte 'pacote', 'palete' etc. para a unidade base do produto."""
    if unidade is None or unidade.lower() == produto.unidade_base.lower():
        return quantidade
    for conv in produto.conversoes:
        if conv.nome.lower() == unidade.lower():
            return quantidade * Decimal(conv.fator)
    raise HTTPException(
        400, f"Unidade '{unidade}' não cadastrada para este produto"
    )


@router.post("/lotes", response_model=LoteOut, status_code=201)
def entrada_lote(dados: LoteCreate, db: Session = Depends(get_db)):
    produto = db.get(Produto, dados.produto_id)
    if not produto or not produto.ativo:
        raise HTTPException(404, "Produto não encontrado")

    quantidade_base = converter_para_base(produto, dados.quantidade, dados.unidade)

    lote = Lote(
        produto_id=produto.id,
        quantidade=quantidade_base,
        validade=dados.validade,
        custo_unitario=dados.custo_unitario,
    )
    db.add(lote)
    db.flush()  # gera o id do lote antes de registrar a movimentação

    db.add(
        Movimentacao(
            tipo="entrada",
            produto_id=produto.id,
            lote_id=lote.id,
            quantidade=quantidade_base,
            custo_unitario=dados.custo_unitario,
        )
    )
    db.commit()
    db.refresh(lote)
    return lote


@router.get("/produtos/{produto_id}/lotes", response_model=list[LoteOut])
def listar_lotes_produto(produto_id: int, db: Session = Depends(get_db)):
    consulta = (
        select(Lote)
        .where(Lote.produto_id == produto_id, Lote.ativo == True, Lote.quantidade > 0)
        .order_by(Lote.validade)
    )
    return db.scalars(consulta).all()


@router.get("/estoque/vencimentos", response_model=list[LoteVencimentoOut])
def lotes_a_vencer(dias: int = 30, db: Session = Depends(get_db)):
    """Lista lotes que vencem em até X dias (e os já vencidos), do mais urgente ao menos."""
    limite = date.today() + timedelta(days=dias)
    consulta = (
        select(Lote, Produto)
        .join(Produto, Produto.id == Lote.produto_id)
        .where(Lote.ativo == True, Lote.quantidade > 0, Lote.validade <= limite)
        .order_by(Lote.validade)
    )
    resultado = []
    for lote, produto in db.execute(consulta).all():
        desconto = desconto_sugerido(lote.validade)
        preco = Decimal(produto.preco_venda)
        resultado.append(
            LoteVencimentoOut(
                lote_id=lote.id,
                produto_id=produto.id,
                produto=produto.nome,
                categoria_id=produto.categoria_id,
                quantidade=lote.quantidade,
                validade=lote.validade,
                dias_para_vencer=dias_para_vencer(lote.validade),
                status=status_validade(lote.validade),
                preco_normal=preco,
                desconto_percentual=desconto,
                preco_sugerido=aplicar_desconto(preco, desconto),
            )
        )
    return resultado


@router.post("/vendas", response_model=VendaOut)
def vender(dados: VendaCreate, db: Session = Depends(get_db)):
    """Baixa o estoque pelo método FEFO e aplica o desconto de validade de cada lote."""
    produto = db.get(Produto, dados.produto_id)
    if not produto or not produto.ativo:
        raise HTTPException(404, "Produto não encontrado")

    restante = converter_para_base(produto, dados.quantidade, dados.unidade)
    quantidade_total = restante

    lotes = db.scalars(
        select(Lote)
        .where(
            Lote.produto_id == produto.id,
            Lote.ativo == True,
            Lote.quantidade > 0,
            Lote.validade >= date.today(),  # lote vencido não é vendido
        )
        .order_by(Lote.validade, Lote.id)
    ).all()

    disponivel = sum((Decimal(l.quantidade) for l in lotes), Decimal(0))
    if disponivel < restante:
        raise HTTPException(
            409,
            f"Estoque insuficiente. Disponível (dentro da validade): {disponivel} {produto.unidade_base}",
        )

    preco_base = Decimal(produto.preco_venda)
    usados = []
    valor_total = Decimal(0)

    for lote in lotes:
        if restante <= 0:
            break
        qtd_lote = Decimal(lote.quantidade)
        retirar = min(qtd_lote, restante)
        lote.quantidade = qtd_lote - retirar
        restante -= retirar

        desconto = desconto_sugerido(lote.validade)
        preco_final = aplicar_desconto(preco_base, desconto)
        valor_total += preco_final * retirar

        db.add(
            Movimentacao(
                tipo="venda",
                produto_id=produto.id,
                lote_id=lote.id,
                quantidade=retirar,
                custo_unitario=lote.custo_unitario,
                preco_unitario=preco_final,
                desconto_percentual=desconto,
            )
        )
        usados.append(
            BaixaLote(
                lote_id=lote.id,
                validade=lote.validade,
                quantidade=retirar,
                desconto_percentual=desconto,
                preco_unitario=preco_final,
            )
        )

    db.commit()
    return VendaOut(
        produto_id=produto.id,
        quantidade_total=quantidade_total,
        valor_total=valor_total.quantize(CENTAVOS, rounding=ROUND_HALF_UP),
        lotes_utilizados=usados,
    )