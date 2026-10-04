"""Brasil, 1º turno, Presidente: apuração de 2026 (soma dos 27 estados + exterior, ao vivo) x 2022 no mesmo horário.

Por que somar os estados e não usar o arquivo nacional do TSE (br-...-u.json)? Ele é atualizado com atraso
(em 04/10/2026 estava ~22 min atrás dos arquivos estaduais). Cada UF de 2022 é cortada no horário do arquivo daquela UF.
Definições: % de seções = apuradas/total do ano; % de votos = votos do candidato / votos válidos (sem brancos e nulos).
"""
import json, os, urllib.request
from datetime import datetime
import pandas as pd
from corte2022 import secoes_ate

AQUI = os.path.dirname(os.path.abspath(__file__))
REGIOES = {
    "Norte": "AC AM AP PA RO RR TO", "Nordeste": "AL BA CE MA PB PE PI RN SE",
    "Centro-Oeste": "DF GO MS MT", "Sudeste": "ES MG RJ SP", "Sul": "PR RS SC", "Exterior": "ZZ"}
UF_REG = {uf: r for r, ufs in REGIOES.items() for uf in ufs.split()}
assert len(UF_REG) == 28

def baixa(uf):
    q = urllib.request.Request(f"https://resultados.tse.jus.br/oficial/ele2026/6257/dados/{uf.lower()}/{uf.lower()}-c0001-e006257-u.json",
                               headers={"User-Agent": "Mozilla/5.0"})
    return json.load(urllib.request.urlopen(q, timeout=30))

linhas = []
for uf in UF_REG:
    d = baixa(uf)
    c = {k["n"]: int(k["vap"]) for ag in d["carg"][0]["agr"] for p in ag["par"] for k in p["cand"]}
    vv = int(d["v"]["vv"]); assert sum(c.values()) == vv, uf
    linhas.append(dict(uf=uf, regiao=UF_REG[uf], gerado_em=f'{d["dg"]} {d["hg"]}', secoes_total=int(d["s"]["ts"]),
                       secoes_apuradas=int(d["s"]["st"]), votos_validos=vv, lula=c["13"], flavio=c["22"]))
A = pd.DataFrame(linhas)

# --- 2022: seções de todas as UFs (norte + nordeste + top10 + resto, sem duplicar) ---
partes = [pd.read_csv(f"{AQUI}/secoes_{n}_1t_2022.csv.gz", parse_dates=["recebido"]) for n in ("norte", "nordeste", "top10", "resto")]
s22 = pd.concat(partes).drop_duplicates("secao_id")
assert set(s22.uf) == set(UF_REG), set(UF_REG) ^ set(s22.uf)
r = secoes_ate(s22, A[["uf", "gerado_em"]])
r["regiao"] = r.uf.map(UF_REG); s22["regiao"] = s22.uf.map(UF_REG)

def linha(nome, a, x, s):
    v22 = x.lula.sum() + x.bolsonaro.sum() + x.outros.sum()
    return dict(recorte=nome, sec26=a.secoes_apuradas.sum(), tot26=a.secoes_total.sum(), pct_sec26=round(a.secoes_apuradas.sum() / a.secoes_total.sum() * 100, 1),
                sec22=len(x), tot22=len(s), pct_sec22=round(len(x) / len(s) * 100, 1),
                lula26=round(a.lula.sum() / a.votos_validos.sum() * 100, 1), flavio26=round(a.flavio.sum() / a.votos_validos.sum() * 100, 1),
                lula22=round(x.lula.sum() / v22 * 100, 1), bolso22=round(x.bolsonaro.sum() / v22 * 100, 1),
                votos_lula26=a.lula.sum(), votos_flavio26=a.flavio.sum(), votos_validos26=a.votos_validos.sum())
T = pd.DataFrame([linha("BRASIL", A, r, s22)] + [linha(n, A[A.regiao == n], r[r.regiao == n], s22[s22.regiao == n]) for n in REGIOES])
T.to_csv(f"{AQUI}/nacional_comparativo.csv", index=False)
horas = sorted(A.gerado_em.str[-8:])
inst = f"{A.gerado_em.iloc[0][:10]} (arquivos entre {horas[0]} e {horas[-1]})"

H = f"{AQUI}/historico_2026_nacional.csv"
reg = T.iloc[0].to_dict(); reg["gerado_ate"] = f'{A.gerado_em.iloc[0][:10]} {horas[-1]}'
pd.DataFrame([reg]).to_csv(H, mode="a", header=not os.path.exists(H), index=False)

# --- conferência de 2022 contra o resultado oficial nacional (Lula 57.259.504 | Bolsonaro 51.072.345) ---
tl, tb, to = s22.lula.sum(), s22.bolsonaro.sum(), s22.outros.sum()
print(f"[conferência 2022] seções {len(s22):,} | Lula {tl:,.0f} | Bolsonaro {tb:,.0f} | válidos {tl+tb+to:,.0f} | "
      f"Lula {tl/(tl+tb+to)*100:.2f}% Bolsonaro {tb/(tl+tb+to)*100:.2f}%".replace(",", "."))
# arquivo nacional do TSE (para comparar com o que a TV mostra)
try:
    q = urllib.request.Request("https://resultados.tse.jus.br/oficial/ele2026/6257/dados/br/br-c0001-e006257-u.json", headers={"User-Agent": "Mozilla/5.0"})
    b = json.load(urllib.request.urlopen(q, timeout=30))
    print(f"[arquivo nacional TSE] {b['s']['pst']}% das seções, gerado às {b['hg']}")
except Exception as e:
    print("[arquivo nacional TSE] indisponível:", e)
print(f"\n2026: {inst}\n")
print(T.drop(columns=["votos_lula26", "votos_flavio26", "votos_validos26"]).to_string(index=False))
