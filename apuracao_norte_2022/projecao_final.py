"""Projeção do resultado final do 1º turno de 2026 (Presidente, Brasil) a partir da apuração parcial.
Cenário A: os votos que faltam em cada UF repetem a proporção já apurada naquela UF.
Cenário B: além disso, aplica a mudança que ocorreu em 2022 naquela UF entre o mesmo ponto de apuração (mesma fração de seções)
           e o fim (sem ordem de chegada igual à de 2022 isso pode não se repetir).
Votos que faltam por UF = eleitores nas seções não apuradas x comparecimento e % de válidos já observados na UF."""
import json, urllib.request
import numpy as np, pandas as pd
AQUI = __file__.rsplit("/", 1)[0]
UFS = "AC AL AM AP BA CE DF ES GO MA MG MS MT PA PB PE PI PR RJ RN RO RR RS SC SE SP TO ZZ".split()
s = pd.concat([pd.read_csv(f"{AQUI}/secoes_{n}_1t_2022.csv.gz", parse_dates=["recebido"]) for n in ("norte", "nordeste", "top10", "resto")]).drop_duplicates("secao_id")

def curva(uf):  # compartilhamento acumulado 2022 por seção, em ordem de chegada
    g = s[s.uf == uf].sort_values("recebido")
    v = (g.lula + g.bolsonaro + g.outros).cumsum()
    return g, (g.lula.cumsum() / v).values, (g.bolsonaro.cumsum() / v).values

linhas = []; hg = []
for uf in UFS:
    q = urllib.request.Request(f"https://resultados.tse.jus.br/oficial/ele2026/6257/dados/{uf.lower()}/{uf.lower()}-c0001-e006257-u.json", headers={"User-Agent": "Mozilla/5.0"})
    d = json.load(urllib.request.urlopen(q, timeout=30)); hg.append(d["hg"])
    c = {k["n"]: int(k["vap"]) for ag in d["carg"][0]["agr"] for p in ag["par"] for k in p["cand"]}
    vv = int(d["v"]["vv"]); st, ts = int(d["s"]["st"]), int(d["s"]["ts"]); comp = int(d["e"]["c"]); est = int(d["e"]["est"]); esnt = int(d["e"]["esnt"])
    rest = esnt * comp / est * vv / comp            # válidos que faltam (estim.)
    g, cl, cb = curva(uf); k = max(1, min(len(g), round(st / ts * len(g))))
    dl, db = cl[-1] - cl[k - 1], cb[-1] - cb[k - 1]  # mudança de 2022 do ponto k até o fim
    l, f = c["13"] / vv, c["22"] / vv
    linhas.append(dict(uf=uf, vv=vv, rest=rest, lula=c["13"], fla=c["22"], l=l, f=f, dl=dl, db=db, pct=st / ts * 100))
D = pd.DataFrame(linhas)
D["vvf"] = D.vv + D.rest
def final(shift):
    lp = (D.l + shift * D.dl).clip(0, 1); fp = (D.f + shift * D.db).clip(0, 1)
    L = D.lula + D.rest * lp if False else D.vvf * np.where(shift == 0, D.l, lp)  # valor final por UF
    F = D.vvf * np.where(shift == 0, D.f, fp)
    return L.sum(), F.sum(), D.vvf.sum()
out = {}
for nome, sh in (("A (restante igual ao já apurado)", 0), ("B (A + padrão de 2022 na reta final)", 1)):
    L, F, V = final(sh); out[nome] = (L, F, V)
    print(f"{nome}: Lula {L/V*100:.1f}% ({L:,.0f}) | Flávio {F/V*100:.1f}% ({F:,.0f}) | outros {100-(L+F)/V*100:.1f}% | válidos finais {V:,.0f} | diferença {F-L:,.0f} votos ({(F-L)/V*100:+.1f} pp)".replace(",", "."))
print(f"Arquivos {min(hg)} a {max(hg)} | seções apuradas médias (ponderado simples) {D.pct.mean():.1f}%")

# --- Teste do método em 2022 (cenário A) : se parássemos em X% das seções de cada UF, quanto erraria o final? ---
tot = s[["lula", "bolsonaro", "outros"]].sum(); Vf = tot.sum()
for frac in (0.80, 0.90):
    Lp = Fp = 0
    for uf in UFS:
        g = s[s.uf == uf].sort_values("recebido"); k = round(frac * len(g)); h = g.iloc[:k]
        v = h.lula.sum() + h.bolsonaro.sum() + h.outros.sum(); tot_uf = g.lula.sum() + g.bolsonaro.sum() + g.outros.sum()
        vf_est = v * len(g) / k          # válidos finais estimados pela fração de seções
        Lp += vf_est * h.lula.sum() / v; Fp += vf_est * h.bolsonaro.sum() / v
    print(f"[teste 2022, parando em {frac*100:.0f}% das seções de cada UF] projetado Lula {Lp/Vf*100:.1f}% Bolsonaro {Fp/Vf*100:.1f}% | real Lula {tot.lula/Vf*100:.2f}% Bolsonaro {tot.bolsonaro/Vf*100:.2f}% | erro Lula {Lp/Vf*100-tot.lula/Vf*100:+.1f} pp, Bolsonaro {Fp/Vf*100-tot.bolsonaro/Vf*100:+.1f} pp")
