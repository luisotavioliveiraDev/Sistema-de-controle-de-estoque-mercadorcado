from datetime import date
from decimal import Decimal

# Ajuste esses valores conforme a política do seu mercado
DIAS_ATENCAO = 30
DIAS_PROMOCAO = 15
DIAS_CRITICO = 7


def dias_para_vencer(validade: date) -> int:
    return (validade - date.today()).days


def status_validade(validade: date) -> str:
    dias = dias_para_vencer(validade)
    if dias < 0:
        return "vencido"
    if dias <= DIAS_CRITICO:
        return "critico"
    if dias <= DIAS_PROMOCAO:
        return "promocao"
    if dias <= DIAS_ATENCAO:
        return "atencao"
    return "normal"


def desconto_sugerido(validade: date) -> int:
    """Percentual de desconto sugerido pela proximidade do vencimento."""
    dias = dias_para_vencer(validade)
    if dias < 0:
        return 0  # vencido não se vende
    if dias <= DIAS_CRITICO:
        return 50
    if dias <= DIAS_PROMOCAO:
        return 30
    return 0