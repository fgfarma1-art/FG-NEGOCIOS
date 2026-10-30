"""Imagem simples (para leigos) com a apuração atual de 2026 x 2022 no mesmo horário."""
import os, sys
from datetime import datetime
import pandas as pd
from corte2022 import secoes_ate
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

AQUI = os.path.dirname(os.path.abspath(__file__))
VERM, AZUL = "#C62828", "#1565C0"
CINZA, TXT = "#E6E6E6", "#1b1b1b"

def dados(regiao):
    h = pd.read_csv(f"{AQUI}/historico_2026_{regiao}.csv")
    ult = h[h.gerado_em == h.gerado_em.iloc[-1]].set_index("uf").loc[regiao.upper()]
    inst = datetime.strptime(ult.gerado_em, "%d/%m/%Y %H:%M:%S")
    s22 = pd.read_csv(f"{AQUI}/secoes_{regiao}_1t_2022.csv.gz", parse_dates=["recebido"])
    ufs = h.tail(s22.uf.nunique() + 1); ufs = ufs[ufs.uf != regiao.upper()]
    r = secoes_ate(s22, ufs)
    val = r.lula.sum() + r.bolsonaro.sum() + r.outros.sum()
    return dict(inst=inst, p26=ult.pct_secoes, p22=len(r) / len(s22) * 100,
                l26=ult["v_LULA"] / ult.votos_validos * 100, b26=ult["v_FLAVIO BOLSONARO"] / ult.votos_validos * 100,
                l22=r.lula.sum() / val * 100, b22=r.bolsonaro.sum() / val * 100)

D = {"norte": dados("norte"), "nordeste": dados("nordeste")}
inst = D["norte"]["inst"]

fig = plt.figure(figsize=(9, 14), facecolor="white")
fig.text(.5, .965, "Como está a apuração agora?", ha="center", fontsize=26, weight="bold", color=TXT)
fig.text(.5, .94, f"1º turno, Presidente · {inst:%d/%m/%Y} às {inst:%H:%M} (Brasília)", ha="center", fontsize=13, color="#555")
fig.text(.5, .918, "Comparado com 2022 no MESMO horário", ha="center", fontsize=14, weight="bold", color="#555")

def painel(topo, regiao, titulo):
    d = D[regiao]
    fig.text(.06, topo, titulo, fontsize=22, weight="bold", color=TXT)
    fig.text(.06, topo - .035, "1) Quanto da votação já foi contada", fontsize=14, color="#444")
    ax = fig.add_axes([.17, topo - .125, .77, .075]); ax.set_xlim(0, 100); ax.set_ylim(-.5, 1.5); ax.axis("off")
    for y, v, cor, rot in [(1, d["p26"], "#2E7D32", "2026"), (0, d["p22"], "#9E9E9E", "2022")]:
        ax.barh(y, 100, color=CINZA, height=.7); ax.barh(y, v, color=cor, height=.7)
        ax.text(-2, y, rot, ha="right", va="center", fontsize=15, weight="bold")
        dentro = v >= 88
        ax.text(v - 1.5 if dentro else v + 1.5, y, f"{v:.0f}%", ha="right" if dentro else "left",
                va="center", fontsize=17, weight="bold", color="white" if dentro else TXT)
    fig.text(.06, topo - .16, "2) Quem está na frente (% dos votos já contados)", fontsize=14, color="#444")
    ax2 = fig.add_axes([.17, topo - .29, .77, .11]); ax2.set_ylim(-.6, 3.6); ax2.axis("off")
    linhas = [(3, "2026", "Lula", d["l26"], VERM, 1), (2, "2026", "Flávio Bolsonaro", d["b26"], AZUL, 1),
              (1, "2022", "Lula", d["l22"], VERM, .45), (0, "2022", "Bolsonaro", d["b22"], AZUL, .45)]
    for y, ano, nome, v, cor, al in linhas:
        ax2.barh(y, v, color=cor, alpha=al, height=.75)
        ax2.text(-1.5, y, ano, ha="right", va="center", fontsize=13, weight="bold", color="#555")
        ax2.text(v + 1.2, y, f"{v:.0f}%  {nome}", va="center", fontsize=14, color=TXT)
    ax2.set_xlim(0, 115)
    fig.text(.06, topo - .325, f"⚠ Ainda falta contar {100 - d['p26']:.0f}% — o resultado final pode mudar.", fontsize=13, color="#8A5A00", weight="bold")

painel(.86, "norte", "REGIÃO NORTE")
painel(.47, "nordeste", "REGIÃO NORDESTE")
fig.text(.5, .015, "Fonte: TSE (apuração 2026 ao vivo; boletins de urna de 2022). Cores claras = 2022.", ha="center", fontsize=10, color="#777")
fig.savefig(f"{AQUI}/resumo_para_leigos.png", dpi=110)
