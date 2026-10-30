"""Senado 2026 (1º turno): quem está nas 2 primeiras posições em cada UF, agora (apuração parcial).

Fonte: JSON oficial do TSE, resultados.tse.jus.br/oficial/ele2026/6259/dados/<uf>/<uf>-c0005-e006259-u.json
Em 2026 cada UF elege 2 senadores (54 vagas). "Na frente" = os 2 candidatos mais votados HOJE, não eleitos.
Classificação ideológica por PARTIDO do candidato (convenção do script, ajustável em GRUPOS).
"""
import json, os, urllib.request
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
UFS = "ac al am ap ba ce df es go ma mg ms mt pa pb pe pi pr rj rn ro rr rs sc se sp to".split()
# Convenção usada (discutível — ajuste aqui se quiser): direita = PL + partidos de direita/centro-direita do bloco conservador
GRUPOS = {
    "PL": "PL",
    **{p: "Direita (outros)" for p in ["NOVO", "PP", "UNIÃO", "REPUBLICANOS", "PRD", "DC", "PRTB", "PMB", "AGIR", "MISSÃO", "DEMOCRATA"]},
    **{p: "Centro" for p in ["PSD", "MDB", "PODE", "PSDB", "CIDADANIA", "AVANTE", "SOLIDARIEDADE", "MOBILIZA", "PATRIOTA"]},
    **{p: "Esquerda" for p in ["PT", "PSB", "PDT", "PSOL", "REDE", "PCDOB", "PC DO B", "PV", "PCB", "PSTU", "PCO", "UP"]},
}

def baixa(uf):
    r = urllib.request.Request(f"https://resultados.tse.jus.br/oficial/ele2026/6259/dados/{uf}/{uf}-c0005-e006259-u.json",
                               headers={"User-Agent": "Mozilla/5.0"})
    return json.load(urllib.request.urlopen(r, timeout=30))

linhas = []
for uf in UFS:
    d = baixa(uf)
    c = d["carg"][0]; assert c["cd"] == "5" and c["nv"] == "2"
    cands = []
    for ag in c["agr"]:
        for p in ag["par"]:
            for k in p["cand"]:
                cands.append(dict(nome=k["nmu"], partido=p["sg"], votos=int(k["vap"]), pct=float(k["pvapn"].replace(",", ".")), eleito=k["e"]))
    cands.sort(key=lambda x: -x["votos"])
    vv = int(d["v"]["vv"])
    for pos, k in enumerate(cands[:3], 1):
        linhas.append(dict(uf=uf.upper(), pos=pos, **k, grupo=GRUPOS.get(k["partido"], "?"), pct_secoes=float(d["s"]["pstn"].replace(",", ".")),
                           hora=f'{d["dg"]} {d["hg"]}', margem_2o_3o=round(cands[1]["votos"] / vv * 100 - cands[2]["votos"] / vv * 100, 1) if len(cands) > 2 else None))
D = pd.DataFrame(linhas)
D.to_csv(f"{AQUI}/senado_2026_parcial.csv", index=False)
top2 = D[D.pos <= 2]
print("Partidos sem classificação:", sorted(set(top2[top2.grupo == "?"].partido)))
print(f"Foto: {D.hora.iloc[0]} | seções apuradas média {D.drop_duplicates('uf').pct_secoes.mean():.0f}%")
print("\nVagas hoje, por grupo:\n", top2.grupo.value_counts().to_string())
print("\nPor partido:\n", top2.partido.value_counts().to_string())
print("\nPor UF (2 primeiros + 3º):")
for uf, g in D.groupby("uf", sort=False):
    print(f"{uf} ({g.pct_secoes.iloc[0]:.0f}% apurado): " + " | ".join(f"{r.pos}º {r.nome} ({r.partido}) {r.pct:.1f}%" for r in g.itertuples()))
