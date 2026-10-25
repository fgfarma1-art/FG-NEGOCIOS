"""Chance de virada no 2º turno 2026: o que falta apurar, estado por estado, com erro calibrado no 2º turno de 2022.
Cenário base: os votos que faltam em cada UF repetem a diferença (Lula-Flávio, em % dos válidos) já contada na UF.
Erro: no 2º turno de 2022, para cada UF, com a MESMA fração de seções já apuradas que a UF tem hoje em 2026 (ordem de chegada real),
mediu-se o quanto a diferença dos votos restantes divergiu da diferença já contada. Esses desvios entram na simulação."""
import json, sys, time, urllib.request
import numpy as np, pandas as pd
AQUI = __file__.rsplit("/", 1)[0]; rng = np.random.default_rng(11)
UFS = "AC AL AM AP BA CE DF ES GO MA MG MS MT PA PB PE PI PR RJ RN RO RR RS SC SE SP TO ZZ".split()

def get(uf):
    for t in range(7):
        try:
            q = urllib.request.Request(f"https://resultados.tse.jus.br/oficial/ele2026/6258/dados/{uf.lower()}/{uf.lower()}-c0001-e006258-u.json", headers={"User-Agent": "Mozilla/5.0"})
            d = json.load(urllib.request.urlopen(q, timeout=25)); c = {k["n"]: int(k["vap"]) for ag in d["carg"][0]["agr"] for p in ag["par"] for k in p["cand"]}
            return dict(uf=uf, hg=d["hg"], st=int(d["s"]["st"]), ts=int(d["s"]["ts"]), vv=int(d["v"]["vv"]), L=c["13"], F=c["22"], esnt=int(d["e"]["esnt"]), est=int(d["e"]["est"]), comp=int(d["e"]["c"]), te=int(d["e"]["te"]))
        except Exception: time.sleep(1.5 * (t + 1))
    return None
rows = []
for u in UFS:
    r = get(u); time.sleep(0.25)
    if r: rows.append(r)
    else: print("sem resposta:", u)
D = pd.DataFrame(rows).set_index("uf")
nac_turn = D.comp.sum() / D.est.sum(); nac_val = D.vv.sum() / D.comp.sum()
turn = (D.comp / D.est).where(D.est > 20000, nac_turn); val = (D.vv / D.comp).where(D.comp > 20000, nac_val)
D["rest"] = D.esnt * turn * val                                   # votos válidos que faltam (estimativa)
D["f"] = D.st / D.ts; D["net"] = (D.L - D.F) / D.vv               # diferença Lula-Flávio já contada, em fração dos válidos
lead = int((D.L - D.F).sum()); counted_valid = int(D.vv.sum()); rest_total = D.rest.sum()
print(f"Agora ({D.hg.max()}): seções {int(D.st.sum()):,}/{int(D.ts.sum()):,} = {D.st.sum()/D.ts.sum()*100:.1f}% | Lula {'+' if lead>0 else ''}{lead:,} votos ({lead/counted_valid*100:.2f} pp)")
print(f"Votos válidos que faltam (estimativa): {rest_total:,.0f} ({rest_total/(rest_total+counted_valid)*100:.0f}% do total)")
base = (D.rest * D.net).sum(); print(f"Cenário base (o que falta repete a diferença já contada em cada UF): resto dá Lula {'+' if base>0 else ''}{base:,.0f} -> final Lula {'+' if lead+base>0 else ''}{lead+base:,.0f} ({(lead+base)/(counted_valid+rest_total)*100:.2f} pp)")
need = -lead / rest_total
print(f"Para Flávio virar, os votos restantes teriam de dar a ele uma diferença média de {need*100:.1f} pp ({(1+need)/2*100:.1f}% x {(1-need)/2*100:.1f}% dos válidos), contra {base/rest_total*100:+.1f} pp (Lula) do cenário base")

# ---- calibração com o 2º turno de 2022 ----
S = pd.read_csv(f"{AQUI}/secoes_2t_2022.csv.gz", parse_dates=["recebido"])
sh = {}
for u, g in S.groupby("uf"):
    if u not in D.index: continue
    g = g.sort_values("recebido"); k = int(round(D.loc[u, "f"] * len(g)))
    if k < 20 or k >= len(g) - 1: continue
    c, r = g.iloc[:k], g.iloc[k:]
    vc, vr = (c.lula + c.bolsonaro).sum(), (r.lula + r.bolsonaro).sum()
    sh[u] = ((r.lula - r.bolsonaro).sum() / vr) - ((c.lula - c.bolsonaro).sum() / vc)   # desvio: diferença do restante - diferença contada
dev = pd.Series(sh)
W = (D.rest.reindex(dev.index) / D.rest.reindex(dev.index).sum())
print(f"\n[2022, mesma fração por UF] desvio da diferença do restante vs. já contada: média {dev.mean()*100:+.1f} pp, desvio-padrão {dev.std()*100:.1f} pp, ponderado pelo que falta hoje {np.average(dev, weights=W)*100:+.1f} pp (n={len(dev)} UFs)")
# erro nacional em 2022 com essas frações: previsão (base) x final real
pred = real = 0
for u in dev.index:
    g = S[S.uf == u].sort_values("recebido"); k = int(round(D.loc[u, "f"] * len(g))); c, r = g.iloc[:k], g.iloc[k:]
    vc, vr = (c.lula + c.bolsonaro).sum(), (r.lula + r.bolsonaro).sum()
    pred += (c.lula - c.bolsonaro).sum() + vr * ((c.lula - c.bolsonaro).sum() / vc); real += (g.lula - g.bolsonaro).sum()
tot22 = (S.lula + S.bolsonaro).sum()
print(f"[2022] margem final prevista pelo cenário base {pred/tot22*100:+.2f} pp x real {real/tot22*100:+.2f} pp (erro {(pred-real)/tot22*100:+.2f} pp do total de válidos)")

# ---- simulação ----
N = 40000; mu_d = dev.mean() * 0.0                               # sem viés (o viés de 2022 é de um único turno)
res = {}
for nome, sd_state, sd_common in (("só incerteza por estado (calibrada em 2022)", dev.std(), 0.0), ("+ choque comum nacional de ±1 pp", dev.std(), 0.01), ("+ choque comum nacional de ±2 pp", dev.std(), 0.02)):
    shift = rng.normal(0, sd_state, (N, len(D))) + rng.normal(0, sd_common, (N, 1))
    nets = np.clip(D.net.values[None, :] + shift, -1, 1)
    final = lead + (nets * D.rest.values[None, :]).sum(axis=1)
    res[nome] = final; p = (final < 0).mean()
    print(f"{nome}: P(Flávio vira) = {p*100:.1f}% | margem final de Lula: mediana {np.median(final):,.0f} | 5%-95%: {np.percentile(final,5):,.0f} a {np.percentile(final,95):,.0f}")
