"""Compara a apuração AO VIVO de 2026 (Presidente, 1º turno) no Norte com 2022, no mesmo horário.

2026: JSON oficial do TSE (resultados.tse.jus.br/oficial/ele2026/6257/dados/<uf>/<uf>-c0001-e006257-u.json).
2022: secoes_norte_1t_2022.csv.gz (gerado por apuracao_por_hora.py), com o horário de recebimento de cada BU.
Cada execução acrescenta uma linha por UF em historico_2026_<regiao>.csv e imprime o comparativo da execução.
"""
import json, sys, urllib.request, os
from datetime import datetime, timedelta
import pandas as pd
from corte2022 import secoes_ate

REGIAO = sys.argv[1] if len(sys.argv) > 1 else "norte"
REGIOES = {"norte": "ac,am,ap,pa,ro,rr,to", "nordeste": "al,ba,ce,ma,pb,pe,pi,rn,se", "top10": "sp,mg,rj,ba,rs,pr,pe,ce,pa,sc"}
UFS = (sys.argv[2] if len(sys.argv) > 2 else REGIOES[REGIAO]).split(",")
BASE = "https://resultados.tse.jus.br/oficial/ele2026/6257/dados"
AQUI = os.path.dirname(os.path.abspath(__file__))
HIST = f"{AQUI}/historico_2026_{REGIAO}.csv"

def baixa(uf):
    req = urllib.request.Request(f"{BASE}/{uf}/{uf}-c0001-e006257-u.json", headers={"User-Agent": "Mozilla/5.0"})
    return json.load(urllib.request.urlopen(req, timeout=30))

def num(x): return float(str(x).replace(",", "."))

linhas = []
for uf in UFS:
    d = baixa(uf)
    cands = {}
    for ag in d["carg"][0]["agr"]:
        for p in ag["par"]:
            for c in p["cand"]:
                cands[c["nmu"]] = int(c["vap"])
    linhas.append(dict(
        gerado_em=f'{d["dg"]} {d["hg"]}', uf=uf.upper(),
        secoes_total=int(d["s"]["ts"]), secoes_apuradas=int(d["s"]["st"]), pct_secoes=num(d["s"]["pst"]),
        votos_validos=int(d["v"]["vv"]), **{f"v_{k}": v for k, v in cands.items()}))
atual = pd.DataFrame(linhas)
inst = datetime.strptime(atual.gerado_em.iloc[0], "%d/%m/%Y %H:%M:%S")  # horário de Brasília

# --- 2022 no mesmo horário do dia (hora de Brasília) ---
s22 = pd.read_csv(f"{AQUI}/secoes_{REGIAO}_1t_2022.csv.gz", parse_dates=["recebido"])
r = secoes_ate(s22, atual[["uf", "gerado_em"]])  # cada UF cortada no horário do seu arquivo
c22 = r.groupby("uf")[["lula", "bolsonaro", "outros"]].sum()
c22["secoes_apuradas_2022"] = r.groupby("uf").size()
c22["total_2022"] = s22.groupby("uf").size()
c22.loc[REGIAO.upper()] = list(c22[["lula", "bolsonaro", "outros"]].sum()) + [c22.secoes_apuradas_2022.sum(), c22.total_2022.sum()]
c22["pct_secoes_2022"] = (c22.secoes_apuradas_2022 / c22.total_2022 * 100).round(2)
c22["lula_pct_2022"] = (c22.lula / (c22.lula + c22.bolsonaro + c22.outros) * 100).round(2)
c22["bolso_pct_2022"] = (c22.bolsonaro / (c22.lula + c22.bolsonaro + c22.outros) * 100).round(2)

# --- 2026 ---
vc = [c for c in atual.columns if c.startswith("v_")]
tot = atual[["secoes_total", "secoes_apuradas", "votos_validos"] + vc].sum()
tot_row = pd.DataFrame([dict(gerado_em=atual.gerado_em.iloc[0], uf=REGIAO.upper(), pct_secoes=round(tot.secoes_apuradas / tot.secoes_total * 100, 2), **tot.to_dict())])
atual = pd.concat([atual, tot_row], ignore_index=True)
atual.to_csv(HIST, mode="a", header=not os.path.exists(HIST), index=False)

horas = sorted(set(atual.gerado_em.str[-8:].iloc[:-1]))
print(f"Arquivos 2026 gerados entre {horas[0]} e {horas[-1]} (Brasília); cada UF de 2022 cortada no horário do seu arquivo")
out = pd.DataFrame({"uf": atual.uf, "seções 2026 %": atual.pct_secoes}).set_index("uf")
out["seções 2022 %"] = c22.pct_secoes_2022
for k in ["v_LULA", "v_FLAVIO BOLSONARO"]:
    out[k.replace("v_", "") + " 2026 %"] = (atual.set_index("uf")[k] / atual.set_index("uf").votos_validos * 100).round(2)
out["Lula 2022 %"] = c22.lula_pct_2022
out["Bolsonaro 2022 %"] = c22.bolso_pct_2022
print(out.to_string())
