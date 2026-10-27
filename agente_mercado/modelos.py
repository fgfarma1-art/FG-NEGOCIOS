from dataclasses import dataclass, field
from typing import Optional


def brl(valor: float) -> str:
    texto = f"{valor:,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


@dataclass
class Cupom:
    codigo: str
    tipo: str  # "percent" ou "fixo"
    valor: float
    minimo: float = 0.0
    teto: Optional[float] = None

    def desconto(self, subtotal: float) -> float:
        if subtotal + 1e-9 < self.minimo:
            return 0.0
        d = subtotal * self.valor / 100 if self.tipo == "percent" else self.valor
        if self.teto is not None:
            d = min(d, self.teto)
        return min(d, subtotal)


@dataclass
class Produto:
    nome: str
    preco: float
    quantidade: float  # tamanho da embalagem em unidade base (g, ml ou un)
    unidade: str  # "g", "ml" ou "un"
    loja_id: str = ""
    categoria: Optional[str] = None

    @property
    def preco_unitario(self) -> float:
        """Preço por kg, por litro ou por unidade."""
        fator = 1000 if self.unidade in ("g", "ml") else 1
        return self.preco / self.quantidade * fator

    @property
    def rotulo_unitario(self) -> str:
        return {"g": "kg", "ml": "L", "un": "un"}[self.unidade]


@dataclass
class Loja:
    id: str
    nome: str
    taxa_entrega: float = 0.0
    pedido_minimo: float = 0.0
    frete_gratis_acima: Optional[float] = None
    cupom: Optional[Cupom] = None
    produtos: list = field(default_factory=list)

    def cobrar(self, subtotal: float):
        """Retorna (desconto, taxa de entrega, total) de um pedido com este subtotal."""
        desconto = self.cupom.desconto(subtotal) if self.cupom else 0.0
        gratis = self.frete_gratis_acima is not None and subtotal + 1e-9 >= self.frete_gratis_acima
        taxa = 0.0 if gratis else self.taxa_entrega
        return desconto, taxa, subtotal - desconto + taxa


@dataclass
class ItemLista:
    nome: str
    quantidade: float  # em unidade base
    unidade: str  # "g", "ml" ou "un"
    excluir: tuple = ()
    perecivel: bool = False

    @property
    def descricao(self) -> str:
        if self.unidade == "un":
            return f"{self.quantidade:g} un de {self.nome}"
        q, r = (self.quantidade / 1000, "kg" if self.unidade == "g" else "L")
        return f"{q:g} {r} de {self.nome}"
