"""Imagem para leigos: 10 maiores colégios eleitorais, 2026 ao vivo x 2022 no mesmo horário."""
import os
from datetime import datetime
import numpy as np, pandas as pd
from corte2022 import secoes_ate
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

AQUI = os.path.dirname(os.path.abspath(__file__))
VERM, AZUL, VERDE, CINZA = "#C62828", "#1565C0", "#2E7D32", "#9E9E9E"
h = pd.read_csv(f"{AQUI}/historico_2026_top10.csv")
u = h.tail(11).set_index("uf")  # última rodada: 10 UFs + linha TOP10
inst = datetime.strptime(u.loc["SP"].gerado_em, "%d/%m/%Y %H:%M:%S")
s22 = pd.read_csv(f"{AQUI}/secoes_top10_1t_2022.csv.gz", parse_dates=["recebido"])
r = secoes_ate(s22, u.drop("TOP10").reset_index()[["uf", "gerado_em"]])
g = r.groupby("uf")[["lula", "bolsonaro", "outros"]].sum()
ordem = ["SP", "MG", "RJ", "BA", "RS", "PR", "PE", "CE", "PA", "SC"]
L = pd.DataFrame(index=ordem)
L["p26"] = u.pct_secoes.reindex(ordem)
L["p22"] = (r.groupby("uf").size() / s22.groupby("uf").size() * 100).reindex(ordem)
L["m26"] = ((u.v_LULA - u["v_FLAVIO BOLSONARO"]) / u.votos_validos * 100).reindex(ordem)
L["m22"] = ((g.lula - g.bolsonaro) / (g.lula + g.bolsonaro + g.outros) * 100).reindex(ordem)
tot = u.loc["TOP10"]
y = np.arange(len(ordem))[::-1]

fig, ax = plt.subplots(1, 2, figsize=(11, 8.2), sharey=True, facecolor="white")
fig.suptitle("Os 10 maiores estados: como está a apuração?", fontsize=22, weight="bold", y=.985)
fig.text(.5, .925, f"1º turno, Presidente · {inst:%d/%m/%Y} às {inst:%H:%M} (Brasília) · comparado com 2022 no MESMO horário",
         ha="center", fontsize=12, color="#555")

a = ax[0]
a.barh(y + .19, L.p26, height=.36, color=VERDE, label="2026 (hoje)")
a.barh(y - .19, L.p22, height=.36, color=CINZA, label="2022 (mesmo horário)")
for yy, v1, v2 in zip(y, L.p26, L.p22):
    a.text(v1 + 1, yy + .19, f"{v1:.0f}%", va="center", fontsize=11, weight="bold")
    a.text(v2 + 1, yy - .19, f"{v2:.0f}%", va="center", fontsize=11, color="#555")
a.set_title("Quanto da votação já foi contada", fontsize=14, weight="bold", loc="left")
a.set_xlim(0, 108); a.set_xticks([]); a.set_yticks(y); a.set_yticklabels(ordem, fontsize=14, weight="bold")
a.legend(loc="lower right", fontsize=10, frameon=False)

b = ax[1]
cor = lambda v: VERM if v >= 0 else AZUL
b.axvline(0, color="#333", lw=1)
for yy, v1, v2 in zip(y, L.m26, L.m22):
    b.barh(yy + .19, v1, height=.36, color=cor(v1))
    b.barh(yy - .19, v2, height=.36, color=cor(v2), alpha=.4)
    b.text(v1 + (1.2 if v1 >= 0 else -1.2), yy + .19, f"{v1:+.0f}", va="center", ha="left" if v1 >= 0 else "right", fontsize=11, weight="bold")
    b.text(v2 + (1.2 if v2 >= 0 else -1.2), yy - .19, f"{v2:+.0f}", va="center", ha="left" if v2 >= 0 else "right", fontsize=11, color="#555")
b.set_title("Quem está na frente (diferença em pontos)", fontsize=14, weight="bold", loc="left")
b.set_xlim(-30, 42); b.set_xticks([])
b.text(-29, -1.05, "◀ Flávio/Bolsonaro na frente", color=AZUL, fontsize=11, weight="bold", va="center")
b.text(41, -1.05, "Lula na frente ▶", color=VERM, fontsize=11, weight="bold", va="center", ha="right")
b.text(0, 9.85, "Barra forte = 2026 · barra clara = 2022", ha="center", fontsize=10, color="#555")
for a_ in ax:
    for s in ("top", "right", "left", "bottom"): a_.spines[s].set_visible(False)
    a_.tick_params(length=0); a_.set_ylim(-1.4, 10.1)

fig.text(.5, .05, f"Juntos, os 10 estados: {tot.pct_secoes:.0f}% já contado · Lula {tot.v_LULA / tot.votos_validos * 100:.0f}% · "
         f"Flávio Bolsonaro {tot['v_FLAVIO BOLSONARO'] / tot.votos_validos * 100:.0f}%\nO resultado ainda pode mudar bastante.",
         ha="center", fontsize=13, weight="bold", color="#8A5A00", linespacing=1.4)
fig.text(.5, .012, "Fonte: TSE (apuração 2026 ao vivo; boletins de urna de 2022). Diferença = % de Lula menos % do outro, entre os votos já contados.",
         ha="center", fontsize=9, color="#777")
fig.tight_layout(rect=[0, .11, 1, .9])
fig.savefig(f"{AQUI}/resumo_top10_para_leigos.png", dpi=110)
