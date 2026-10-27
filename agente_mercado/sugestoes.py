"""Dicas para gastar menos, derivadas do plano escolhido."""
from .modelos import brl


def gerar(otim, res) -> list:
    sug = []
    plano, itens = res.plano, otim.itens
    ks = sorted(res.por_numero_de_lojas)

    if not plano.valido:
        sug.append("⚠️  Algum pedido ficou abaixo do pedido mínimo da loja e nenhuma combinação resolve isso. "
                   "Aumente a lista ou reduza o número de lojas.")

    if ks and len(plano.pedidos) > 1:
        unica = res.por_numero_de_lojas.get(1)
        if unica and unica.valido:
            sug.append(f"Dividir em {len(plano.pedidos)} lojas economiza {brl(unica.total - plano.total)} "
                       f"frente a comprar tudo em {unica.pedidos[0].loja.nome} ({brl(unica.total)}).")
    elif len(ks) > 1:
        outro = res.por_numero_de_lojas[ks[-1]]
        if outro.valido and outro.total < plano.total:
            sug.append(f"Dividir em {len(outro.pedidos)} lojas economizaria só {brl(plano.total - outro.total)} — "
                       f"abaixo do mínimo de {brl(otim.ganho_minimo)} para valer o trabalho. Ajuste com --ganho-minimo.")

    for ped in plano.pedidos:
        loja = ped.loja
        if loja.frete_gratis_acima and ped.taxa > 0:
            falta = loja.frete_gratis_acima - ped.subtotal
            if falta <= loja.frete_gratis_acima * 0.35:
                sug.append(f"{loja.nome}: faltam {brl(falta)} para frete grátis (você pagaria {brl(ped.taxa)} de "
                           f"entrega). Se for comprar mais algo, vale completar nessa loja.")
        c = loja.cupom
        if c and ped.desconto == 0 and c.minimo > ped.subtotal and c.minimo - ped.subtotal <= c.minimo * 0.35:
            sug.append(f"{loja.nome}: faltam {brl(c.minimo - ped.subtotal)} para usar o cupom {c.codigo} "
                       f"(desconto de {brl(c.desconto(c.minimo))}).")

    no_plano = {p.loja.id for p in plano.pedidos}
    for ped in plano.pedidos:
        for e in ped.escolhas:
            item = itens[e.item]
            if item.unidade == "un" and e.produto.unidade != "un":
                continue  # sem medida comparável
            pu = e.produto.preco_unitario
            # mesma loja, embalagem maior com preço por kg/L bem menor (só não perecíveis)
            if not item.perecivel:
                for alt in otim.candidatos[e.item][ped.loja.id]:
                    if alt.produto.preco_unitario <= pu * 0.85 and alt.custo > e.custo:
                        extra = alt.custo - e.custo
                        sug.append(
                            f"{item.nome}: '{alt.produto.nome}' sai {brl(alt.produto.preco_unitario)}/"
                            f"{alt.produto.rotulo_unitario} contra {brl(pu)} do escolhido "
                            f"({(1 - alt.produto.preco_unitario / pu) * 100:.0f}% menos). Paga {brl(extra)} a mais "
                            f"hoje; compensa se for consumir/estocar.")
                        break
            # outra loja fora do plano com preço unitário bem menor
            melhor = None
            for s, escs in otim.candidatos[e.item].items():
                if s in no_plano:
                    continue
                for alt in escs:
                    if alt.produto.preco_unitario <= pu * 0.9 and (melhor is None or
                            alt.produto.preco_unitario < melhor.produto.preco_unitario):
                        melhor = alt
            if melhor:
                sug.append(f"{item.nome}: em {otim.lojas[melhor.produto.loja_id].nome} o preço é "
                           f"{brl(melhor.produto.preco_unitario)}/{melhor.produto.rotulo_unitario} "
                           f"(vs {brl(pu)}), mas a entrega/mínimo da loja não compensou neste carrinho.")
            if e.sobra > 0 and item.unidade != "un":
                sug.append(f"{item.nome}: a embalagem escolhida deixa sobrar "
                           f"{e.sobra / 1000:g} {'kg' if item.unidade == 'g' else 'L'} — "
                           f"{'perecível, considere dividir/congelar' if item.perecivel else 'dá para estocar'}.")

    for i in res.nao_encontrados:
        sug.append(f"Não encontrei '{itens[i].nome}' em nenhuma loja — confira o nome ou os termos excluídos.")
    return sug
