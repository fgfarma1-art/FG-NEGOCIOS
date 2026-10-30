"""Projeção do 2º turno de 2026 (Lula x Flávio Bolsonaro) — modelo de transferência calibrado no 1º->2º turno de 2022.

Idéia: em cada UF, os eleitores dos OUTROS candidatos do 1º turno (O) viram votos para Lula (gL*O) e Flávio/Bolsonaro (gB*O) no 2º turno.
gL e gB são medidos em 2022 por UF (fração líquida do 'pool' de outros que foi para cada lado, já incluindo a variação de comparecimento).
Aplica-se aos números FINAIS do 1º turno de 2026 por UF. Incerteza: (1) bootstrap dos municípios de 2022 em cada UF; (2) choque comum em gL/gB para
'o pool de 2026 é diferente do de 2022' (sigma e correlação escolhidos por julgamento; testa-se sensibilidade); (3) efeito de 2º turno de governador no comparecimento.
"""
import json, os, sys, urllib.request
import numpy as np, pandas as pd
AQUI = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(2026)
UFS = "AC AL AM AP BA CE DF ES GO MA MG MS MT PA PB PE PI PR RJ RN RO RR RS SC SE SP TO ZZ".split()
GOV22 = {"AL", "AM", "BA", "ES", "MS", "PB", "PE", "RO", "RS", "SC", "SE", "SP"}      # UFs com 2º turno p/ governador em 2022 (dos BUs do 2t)
GOV26 = {"AC", "AM", "DF", "ES", "RJ", "RN", "TO"}                                     # 2026: pelos arquivos do TSE (governadores_2026.py)

# ---------- 2022 por município e UF ----------
M = pd.read_csv(f"{AQUI}/municipios_2022_1t_2t.csv.gz")
M["vv1"] = M.lula_1 + M.bolso_1 + M.outros
M["O"] = M.outros
def uf_tab(df):
    g = df.groupby("SG_UF").agg(L1=("lula_1", "sum"), B1=("bolso_1", "sum"), O=("O", "sum"), L2=("lula_2", "sum"), B2=("bolso_2", "sum"),
                                comp1=("comp_1", "sum"), comp2=("comp_2", "sum"), aptos=("aptos_1", "sum"))
    g["gL"] = (g.L2 - g.L1) / g.O; g["gB"] = (g.B2 - g.B1) / g.O; return g
T22 = uf_tab(M)
nat = T22[["L1", "B1", "O", "L2", "B2"]].sum()
print(f"[2022] pool de outros {nat.O:,.0f} | ganho Lula {nat.L2-nat.L1:,.0f} ({(nat.L2-nat.L1)/nat.O:.3f} do pool) | ganho Bolsonaro {nat.B2-nat.B1:,.0f} ({(nat.B2-nat.B1)/nat.O:.3f})")
# efeito do 2º turno de governador no comparecimento (UF-nível): d(comp/aptos) ~ a + tau*gov22
T22["dturn"] = T22.comp2 / T22.aptos - T22.comp1 / T22.aptos; T22["gov"] = [1.0 if u in GOV22 else 0.0 for u in T22.index]
X = np.c_[np.ones(len(T22)), T22.gov]; y = T22.dturn.values; beta = np.linalg.lstsq(X, y, rcond=None)[0]
res = y - X @ beta; cov = np.linalg.inv(X.T @ X) * (res @ res / (len(y) - 2)); tau, se_tau = beta[1], np.sqrt(cov[1, 1])
print(f"[2022] comparecimento: variação base {beta[0]*100:+.2f} pp; com 2º turno de governador {tau*100:+.2f} pp (erro-padrão {se_tau*100:.2f} pp)")

# ---------- 2026 por UF (finais) ----------
rows = []
for uf in UFS:
    q = urllib.request.Request(f"https://resultados.tse.jus.br/oficial/ele2026/6257/dados/{uf.lower()}/{uf.lower()}-c0001-e006257-u.json", headers={"User-Agent": "Mozilla/5.0"})
    d = json.load(urllib.request.urlopen(q, timeout=30))
    c = {k["n"]: int(k["vap"]) for ag in d["carg"][0]["agr"] for p in ag["par"] for k in p["cand"]}
    vv = int(d["v"]["vv"]); rows.append(dict(uf=uf, L1=c["13"], B1=c["22"], O=vv - c["13"] - c["22"], vv=vv, comp=int(d["e"]["c"]), aptos=int(d["e"]["te"]), sec=float(d["s"]["pstn"].replace(",", "."))))
R = pd.DataFrame(rows).set_index("uf")
print(f"[2026] 1º turno: Lula {R.L1.sum():,} ({R.L1.sum()/R.vv.sum()*100:.2f}%) | Flávio {R.B1.sum():,} ({R.B1.sum()/R.vv.sum()*100:.2f}%) | outros {R.O.sum():,} | seções mín {R.sec.min():.2f}%")

