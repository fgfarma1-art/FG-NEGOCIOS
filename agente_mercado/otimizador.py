"""Escolhe produtos e lojas para minimizar o total (itens + entrega - cupons)."""
import math
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import combinations

from .casamento import casa
from .modelos import Loja, Produto

PENALIDADE = 10_000.0  # custo artificial de um pedido abaixo do mínimo da loja


@dataclass
class Escolha:
    item: int
    produto: Produto
    pacotes: int
    custo: float
    sobra: float  # quantidade comprada além do necessário (unidade base)


@dataclass
class PedidoLoja:
    loja: Loja
    escolhas: list
    subtotal: float
    desconto: float
    taxa: float
    total: float


@dataclass
class Plano:
    pedidos: list
    total: float
    valido: bool


@dataclass
class Resultado:
    plano: Plano
    por_numero_de_lojas: dict = field(default_factory=dict)  # k -> melhor Plano com até k lojas
    nao_encontrados: list = field(default_factory=list)  # índices de itens


def _escolha(idx, item, produto) -> Escolha:
    if item.unidade == "un" and produto.unidade != "un":
        pacotes, sobra = math.ceil(item.quantidade - 1e-9), 0.0  # "12 un" de leite = 12 caixas
    else:
        pacotes = math.ceil(item.quantidade / produto.quantidade - 1e-9)
        sobra = pacotes * produto.quantidade - item.quantidade
    return Escolha(idx, produto, pacotes, round(pacotes * produto.preco, 2), sobra)


class Otimizador:
    def __init__(self, itens, lojas, max_lojas=3, ganho_minimo=5.0):
        self.itens, self.lojas = itens, {l.id: l for l in lojas}
        self.max_lojas, self.ganho_minimo = max_lojas, ganho_minimo
        # candidatos[i][loja_id] = todas as opções que casam; opcoes = a mais barata de cada loja
        self.candidatos = [defaultdict(list) for _ in itens]
        for i, item in enumerate(itens):
            for loja in lojas:
                for p in loja.produtos:
                    if casa(item, p):
                        self.candidatos[i][loja.id].append(_escolha(i, item, p))
        self.opcoes = [
            {s: min(cs, key=lambda e: (e.custo, e.sobra, e.produto.preco_unitario))
             for s, cs in c.items()} for c in self.candidatos
        ]
        self.cobertos = [i for i, o in enumerate(self.opcoes) if o]
        self.nao_encontrados = [i for i, o in enumerate(self.opcoes) if not o]

    # --- avaliação -------------------------------------------------------------
    def _chave(self, atrib) -> float:
        grupos = defaultdict(float)
        for i, s in atrib.items():
            grupos[s] += self.opcoes[i][s].custo
        total = 0.0
        for s, sub in grupos.items():
            loja = self.lojas[s]
            if sub + 1e-9 < loja.pedido_minimo:
                total += PENALIDADE + (loja.pedido_minimo - sub) * 100
            total += loja.cobrar(sub)[2]
        return total

    def _plano(self, atrib) -> Plano:
        grupos = defaultdict(list)
        for i, s in atrib.items():
            grupos[s].append(self.opcoes[i][s])
        pedidos = []
        for s, escs in grupos.items():
            loja = self.lojas[s]
            sub = round(sum(e.custo for e in escs), 2)
            desc, taxa, total = loja.cobrar(sub)
            pedidos.append(PedidoLoja(loja, sorted(escs, key=lambda e: e.item), sub, desc, taxa, round(total, 2)))
        pedidos.sort(key=lambda p: -p.total)
        valido = all(p.subtotal + 1e-9 >= p.loja.pedido_minimo for p in pedidos)
        return Plano(pedidos, round(sum(p.total for p in pedidos), 2), valido)

    # --- busca -----------------------------------------------------------------
    def _melhorar(self, atrib, combo):
        chave = self._chave(atrib)
        melhorou = True
        while melhorou:
            melhorou = False
            for i in self.cobertos:
                atual, melhor_s = atrib[i], None
                for s in combo:
                    if s == atual or s not in self.opcoes[i]:
                        continue
                    atrib[i] = s
                    k = self._chave(atrib)
                    if k < chave - 1e-9:
                        chave, melhor_s = k, s
                atrib[i] = melhor_s or atual
                melhorou |= melhor_s is not None
        return chave, atrib

    def _resolver(self, combo):
        if not all(any(s in self.opcoes[i] for s in combo) for i in self.cobertos):
            return None
        inicios = [{i: min((s for s in combo if s in self.opcoes[i]),
                           key=lambda s: self.opcoes[i][s].custo) for i in self.cobertos}]
        for s in combo:
            if all(s in self.opcoes[i] for i in self.cobertos):
                inicios.append({i: s for i in self.cobertos})
        return min((self._melhorar(dict(a), combo) for a in inicios), key=lambda r: r[0])

    def resolver(self) -> Resultado:
        ids = sorted({s for o in self.opcoes for s in o})
        melhores = {}
        for k in range(1, min(self.max_lojas, len(ids)) + 1):
            achado = None
            for combo in combinations(ids, k):
                r = self._resolver(combo)
                if r and (achado is None or r[0] < achado[0]):
                    achado = r
            if achado:
                melhores[k] = self._plano(achado[1])
        if not melhores:
            return Resultado(Plano([], 0.0, True), {}, self.nao_encontrados)
        # Só aceita mais lojas se a economia compensar o trabalho de pagar mais de um pedido.
        ks = sorted(melhores)
        escolhido = ks[0]
        for k in ks[1:]:
            ref = melhores[escolhido]
            if (melhores[k].valido and not ref.valido) or \
               (melhores[k].valido == ref.valido and melhores[k].total <= ref.total - self.ganho_minimo):
                escolhido = k
        return Resultado(melhores[escolhido], melhores, self.nao_encontrados)
