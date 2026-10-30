"""Resultado final do 1º turno de 2022 (Presidente), todos os candidatos, somando os BUs de 27 UFs + exterior."""
import glob, sys, zipfile
import pandas as pd

DIRS = sys.argv[1:]          # pastas com bweb_1t_<UF>_*.zip
COLS = ["SG_UF", "CD_MUNICIPIO", "NR_ZONA", "NR_SECAO", "DS_CARGO_PERGUNTA", "CD_TIPO_VOTAVEL", "NR_VOTAVEL", "NM_VOTAVEL",
        "QT_VOTOS", "QT_APTOS", "QT_COMPARECIMENTO", "QT_ABSTENCOES"]
arqs = {}
for d in DIRS:
    for f in glob.glob(f"{d}/bweb_1t_*_*.zip"):
        arqs[f.split("bweb_1t_")[1][:2]] = f          # uma por UF (links duplicados colapsam)
assert len(arqs) == 28, sorted(arqs)
votos, secoes = [], []
for uf, f in sorted(arqs.items()):
    z = zipfile.ZipFile(f); n = [x for x in z.namelist() if x.endswith(".csv")][0]
    with z.open(n) as fh:
        for ch in pd.read_csv(fh, sep=";", encoding="latin-1", usecols=COLS, dtype=str, chunksize=500_000):
            ch = ch[ch.DS_CARGO_PERGUNTA == "Presidente"]
            ch = ch.assign(v=ch.QT_VOTOS.astype(int))
            votos.append(ch.groupby(["CD_TIPO_VOTAVEL", "NR_VOTAVEL", "NM_VOTAVEL"]).v.sum().reset_index())
            secoes.append(ch.drop_duplicates(["SG_UF", "CD_MUNICIPIO", "NR_ZONA", "NR_SECAO"])[["SG_UF", "CD_MUNICIPIO", "NR_ZONA", "NR_SECAO", "QT_APTOS", "QT_COMPARECIMENTO", "QT_ABSTENCOES"]])
    print(uf, end=" ", flush=True)
V = pd.concat(votos).groupby(["CD_TIPO_VOTAVEL", "NR_VOTAVEL", "NM_VOTAVEL"]).v.sum().reset_index()
S = pd.concat(secoes).drop_duplicates(["SG_UF", "CD_MUNICIPIO", "NR_ZONA", "NR_SECAO"])
for c in ("QT_APTOS", "QT_COMPARECIMENTO", "QT_ABSTENCOES"): S[c] = S[c].astype(int)
nom = V[V.CD_TIPO_VOTAVEL == "1"].sort_values("v", ascending=False).copy()
validos = nom.v.sum(); comp = S.QT_COMPARECIMENTO.sum()
nom["pct_validos"] = (nom.v / validos * 100).round(2)
nom.rename(columns={"NR_VOTAVEL": "numero", "NM_VOTAVEL": "candidato", "v": "votos"}).drop(columns="CD_TIPO_VOTAVEL").to_csv("resultado_final_2022_1t.csv", index=False)
branco = V[V.CD_TIPO_VOTAVEL == "2"].v.sum(); nulo = V[V.CD_TIPO_VOTAVEL == "3"].v.sum()
print(f"\nseções {len(S):,} | aptos {S.QT_APTOS.sum():,} | comparecimento {comp:,} ({comp/S.QT_APTOS.sum()*100:.2f}%) | abstenções {S.QT_ABSTENCOES.sum():,} ({S.QT_ABSTENCOES.sum()/S.QT_APTOS.sum()*100:.2f}%)")
print(f"válidos {validos:,} | brancos {branco:,} | nulos {nulo:,} | soma {validos+branco+nulo:,} (== comparecimento? {validos+branco+nulo==comp})\n")
print(nom[["NR_VOTAVEL", "NM_VOTAVEL", "v", "pct_validos"]].to_string(index=False))
