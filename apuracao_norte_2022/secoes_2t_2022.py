"""Seções do 2º turno de 2022 (Presidente) com horário de recebimento do BU: base para comparar 2026 no mesmo horário.
Uso: python3 -I secoes_2t_2022.py <pasta com bweb_2t_*.zip> <saida.csv.gz>"""
import glob, sys, zipfile
import pandas as pd
src, out = sys.argv[1], sys.argv[2]
COLS = ["SG_UF", "CD_MUNICIPIO", "NR_ZONA", "NR_SECAO", "DS_CARGO_PERGUNTA", "CD_TIPO_VOTAVEL", "NR_VOTAVEL", "QT_VOTOS", "DT_BU_RECEBIDO"]
partes = []
for f in sorted(glob.glob(f"{src}/bweb_2t_*.zip")):
    z = zipfile.ZipFile(f); n = [x for x in z.namelist() if x.endswith(".csv")][0]; fr = []
    with z.open(n) as fh:
        for ch in pd.read_csv(fh, sep=";", encoding="latin-1", usecols=COLS, dtype=str, chunksize=500_000):
            ch = ch[ch.DS_CARGO_PERGUNTA == "Presidente"].copy(); ch["v"] = ch.QT_VOTOS.astype(int)
            ch["cat"] = "x"; ch.loc[ch.NR_VOTAVEL == "13", "cat"] = "lula"; ch.loc[ch.NR_VOTAVEL == "22", "cat"] = "bolsonaro"
            ch.loc[ch.CD_TIPO_VOTAVEL == "2", "cat"] = "branco"; ch.loc[ch.CD_TIPO_VOTAVEL == "3", "cat"] = "nulo"
            ch["secao_id"] = ch.SG_UF + "-" + ch.CD_MUNICIPIO + "-" + ch.NR_ZONA + "-" + ch.NR_SECAO
            g = ch.groupby(["secao_id", "SG_UF", "cat"]).v.sum().unstack("cat", fill_value=0).reset_index()
            rec = ch.drop_duplicates("secao_id").set_index("secao_id").DT_BU_RECEBIDO
            g["recebido"] = g.secao_id.map(rec); fr.append(g)
    partes.append(pd.concat(fr).groupby(["secao_id", "SG_UF"], as_index=False).agg({"lula": "sum", "bolsonaro": "sum", "branco": "sum", "nulo": "sum", "recebido": "first"}))
    print(f.split("bweb_2t_")[1][:2], end=" ", flush=True)
S = pd.concat(partes).rename(columns={"SG_UF": "uf"}); S["recebido"] = pd.to_datetime(S.recebido, format="%d/%m/%Y %H:%M:%S")
S.to_csv(out, index=False)
print(f"\nseções {len(S):,} | Lula {S.lula.sum():,} | Bolsonaro {S.bolsonaro.sum():,} | 1ª urna {S.recebido.min()} | última {S.recebido.max()}")
