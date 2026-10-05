"""Imagem para leigos: Brasil e regiões, 2026 ao vivo x 2022 no mesmo horário (lê nacional_comparativo.csv)."""
import os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

AQUI = os.path.dirname(os.path.abspath(__file__))
VERM, AZUL, VERDE, CINZA = "#C62828", "#1565C0", "#2E7D32", "#9E9E9E"
T = pd.read_csv(f"{AQUI}/nacional_comparativo.csv").set_index("recorte")
hist = pd.read_csv(f"{AQUI}/historico_2026_nacional.csv")
quando = hist.gerado_ate.iloc[-1]
ordem = ["BRASIL", "Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul", "Exterior"]
L = T.loc[ordem]; L["m26"] = L.lula26 - L.flavio26; L["m22"] = L.lula22 - L.bolso22
y = np.arange(len(ordem))[::-1]
B = T.loc["BRASIL"]

fig, ax = plt.subplots(1, 2, figsize=(11.5, 8.4), sharey=True, facecolor="white")
fig.suptitle("Brasil: como está a apuração?", fontsize=24, weight="bold", y=.985)
fig.text(.5, .93, f"1º turno, Presidente · {quando[:10]} · arquivos do TSE até {quando[11:16]} (Brasília) · comparado com 2022 no MESMO horário",
         ha="center", fontsize=11.5, color="#555")
a = ax[0]
a.barh(y + .19, L.pct_sec26, height=.36, color=VERDE, label="2026 (hoje)")
a.barh(y - .19, L.pct_sec22, height=.36, color=CINZA, label="2022 (mesmo horário)")
for yy, v1, v2 in zip(y, L.pct_sec26, L.pct_sec22):
    a.text(v1 + 1, yy + .19, f"{v1:.0f}%", va="center", fontsize=11, weight="bold")
    a.text(v2 + 1, yy - .19, f"{v2:.0f}%", va="center", fontsize=11, color="#555")
a.set_title("Quanto da votação já foi contada", fontsize=14, weight="bold", loc="left")
a.set_xlim(0, 112); a.set_xticks([]); a.set_yticks(y); a.set_yticklabels(ordem, fontsize=14, weight="bold")
a.get_yticklabels()[0].set_fontsize(16)
a.legend(loc="lower right", fontsize=10, frameon=False)
b = ax[1]; cor = lambda v: VERM if v >= 0 else AZUL
b.axvline(0, color="#333", lw=1)
for yy, v1, v2 in zip(y, L.m26, L.m22):
    b.barh(yy + .19, v1, height=.36, color=cor(v1)); b.barh(yy - .19, v2, height=.36, color=cor(v2), alpha=.4)
    for v, dy, bold, c in ((v1, .19, True, "black"), (v2, -.19, False, "#555")):
        b.text(v + (1.2 if v >= 0 else -1.2), yy + dy, f"{v:+.0f}", va="center", ha="left" if v >= 0 else "right", fontsize=11, weight="bold" if bold else "normal", color=c)
b.set_title("Quem está na frente (diferença em pontos)", fontsize=14, weight="bold", loc="left")
b.set_xlim(-38, 38); b.set_xticks([])
b.text(-37, -1.05, "◀ Flávio/Bolsonaro na frente", color=AZUL, fontsize=11, weight="bold", va="center")
b.text(37, -1.05, "Lula na frente ▶", color=VERM, fontsize=11, weight="bold", va="center", ha="right")
b.text(0, 6.85, "Barra forte = 2026 · barra clara = 2022", ha="center", fontsize=10, color="#555")
for a_ in ax:
    for s in ("top", "right", "left", "bottom"): a_.spines[s].set_visible(False)
    a_.tick_params(length=0); a_.set_ylim(-1.4, 7.1)
fig.text(.5, .062, f"Brasil agora: {B.pct_sec26:.0f}% contado · Lula {B.lula26:.1f}% · Flávio Bolsonaro {B.flavio26:.1f}%\n"
         f"2022 no mesmo horário: {B.pct_sec22:.0f}% contado · Lula {B.lula22:.1f}% · Bolsonaro {B.bolso22:.1f}%\n"
         "O resultado ainda pode mudar bastante.",
         ha="center", fontsize=12.5, weight="bold", color="#8A5A00", linespacing=1.5)
fig.text(.5, .012, "Fonte: TSE (soma dos arquivos estaduais de 2026 ao vivo; boletins de urna de 2022). Diferença = % de Lula menos % do outro, entre votos válidos já contados.",
         ha="center", fontsize=8.5, color="#777")
fig.tight_layout(rect=[0, .13, 1, .9]); fig.savefig(f"{AQUI}/resumo_nacional_para_leigos.png", dpi=110)
