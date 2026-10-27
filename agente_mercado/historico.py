"""Histórico de execuções: alertas de preço e itens que você compra com frequência."""
import json
from datetime import date
from pathlib import Path
from statistics import mean, median

from .casamento import tokens
from .modelos import ItemLista, brl


def carregar(caminho) -> dict:
    p = Path(caminho)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"execucoes": []}


def _chave_item(nome: str) -> str:
    return " ".join(sorted(tokens(nome)))


def registrar(caminho, hist, otim, res, hoje: date = None):
    """Grava os itens comprados e os preços vistos nesta execução."""
    hoje = hoje or date.today()
    comprados = {e.item for p in res.plano.pedidos for e in p.escolhas}
    precos = {(otim.lojas[s].nome, c.produto.nome): c.produto.preco
              for i in otim.cobertos for s, cs in otim.candidatos[i].items() for c in cs}
    hist["execucoes"].append({
        "data": hoje.isoformat(),
        "total": res.plano.total,
        "itens": [{"item": otim.itens[i].nome, "quantidade": otim.itens[i].quantidade,
                   "unidade": otim.itens[i].unidade, "perecivel": otim.itens[i].perecivel}
                  for i in sorted(comprados)],
        "precos": [{"loja": l, "produto": n, "preco": v} for (l, n), v in sorted(precos.items())],
    })
    Path(caminho).write_text(json.dumps(hist, ensure_ascii=False, indent=1), encoding="utf-8")


def recorrentes_vencidos(hist, itens_atuais, hoje: date = None, min_compras=2):
    """Itens comprados >= min_compras vezes cujo intervalo médio já passou e que não estão na lista.
    Retorna [(ItemLista, intervalo_medio_dias, dias_desde_a_ultima)]."""
    hoje = hoje or date.today()
    por_item = {}
    for ex in hist["execucoes"]:
        d = date.fromisoformat(ex["data"])
        for it in ex["itens"]:
            por_item.setdefault(_chave_item(it["item"]), []).append((d, it))
    na_lista = [tokens(i.nome) for i in itens_atuais]
    saida = []
    for chave, compras in por_item.items():
        datas = sorted({d for d, _ in compras})
        if len(datas) < min_compras:
            continue
        intervalo = mean((b - a).days for a, b in zip(datas, datas[1:]))
        desde = (hoje - datas[-1]).days
        alvo = set(chave.split())
        if intervalo <= 0 or desde < intervalo * 0.8 or any(t <= alvo or alvo <= t for t in na_lista):
            continue
        ultimo = max(compras, key=lambda c: c[0])[1]
        qtd = median(it["quantidade"] for _, it in compras)
        saida.append((ItemLista(ultimo["item"], qtd, ultimo["unidade"], (), ultimo.get("perecivel", False)),
                      intervalo, desde))
    return sorted(saida, key=lambda r: r[0].nome)


def alertas_de_preco(hist, otim, res) -> list:
    """Compara cada produto do carrinho com o que já foi visto na mesma loja."""
    vistos = {}
    for ex in hist["execucoes"]:
        for p in ex["precos"]:
            vistos.setdefault((p["loja"], p["produto"]), []).append(p["preco"])
    msgs = []
    for ped in res.plano.pedidos:
        for e in ped.escolhas:
            antes = vistos.get((ped.loja.nome, e.produto.nome), [])
            if len(antes) < 2:
                continue
            nome, atual, media = e.produto.nome, e.produto.preco, mean(antes)
            if atual <= min(antes) - 1e-9:
                msgs.append(f"{nome} ({ped.loja.nome}): {brl(atual)} é o menor preço que já vi "
                            f"(média {brl(media)}). Bom momento para estocar.")
            elif atual >= media * 1.10:
                msgs.append(f"{nome} ({ped.loja.nome}): {brl(atual)} está {(atual / media - 1) * 100:.0f}% acima "
                            f"da média ({brl(media)}, mínimo {brl(min(antes))}). Se não for urgente, espere baixar.")
    return msgs
