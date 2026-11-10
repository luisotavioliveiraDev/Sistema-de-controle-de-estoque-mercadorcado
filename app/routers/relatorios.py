from datetime import date, datetime, time
from decimal import Decimal, ROUND_HALF_UP
from app.security import exigir_perfil

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Movimentacao, Produto, Usuario
from app.schemas import MovimentacaoOut

router = APIRouter(
    tags=["Relatórios"],
    dependencies=[Depends(exigir_perfil("gerente"))],
)

CENTAVOS = Decimal("0.01")


def money(valor: Decimal) -> Decimal:
    return valor.quantize(CENTAVOS, rounding=ROUND_HALF_UP)


def filtrar_periodo(consulta, inicio: date | None, fim: date | None):
    if inicio:
        consulta = consulta.where(
            Movimentacao.criado_em >= datetime.combine(inicio, time.min)
        )
    if fim:
        consulta = consulta.where(
            Movimentacao.criado_em <= datetime.combine(fim, time.max)
        )
    return consulta


@router.get("/movimentacoes", response_model=list[MovimentacaoOut])
def listar_movimentacoes(
    produto_id: int | None = None,
    tipo: str | None = None,
    usuario_id: int | None = None,
    inicio: date | None = None,
    fim: date | None = None,
    db: Session = Depends(get_db),
):
    """Histórico de movimentações, da mais recente para a mais antiga."""
    consulta = (
        select(Movimentacao, Usuario.nome)
        .outerjoin(Usuario, Usuario.id == Movimentacao.usuario_id)
        .order_by(Movimentacao.id.desc())
    )
    if produto_id:
        consulta = consulta.where(Movimentacao.produto_id == produto_id)
    if tipo:
        consulta = consulta.where(Movimentacao.tipo == tipo)
    if usuario_id:
        consulta = consulta.where(Movimentacao.usuario_id == usuario_id)
    consulta = filtrar_periodo(consulta, inicio, fim)

    resultado = []
    for mov, nome in db.execute(consulta).all():
        item = MovimentacaoOut.model_validate(mov)
        item.usuario = nome
        resultado.append(item)
    return resultado


@router.get("/relatorios/resumo")
def resumo(inicio: date | None = None, fim: date | None = None, db: Session = Depends(get_db)):
    """Perdas, vendas com desconto de validade e vendas normais no período."""
    consulta = filtrar_periodo(
        select(Movimentacao, Produto)
        .join(Produto, Produto.id == Movimentacao.produto_id)
        .where(Movimentacao.tipo.in_(["venda", "perda"])),
        inicio,
        fim,
    )

    perdas_qtd = perdas_custo = Decimal(0)
    perdas_por_motivo: dict[str, Decimal] = {}
    perdas_por_produto: dict[str, Decimal] = {}

    promo_qtd = promo_receita = promo_custo = Decimal(0)
    normal_qtd = normal_receita = normal_custo = Decimal(0)

    for mov, produto in db.execute(consulta).all():
        qtd = Decimal(mov.quantidade)
        custo = qtd * Decimal(mov.custo_unitario)

        if mov.tipo == "perda":
            perdas_qtd += qtd
            perdas_custo += custo
            motivo = mov.motivo or "sem motivo"
            perdas_por_motivo[motivo] = perdas_por_motivo.get(motivo, Decimal(0)) + custo
            perdas_por_produto[produto.nome] = (
                perdas_por_produto.get(produto.nome, Decimal(0)) + custo
            )
        else:  # venda
            receita = qtd * Decimal(mov.preco_unitario)
            if mov.desconto_percentual > 0:
                promo_qtd += qtd
                promo_receita += receita
                promo_custo += custo
            else:
                normal_qtd += qtd
                normal_receita += receita
                normal_custo += custo

    return {
        "periodo": {"inicio": inicio, "fim": fim},
        "perdas": {
            "quantidade": perdas_qtd,
            "custo_total": money(perdas_custo),
            "por_motivo": {k: money(v) for k, v in perdas_por_motivo.items()},
            "por_produto": {k: money(v) for k, v in perdas_por_produto.items()},
        },
        "vendas_com_desconto_validade": {
            "quantidade": promo_qtd,
            "receita": money(promo_receita),
            "lucro": money(promo_receita - promo_custo),
        },
        "vendas_normais": {
            "quantidade": normal_qtd,
            "receita": money(normal_receita),
            "lucro": money(normal_receita - normal_custo),
        },
    }