# ---------- simulação ----------
SIGMA, RHO, NB = float(sys.argv[1]) if len(sys.argv) > 1 else 0.10, -0.6, 4000
mun_by_uf = {u: g[["lula_1", "bolso_1", "O", "lula_2", "bolso_2"]].values for u, g in M.groupby("SG_UF")}
gov_adj = np.array([(1.0 if u in GOV26 else 0.0) - (1.0 if u in GOV22 else 0.0) for u in UFS])
Lv = R.loc[UFS, "L1"].values.astype(float); Bv = R.loc[UFS, "B1"].values.astype(float); Ov = R.loc[UFS, "O"].values.astype(float); Av = R.loc[UFS, "aptos"].values.astype(float)
out = np.zeros((NB, 2)); parts = []
for b in range(NB):
    gL = np.zeros(len(UFS)); gB = np.zeros(len(UFS))
    for i, u in enumerate(UFS):
        a = mun_by_uf[u]; s = a[rng.integers(0, len(a), len(a))]
        gL[i] = (s[:, 3].sum() - s[:, 0].sum()) / s[:, 2].sum(); gB[i] = (s[:, 4].sum() - s[:, 1].sum()) / s[:, 2].sum()
    z1, z2 = rng.standard_normal(2); eL = SIGMA * z1; eB = SIGMA * (RHO * z1 + np.sqrt(1 - RHO ** 2) * z2)
    L2 = Lv + (gL + eL) * Ov; B2 = Bv + (gB + eB) * Ov
    lam = L2 / (L2 + B2); extra = (tau + se_tau * rng.standard_normal()) * gov_adj * Av * 0.95   # 95% válidos
    L2 = L2 + extra * lam; B2 = B2 + extra * (1 - lam)
    out[b] = (L2.sum(), B2.sum()); 
    if b < 400: parts.append(lam)
share = out[:, 0] / out.sum(axis=1); marg = out[:, 1] - out[:, 0]
q = lambda x, p: np.percentile(x, p)
print(f"\n[Simulação sigma={SIGMA} | {NB} sorteios] Lula % dos válidos: média {share.mean()*100:.2f} | p5 {q(share,5)*100:.2f} | p50 {q(share,50)*100:.2f} | p95 {q(share,95)*100:.2f}")
print(f"  P(Flávio vence) = {(share<0.5).mean()*100:.1f}% | margem Flávio-Lula (votos): média {marg.mean():,.0f} | p5 {q(marg,5):,.0f} | p95 {q(marg,95):,.0f}")
print(f"  votos válidos 2º turno (média): {out.sum(axis=1).mean():,.0f}")
# efeito do ajuste de governador sozinho
nL, nB = (Lv + (T22.reindex(UFS).gL.values) * Ov).sum(), (Bv + T22.reindex(UFS).gB.values * Ov).sum()
print(f"  replay puro de 2022 (sem choque/governador): Lula {nL:,.0f} ({nL/(nL+nB)*100:.2f}%) | Flávio {nB:,.0f} | margem {nB-nL:,.0f}")
pd.DataFrame({"uf": UFS, "lula_pct_2t_mediana": np.median(np.array(parts), axis=0) * 100}).to_csv(f"{AQUI}/projecao_2turno_por_uf.csv", index=False)
np.save(f"{AQUI}/_sim_share_sigma{SIGMA}.npy", share)

# ---------- validação: deixa uma UF de fora (g agrupado das demais) e prevê o 2º turno de 2022 ----------
errs = []; pL = pB = 0.0
for u in T22.index:
    o = T22.drop(u); gl = (o.L2 - o.L1).sum() / o.O.sum(); gb = (o.B2 - o.B1).sum() / o.O.sum(); t = T22.loc[u]
    L2p, B2p = t.L1 + gl * t.O, t.B1 + gb * t.O; pL += L2p; pB += B2p
    errs.append((L2p / (L2p + B2p) - t.L2 / (t.L2 + t.B2)) * 100)
errs = np.array(errs)
print(f"\n[Validação 2022, deixando 1 UF de fora] erro na % de Lula por UF: média {errs.mean():+.2f} pp | RMSE {np.sqrt((errs**2).mean()):.2f} pp | máx {np.abs(errs).max():.2f} pp")
tl, tb = T22.L2.sum(), T22.B2.sum(); print(f"  nacional previsto Lula {pL/(pL+pB)*100:.2f}% vs real {tl/(tl+tb)*100:.2f}% (erro {(pL/(pL+pB)-tl/(tl+tb))*100:+.2f} pp)")
