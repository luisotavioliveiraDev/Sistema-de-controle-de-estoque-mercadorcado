from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class CategoriaCreate(BaseModel):
    nome: str


class CategoriaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    ativo: bool


class ConversaoCreate(BaseModel):
    nome: str
    fator: Decimal = Field(gt=0)


class ConversaoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    fator: Decimal


class ProdutoCreate(BaseModel):
    nome: str
    codigo_barras: str | None = None
    categoria_id: int
    unidade_base: str
    preco_venda: Decimal = Field(ge=0)
    conversoes: list[ConversaoCreate] = []


class ProdutoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    codigo_barras: str | None
    categoria_id: int
    unidade_base: str
    preco_venda: Decimal
    ativo: bool
    conversoes: list[ConversaoOut] = []


class LoteCreate(BaseModel):
    produto_id: int
    quantidade: Decimal = Field(gt=0)
    unidade: str | None = None
    validade: date
    custo_unitario: Decimal = Field(ge=0)


class LoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    produto_id: int
    quantidade: Decimal
    validade: date
    custo_unitario: Decimal
    data_entrada: date
    ativo: bool


class LoteVencimentoOut(BaseModel):
    lote_id: int
    produto_id: int
    produto: str
    categoria_id: int
    quantidade: Decimal
    validade: date
    dias_para_vencer: int
    status: str
    preco_normal: Decimal
    desconto_percentual: int
    preco_sugerido: Decimal


class VendaCreate(BaseModel):
    produto_id: int
    quantidade: Decimal = Field(gt=0)
    unidade: str | None = None


class BaixaLote(BaseModel):
    lote_id: int
    validade: date
    quantidade: Decimal
    desconto_percentual: int
    preco_unitario: Decimal


class VendaOut(BaseModel):
    produto_id: int
    quantidade_total: Decimal
    valor_total: Decimal
    lotes_utilizados: list[BaixaLote]


class PerdaCreate(BaseModel):
    lote_id: int
    quantidade: Decimal | None = Field(default=None, gt=0)
    motivo: str = "avaria"


class PerdaOut(BaseModel):
    lote_id: int
    produto_id: int
    quantidade: Decimal
    custo_total: Decimal


class PerdaVencidosOut(BaseModel):
    lotes_baixados: int
    quantidade_total: Decimal
    custo_total: Decimal


class MovimentacaoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tipo: str
    produto_id: int
    lote_id: int | None
    quantidade: Decimal
    custo_unitario: Decimal
    preco_unitario: Decimal | None
    desconto_percentual: int
    motivo: str | None
    criado_em: datetime


class ProdutoUpdate(BaseModel):
    nome: str | None = None
    codigo_barras: str | None = None
    categoria_id: int | None = None
    preco_venda: Decimal | None = Field(default=None, ge=0)


class UsuarioCreate(BaseModel):
    nome: str
    email: str
    senha: str = Field(min_length=6)
    perfil: str = Field(pattern="^(caixa|estoquista|gerente)$")


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    email: str
    perfil: str
    ativo: bool


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"