from .modelos import brl


def _qtd(e, item) -> str:
    return f"{e.pacotes}x {e.produto.nome}"


def texto(otim, res, sugestoes) -> str:
    itens, plano = otim.itens, res.plano
    out = ["=" * 64, "CARRINHO OTIMIZADO", "=" * 64]
    for n, ped in enumerate(plano.pedidos, 1):
        out.append(f"\nPedido {n}: {ped.loja.nome}")
        for e in ped.escolhas:
            out.append(f"  {e.pacotes}x {e.produto.nome:<38} {brl(e.produto.preco):>10}  = {brl(e.custo):>10}"
                       f"   ({brl(e.produto.preco_unitario)}/{e.produto.rotulo_unitario})")
        out.append(f"  {'Subtotal':<52} {brl(ped.subtotal):>10}")
        if ped.desconto:
            out.append(f"  {'Cupom ' + ped.loja.cupom.codigo:<52} {'-' + brl(ped.desconto):>10}")
        out.append(f"  {'Entrega' + (' (grátis)' if not ped.taxa else ''):<52} {brl(ped.taxa):>10}")
        out.append(f"  {'TOTAL DO PEDIDO':<52} {brl(ped.total):>10}")
    out.append(f"\nTOTAL GERAL: {brl(plano.total)}")
    ref = res.por_numero_de_lojas.get(1)
    if ref and ref.pedidos and len(plano.pedidos) > 1:
        out.append(f"(Tudo em uma loja custaria {brl(ref.total)})")
    if sugestoes:
        out.append("\nSUGESTÕES PARA ECONOMIZAR")
        out += [f"  • {s}" for s in sugestoes]
    return "\n".join(out)


def como_dict(otim, res, sugestoes) -> dict:
    return {
        "total": res.plano.total,
        "valido": res.plano.valido,
        "pedidos": [{
            "loja": p.loja.nome, "subtotal": p.subtotal, "desconto": p.desconto,
            "taxa_entrega": p.taxa, "total": p.total,
            "itens": [{"pedido_para": otim.itens[e.item].nome, "produto": e.produto.nome,
                       "pacotes": e.pacotes, "preco": e.produto.preco, "custo": e.custo}
                      for e in p.escolhas],
        } for p in res.plano.pedidos],
        "nao_encontrados": [otim.itens[i].nome for i in res.nao_encontrados],
        "sugestoes": sugestoes,
    }
