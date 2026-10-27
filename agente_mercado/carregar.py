"""Leitura das ofertas (JSON ou CSV) e da lista de compras (JSON ou texto)."""
import csv
import json
import re
from pathlib import Path

from .modelos import Cupom, ItemLista, Loja, Produto
from .unidades import converter, extrair_medida


def _produto(d: dict, loja_id: str) -> Produto:
    preco = d.get("preco_promocional") or d["preco"]
    medida = None
    if d.get("embalagem"):
        medida = extrair_medida(str(d["embalagem"]))
    medida = medida or extrair_medida(d["nome"])
    if medida is None:
        medida = (1.0, "un")  # sem tamanho informado: trata como 1 unidade
    return Produto(d["nome"], float(preco), medida[0], medida[1], loja_id, d.get("categoria"))


def _cupom(d):
    if not d:
        return None
    return Cupom(d["codigo"], d["tipo"], float(d["valor"]), float(d.get("minimo", 0)),
                 float(d["teto"]) if d.get("teto") is not None else None)


def _loja(d: dict) -> Loja:
    lid = d.get("id") or d["nome"]
    gratis = d.get("frete_gratis_acima")
    return Loja(
        id=lid, nome=d["nome"],
        taxa_entrega=float(d.get("taxa_entrega", 0)),
        pedido_minimo=float(d.get("pedido_minimo", 0)),
        frete_gratis_acima=float(gratis) if gratis is not None else None,
        cupom=_cupom(d.get("cupom")),
        produtos=[_produto(p, lid) for p in d.get("produtos", [])],
    )


def carregar_ofertas(caminho) -> list:
    caminho = Path(caminho)
    if caminho.suffix.lower() == ".csv":
        return _lojas_de_csv(caminho)
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    return [_loja(l) for l in dados["lojas"]]


def _lojas_de_csv(caminho: Path) -> list:
    """CSV em formato longo: loja,produto,preco[,preco_promocional,embalagem,categoria,
    taxa_entrega,pedido_minimo,frete_gratis_acima,cupom_codigo,cupom_tipo,cupom_valor,
    cupom_minimo,cupom_teto]. Os dados da loja valem pela primeira linha dela."""
    lojas: dict = {}
    with caminho.open(encoding="utf-8-sig", newline="") as f:
        for linha in csv.DictReader(f):
            linha = {k.strip(): (v or "").strip() for k, v in linha.items()}
            nome = linha["loja"]
            if nome == "loja":  # cabeçalho repetido ao juntar CSVs de várias lojas
                continue
            if nome not in lojas:
                cupom = None
                if linha.get("cupom_codigo"):
                    cupom = {"codigo": linha["cupom_codigo"], "tipo": linha.get("cupom_tipo") or "fixo",
                             "valor": linha["cupom_valor"], "minimo": linha.get("cupom_minimo") or 0,
                             "teto": linha.get("cupom_teto") or None}
                lojas[nome] = {"nome": nome, "cupom": cupom, "produtos": [],
                               **{c: linha[c] for c in ("taxa_entrega", "pedido_minimo", "frete_gratis_acima")
                                  if linha.get(c)}}
            lojas[nome]["produtos"].append({
                "nome": linha["produto"], "preco": float(linha["preco"].replace(",", ".")),
                "preco_promocional": float(linha["preco_promocional"].replace(",", "."))
                if linha.get("preco_promocional") else None,
                "embalagem": linha.get("embalagem"), "categoria": linha.get("categoria") or None,
            })
    return [_loja(l) for l in lojas.values()]


_LINHA = re.compile(r"^\s*(?P<nome>[^|;]+?)\s*[|;]\s*(?P<qtd>\d+(?:[.,]\d+)?)\s*(?P<un>[a-zA-Zçã]*)\s*$")


def _item(nome: str, qtd: float, unidade: str, perecivel=False) -> ItemLista:
    termos = nome.split()
    excluir = tuple(t[1:] for t in termos if t.startswith("-") and len(t) > 1)
    nome = " ".join(t for t in termos if not t.startswith("-"))
    q, base = converter(qtd, unidade or "un")
    return ItemLista(nome, q, base, excluir, perecivel)


def carregar_lista(caminho) -> list:
    """Texto: uma linha por item, "arroz tipo 1 | 5 kg"; use -palavra para excluir
    ("arroz -integral | 5 kg"). JSON: [{"item","quantidade","unidade","excluir","perecivel"}]."""
    caminho = Path(caminho)
    if caminho.suffix.lower() == ".json":
        itens = []
        for d in json.loads(caminho.read_text(encoding="utf-8")):
            it = _item(d["item"], float(d.get("quantidade", 1)), d.get("unidade", "un"), d.get("perecivel", False))
            itens.append(ItemLista(it.nome, it.quantidade, it.unidade,
                                   tuple(d.get("excluir", ())) + it.excluir, it.perecivel))
        return itens
    itens = []
    for n, bruta in enumerate(caminho.read_text(encoding="utf-8").splitlines(), 1):
        linha = bruta.split("#")[0].strip()
        if not linha:
            continue
        m = _LINHA.match(linha)
        if not m:
            raise ValueError(f"{caminho}:{n}: use o formato 'item | quantidade unidade' (veio {bruta!r})")
        itens.append(_item(m["nome"], float(m["qtd"].replace(",", ".")), m["un"]))
    return itens
