"""Governadores 2026, 1º turno: quem está eleito (>50% dos válidos) e quem vai ao 2º turno.
Fonte: resultados.tse.jus.br/oficial/ele2026/6259/dados/<uf>/<uf>-c0003-e006259-u.json. Classificação por partido (grupos_partidos.py)."""
import json, os, urllib.request
import pandas as pd
from grupos_partidos import GRUPOS
AQUI = os.path.dirname(os.path.abspath(__file__))
UFS = "ac al am ap ba ce df es go ma mg ms mt pa pb pe pi pr rj rn ro rr rs sc se sp to".split()
rows = []
for uf in UFS:
    q = urllib.request.Request(f"https://resultados.tse.jus.br/oficial/ele2026/6259/dados/{uf}/{uf}-c0003-e006259-u.json", headers={"User-Agent": "Mozilla/5.0"})
    d = json.load(urllib.request.urlopen(q, timeout=30)); c = d["carg"][0]
    cs = []
    for ag in c["agr"]:
        for p in ag["par"]:
            for k in p["cand"]:
                cs.append(dict(nome=k["nmu"], partido=p["sg"], votos=int(k["vap"]), pct=float(k["pvapn"].replace(",", ".")), e=k["e"]))
    cs.sort(key=lambda x: -x["votos"]); vv = int(d["v"]["vv"])
    for pos, k in enumerate(cs[:3], 1):
        rows.append(dict(uf=uf.upper(), pos=pos, **k, grupo=GRUPOS.get(k["partido"], "?"), pct_secoes=float(d["s"]["pstn"].replace(",", ".")), hg=d["hg"], vv=vv))
D = pd.DataFrame(rows); D.to_csv(f"{AQUI}/governadores_2026.csv", index=False)
top = D[D.pos == 1]; seg = D[D.pos == 2]
print("flag e (1º/2º):", top.e.value_counts().to_dict(), seg.e.value_counts().to_dict(), "| seções mín", D.pct_secoes.min().round(2), "| arquivos", D.hg.min(), D.hg.max())
print("sem classificação:", sorted(set(D[(D.pos <= 2) & (D.grupo == '?')].partido)))
ganhou1t = top[top.pct > 50]; seg2t = top[top.pct <= 50]
print(f"\nEleitos no 1º turno (>50% dos válidos): {len(ganhou1t)} | vão a 2º turno: {len(seg2t)}")
print("Eleitos no 1º turno por grupo:", ganhou1t.grupo.value_counts().to_dict())
print("\nEleitos 1º turno:", "; ".join(f"{r.uf} {r.nome} ({r.partido}) {r.pct:.1f}%" for r in ganhou1t.itertuples()))
print("\nVão ao 2º turno:")
for uf in seg2t.uf:
    g = D[D.uf == uf]
    print(f"  {uf}: {g.iloc[0].nome} ({g.iloc[0].partido}, {g.iloc[0].grupo}) {g.iloc[0].pct:.1f}%  x  {g.iloc[1].nome} ({g.iloc[1].partido}, {g.iloc[1].grupo}) {g.iloc[1].pct:.1f}%")
