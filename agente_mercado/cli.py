import argparse
import json

from . import historico as hist_mod, relatorio, sugestoes
from .carregar import carregar_lista, carregar_ofertas
from .otimizador import Otimizador


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="agente_mercado",
                                 description="Monta o carrinho de mercado mais barato entre várias lojas.")
    ap.add_argument("--ofertas", required=True, help="JSON ou CSV com lojas e preços")
    ap.add_argument("--lista", required=True, help="lista de compras (.txt ou .json)")
    ap.add_argument("--max-lojas", type=int, default=3, help="máximo de lojas/pedidos (padrão 3)")
    ap.add_argument("--ganho-minimo", type=float, default=5.0,
                    help="economia mínima (R$) para justificar cada loja extra (padrão 5)")
    ap.add_argument("--historico", help="arquivo JSON do histórico (criado se não existir): ativa alertas "
                    "de preço e itens recorrentes e registra esta execução")
    ap.add_argument("--incluir-recorrentes", action="store_true",
                    help="adiciona à lista os itens que você costuma repor e já estão na hora")
    ap.add_argument("--nao-registrar", action="store_true", help="usa o histórico sem gravar esta execução")
    ap.add_argument("--json", dest="saida_json", help="salva o carrinho neste arquivo JSON")
    a = ap.parse_args(argv)

    lojas, itens = carregar_ofertas(a.ofertas), carregar_lista(a.lista)
    hist = hist_mod.carregar(a.historico) if a.historico else None
    recorrentes = hist_mod.recorrentes_vencidos(hist, itens) if hist else []
    if a.incluir_recorrentes:
        itens += [r[0] for r in recorrentes]
    otim = Otimizador(itens, lojas, a.max_lojas, a.ganho_minimo)
    res = otim.resolver()
    dicas = sugestoes.gerar(otim, res)
    if hist:
        dicas = hist_mod.alertas_de_preco(hist, otim, res) + dicas
        if not a.incluir_recorrentes:
            dicas += [f"Você costuma comprar {i.nome} a cada ~{iv:.0f} dias e a última vez foi há {d} dias "
                      f"— quer incluir? (--incluir-recorrentes)" for i, iv, d in recorrentes]
        if not a.nao_registrar:
            hist_mod.registrar(a.historico, hist, otim, res)
    print(relatorio.texto(otim, res, dicas))
    if a.saida_json:
        with open(a.saida_json, "w", encoding="utf-8") as f:
            json.dump(relatorio.como_dict(otim, res, dicas), f, ensure_ascii=False, indent=2)
    return 0 if res.plano.valido and not res.nao_encontrados else 1
