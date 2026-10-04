import pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
d = pd.read_csv("apuracao_por_hora_norte_1t_2022.csv", parse_dates=["hora_brasilia"])
d = d[d.hora_brasilia <= "2022-10-03 00:00"]
d["h"] = d.hora_brasilia.dt.strftime("%H:%M")
# tabela: % de seções apuradas por estado, ao fim de cada hora
p = d.pivot(index="h", columns="uf", values="pct_secoes")
p.to_csv("pct_secoes_apuradas_por_hora.csv")
dif = d.pivot(index="h", columns="uf", values="dif_lula_menos_bolsonaro_pp")
dif.to_csv("dif_lula_bolsonaro_por_hora.csv")
fig, ax = plt.subplots(1, 2, figsize=(14, 5))
for uf in p.columns:
    lw, c = (3, "k") if uf == "NORTE" else (1.5, None)
    ax[0].plot(p.index, p[uf], label=uf, lw=lw, color=c)
    ax[1].plot(dif.index, dif[uf], label=uf, lw=lw, color=c)
ax[0].set_title("% de seções apuradas (acumulado, hora de Brasília)")
ax[1].set_title("Lula − Bolsonaro, p.p. dos votos válidos apurados")
ax[1].axhline(0, color="gray", lw=.8)
for a in ax: a.tick_params(axis="x", rotation=60); a.grid(alpha=.3)
ax[0].legend(ncol=2, fontsize=8)
fig.suptitle("1º turno 2022, Presidente — região Norte (hora de recebimento do BU na totalização)")
fig.tight_layout(); fig.savefig("apuracao_norte_por_hora.png", dpi=130)
print(p.loc["17:00":"22:00"].round(1).to_string())
print(dif.loc["17:00":"22:00"].to_string())
