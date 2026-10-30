"""Câmara dos Deputados 2026: cadeiras conquistadas por partido/federação (campo `vag` do TSE), soma dos 27 estados.
Fonte: resultados.tse.jus.br/oficial/ele2026/6259/dados/<uf>/<uf>-c0006-e006259-u.json
Classificação por partido/federação em CLASSE abaixo (convenção do script, ajustável)."""
import json, os, urllib.request
import pandas as pd
AQUI = os.path.dirname(os.path.abspath(__file__))
UFS = "ac al am ap ba ce df es go ma mg ms mt pa pb pe pi pr rj rn ro rr rs sc se sp to".split()
FEDERACOES = {"PCDOB / PT / PV": "Esquerda", "PSOL / REDE": "Esquerda", "PP / UNIÃO": "Direita (outros)",
              "CIDADANIA / PSDB": "Centro", "PRD / SOLIDARIEDADE": "Centro"}   # PRD é direita, Solidariedade é centro: federação mista
CLASSE = {"PL": "PL",
          **{p: "Direita (outros)" for p in ["NOVO", "PP", "UNIÃO", "REPUBLICANOS", "PRD", "DC", "PRTB", "PMB", "AGIR", "MISSÃO", "DEMOCRATA"]},
          **{p: "Centro" for p in ["PSD", "MDB", "PODE", "PSDB", "CIDADANIA", "AVANTE", "SOLIDARIEDADE", "MOBILIZA", "PATRIOTA"]},
          **{p: "Esquerda" for p in ["PT", "PSB", "PDT", "PSOL", "REDE", "PCDOB", "PC DO B", "PV", "PCB", "PSTU", "PCO", "UP"]}}
def classe(com): return FEDERACOES.get(com) or CLASSE.get(com, "?")

rows = []; chk = []
for uf in UFS:
    q = urllib.request.Request(f"https://resultados.tse.jus.br/oficial/ele2026/6259/dados/{uf}/{uf}-c0006-e006259-u.json", headers={"User-Agent": "Mozilla/5.0"})
    d = json.load(urllib.request.urlopen(q, timeout=30)); c = d["carg"][0]
    soma = 0
    for ag in c["agr"]:
        v = int(ag.get("vag", 0)); soma += v
        if v: rows.append(dict(uf=uf.upper(), agr=ag["com"], vag=v))
    chk.append((uf.upper(), int(c["nv"]), soma, float(d["s"]["pstn"].replace(",", ".")), d["hg"]))
C = pd.DataFrame(chk, columns=["uf", "vagas", "soma_vag", "pct_secoes", "hg"])
D = pd.DataFrame(rows); D["grupo"] = D.agr.map(classe)
D.to_csv(f"{AQUI}/camara_2026_cadeiras_por_uf.csv", index=False)
T = D.groupby(["agr", "grupo"]).vag.sum().reset_index().sort_values("vag", ascending=False)
T.to_csv(f"{AQUI}/camara_2026_cadeiras.csv", index=False)
print("UFs com cadeiras != soma:", C[C.vagas != C.soma_vag].values.tolist(), "| total cadeiras", C.vagas.sum(), "| soma vag", C.soma_vag.sum(),
      "| seções mín %", C.pct_secoes.min(), "| arquivos", C.hg.min(), "a", C.hg.max())
print("UFs <100% das seções:", C[C.pct_secoes < 99.99][["uf", "pct_secoes"]].values.tolist())
print("\nPor grupo:\n", D.groupby("grupo").vag.sum().to_string())
print("\nPor partido/federação:\n", T.to_string(index=False))
