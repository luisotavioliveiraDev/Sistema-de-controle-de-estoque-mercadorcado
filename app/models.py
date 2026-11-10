from datetime import date, datetime
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Categoria(Base):
    __tablename__ = "categorias"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), unique=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)


class Produto(Base):
    __tablename__ = "produtos"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(150))
    codigo_barras: Mapped[str | None] = mapped_column(String(50), unique=True)
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categorias.id"))
    unidade_base: Mapped[str] = mapped_column(String(20))  # un, kg...
    preco_venda: Mapped[float] = mapped_column(Numeric(10, 2))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

    categoria: Mapped[Categoria] = relationship()
    conversoes: Mapped[list["ConversaoUnidade"]] = relationship()
    lotes: Mapped[list["Lote"]] = relationship(back_populates="produto")


class ConversaoUnidade(Base):
    __tablename__ = "conversoes_unidade"
    id: Mapped[int] = mapped_column(primary_key=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"))
    nome: Mapped[str] = mapped_column(String(30))        # pacote, palete
    fator: Mapped[float] = mapped_column(Numeric(10, 3))  # qtd na unidade base


class Lote(Base):
    __tablename__ = "lotes"
    id: Mapped[int] = mapped_column(primary_key=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"))
    quantidade: Mapped[float] = mapped_column(Numeric(12, 3))  # unidade base
    validade: Mapped[date] = mapped_column(Date)
    custo_unitario: Mapped[float] = mapped_column(Numeric(10, 2))
    data_entrada: Mapped[date] = mapped_column(Date, default=date.today)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

    produto: Mapped[Produto] = relationship(back_populates="lotes")


class Movimentacao(Base):
    __tablename__ = "movimentacoes"
    id: Mapped[int] = mapped_column(primary_key=True)
    tipo: Mapped[str] = mapped_column(String(20))  # entrada, venda, perda
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"))
    lote_id: Mapped[int | None] = mapped_column(ForeignKey("lotes.id"))
    quantidade: Mapped[float] = mapped_column(Numeric(12, 3))  # sempre positiva
    custo_unitario: Mapped[float] = mapped_column(Numeric(10, 2))
    preco_unitario: Mapped[float | None] = mapped_column(Numeric(10, 2))  # só em venda
    desconto_percentual: Mapped[int] = mapped_column(Integer, default=0)
    motivo: Mapped[str | None] = mapped_column(String(100))
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    usuario_id: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Usuario(Base):
    __tablename__ = "usuarios"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(150), unique=True)
    senha_hash: Mapped[str] = mapped_column(String(255))
    perfil: Mapped[str] = mapped_column(String(20))  # caixa, estoquista, gerente
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)