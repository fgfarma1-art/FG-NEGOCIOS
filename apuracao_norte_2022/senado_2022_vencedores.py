"""Senadores eleitos em 2022 (27 vagas, 1 por UF), a partir dos boletins de urna. Partido = o do candidato em 2022."""
import glob, sys, zipfile
import pandas as pd
from grupos_partidos import GRUPOS
DIRS = sys.argv[1:]
arqs = {}
for d in DIRS:
    for f in glob.glob(f"{d}/bweb_1t_*_*.zip"): arqs[f.split("bweb_1t_")[1][:2]] = f
arqs.pop("ZZ", None)
COLS = ["SG_UF", "DS_CARGO_PERGUNTA", "CD_TIPO_VOTAVEL", "NR_VOTAVEL", "NM_VOTAVEL", "SG_PARTIDO", "QT_VOTOS"]
rows = []
for uf, f in sorted(arqs.items()):
    z = zipfile.ZipFile(f); n = [x for x in z.namelist() if x.endswith(".csv")][0]
    with z.open(n) as fh:
        for ch in pd.read_csv(fh, sep=";", encoding="latin-1", usecols=COLS, dtype=str, chunksize=500_000):
            ch = ch[(ch.DS_CARGO_PERGUNTA == "Senador") & (ch.CD_TIPO_VOTAVEL == "1")]
            if len(ch): rows.append(ch.assign(v=ch.QT_VOTOS.astype(int)).groupby(["SG_UF", "NR_VOTAVEL", "NM_VOTAVEL", "SG_PARTIDO"]).v.sum().reset_index())
D = pd.concat(rows).groupby(["SG_UF", "NR_VOTAVEL", "NM_VOTAVEL", "SG_PARTIDO"]).v.sum().reset_index().sort_values(["SG_UF", "v"], ascending=[True, False])
W = D.groupby("SG_UF").head(1).copy()
W["grupo"] = W.SG_PARTIDO.map(GRUPOS).fillna("?")
W.to_csv("senado_2022_eleitos.csv", index=False)
print("UFs com senador em 2022:", len(W), "| sem classificação:", sorted(set(W[W.grupo == '?'].SG_PARTIDO)))
print(W.grupo.value_counts().to_string()); print(W.SG_PARTIDO.value_counts().to_string())
print(W[["SG_UF", "NM_VOTAVEL", "SG_PARTIDO", "v"]].to_string(index=False))
