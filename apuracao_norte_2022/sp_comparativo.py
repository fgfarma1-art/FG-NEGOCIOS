"""São Paulo, 1º turno, Presidente: apuração de 2026 (ao vivo) x 2022 no MESMO horário de Brasília.

Definições (iguais nos dois anos):
 - seções apuradas: 2026 = campo `st` do JSON do TSE; 2022 = seções cujo BU foi recebido (DT_BU_RECEBIDO) até o mesmo horário.
 - % de seções = apuradas / total de seções do ano (2026: 103.656; 2022: 101.073).
 - % dos votos = votos do candidato / votos válidos (nominais) já apurados (brancos e nulos fora).
Cada execução busca o JSON atual, acrescenta a foto em historico_2026_sp.csv e refaz tabela e gráfico.
"""
import json, os, urllib.request
from datetime import datetime
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

AQUI = os.path.dirname(os.path.abspath(__file__))
HIST = f"{AQUI}/historico_2026_sp.csv"
URL = "https://resultados.tse.jus.br/oficial/ele2026/6257/dados/sp/sp-c0001-e006257-u.json"

req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
d = json.load(urllib.request.urlopen(req, timeout=30))
cand = {c["n"]: (c["nmu"], int(c["vap"])) for ag in d["carg"][0]["agr"] for p in ag["par"] for c in p["cand"]}
vv = int(d["v"]["vv"])
assert sum(v for _, v in cand.values()) == vv, "soma dos candidatos != votos válidos"
assert d["cdabr"] == "sp" and d["carg"][0]["cd"] == "1"
agora = dict(gerado_em=f'{d["dg"]} {d["hg"]}', secoes_total=int(d["s"]["ts"]), secoes_apuradas=int(d["s"]["st"]),
             votos_validos=vv, lula=cand["13"][1], flavio=cand["22"][1], outros=vv - cand["13"][1] - cand["22"][1],
             comparecimento=int(d["e"]["c"]), aptos=int(d["e"]["te"]))
h = pd.read_csv(HIST) if os.path.exists(HIST) else pd.DataFrame()
if h.empty or h.gerado_em.iloc[-1] != agora["gerado_em"]:
    h = pd.concat([h, pd.DataFrame([agora])], ignore_index=True); h.to_csv(HIST, index=False)

s = pd.read_csv(f"{AQUI}/secoes_top10_1t_2022.csv.gz", parse_dates=["recebido"])
s = s[s.uf == "SP"]
assert len(s) == 101073
linhas = []
for _, r in h.iterrows():
    t = datetime.strptime(r.gerado_em, "%d/%m/%Y %H:%M:%S")
    x = s[s.recebido <= datetime(2022, 10, 2, t.hour, t.minute, t.second)]
    v22 = x.lula.sum() + x.bolsonaro.sum() + x.outros.sum()
    linhas.append(dict(
        hora=t.strftime("%H:%M:%S"),
        sec26=f"{r.secoes_apuradas:,}".replace(",", "."), pct_sec26=round(r.secoes_apuradas / r.secoes_total * 100, 1),
        sec22=f"{len(x):,}".replace(",", "."), pct_sec22=round(len(x) / len(s) * 100, 1),
        lula26=round(r.lula / r.votos_validos * 100, 1), flavio26=round(r.flavio / r.votos_validos * 100, 1),
        lula22=round(x.lula.sum() / v22 * 100, 1), bolso22=round(x.bolsonaro.sum() / v22 * 100, 1),
        dif26=round((r.lula - r.flavio) / r.votos_validos * 100, 1), dif22=round((x.lula.sum() - x.bolsonaro.sum()) / v22 * 100, 1)))
T = pd.DataFrame(linhas); T.to_csv(f"{AQUI}/sp_comparativo.csv", index=False)
print(T.to_string(index=False))
print("\n2026 (última foto): total de seções {:,} | válidos {:,} | comparecimento {:,} de {:,} aptos".format(agora["secoes_total"], vv, agora["comparecimento"], agora["aptos"]).replace(",", "."))

# --- gráfico: curva de 2022 (minuto a minuto) e pontos de 2026 ---
base = datetime(2022, 10, 2)
s = s.sort_values("recebido").copy()
s["min"] = s.recebido.dt.floor("min")
m = s.groupby("min")[["lula", "bolsonaro", "outros"]].sum().cumsum()
m["n"] = s.groupby("min").size().cumsum()
m = m[(m.n >= 500)]            # evita ruído dos primeiros minutos (poucas urnas)
m["pct"] = m.n / len(s) * 100
v = m.lula + m.bolsonaro + m.outros
m["lula_p"], m["bol_p"] = m.lula / v * 100, m.bolsonaro / v * 100
m["t"] = m.index.map(lambda x: x.replace(year=2026, month=10, day=4))
hh = h.copy(); hh["t"] = hh.gerado_em.map(lambda x: datetime.strptime(x, "%d/%m/%Y %H:%M:%S"))
hh["pct"] = hh.secoes_apuradas / hh.secoes_total * 100
hh["lula_p"], hh["fla_p"] = hh.lula / hh.votos_validos * 100, hh.flavio / hh.votos_validos * 100
xmax = datetime(2026, 10, 4, 21, 0)
fig, ax = plt.subplots(1, 2, figsize=(13, 5.6), facecolor="white")
a = ax[0]
a.plot(m.t[m.t <= xmax], m.pct[m.t <= xmax], color="#9E9E9E", lw=3, label="2022")
a.plot(hh.t, hh.pct, "o-", color="#2E7D32", lw=3, ms=8, label="2026 (ao vivo)")
a.set_title("Quanto já foi contado (% das seções)", fontsize=14, weight="bold", loc="left"); a.set_ylim(0, 100)
b = ax[1]
b.plot(m.t[m.t <= xmax], m.lula_p[m.t <= xmax], color="#E57373", lw=3, label="Lula 2022")
b.plot(m.t[m.t <= xmax], m.bol_p[m.t <= xmax], color="#64B5F6", lw=3, label="Bolsonaro 2022")
b.plot(hh.t, hh.lula_p, "o-", color="#C62828", lw=3, ms=8, label="Lula 2026")
b.plot(hh.t, hh.fla_p, "o-", color="#1565C0", lw=3, ms=8, label="Flávio Bolsonaro 2026")
b.set_title("% dos votos válidos já contados", fontsize=14, weight="bold", loc="left")
for a_ in ax:
    a_.set_xlim(datetime(2026, 10, 4, 17, 0), xmax)
    a_.xaxis.set_major_formatter(mdates.DateFormatter("%Hh")); a_.xaxis.set_major_locator(mdates.HourLocator())
    a_.grid(alpha=.3); a_.legend(frameon=False, loc="best"); a_.set_xlabel("Horário de Brasília")
    for sp in ("top", "right"): a_.spines[sp].set_visible(False)
fig.suptitle("São Paulo — 1º turno, Presidente: 2026 x 2022 (mesmo horário)", fontsize=18, weight="bold")
fig.tight_layout(rect=[0, 0, 1, .94]); fig.savefig(f"{AQUI}/sp_comparativo.png", dpi=110)
