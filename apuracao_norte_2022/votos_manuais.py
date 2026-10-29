"""Tipos de urna / apuração manual no BU. Uso: votos_manuais.py DIR TURNO SAIDA.csv"""
import glob, sys, zipfile
import pandas as pd
d, t, out = sys.argv[1:4]
COLS = ["SG_UF", "NM_MUNICIPIO", "NR_ZONA", "NR_SECAO", "DS_CARGO_PERGUNTA", "CD_TIPO_VOTAVEL", "NR_VOTAVEL", "QT_VOTOS", "QT_COMPARECIMENTO", "CD_TIPO_URNA", "DS_TIPO_URNA", "NR_JUNTA_APURADORA", "NR_TURMA_APURADORA", "DS_SECOES_AGREGADAS"]
rs = []
for f in sorted(glob.glob(f"{d}/bweb_{t}t_*_*.zip")):
    z = zipfile.ZipFile(f)
    for n in z.namelist():
        if not n.endswith(".csv"): continue
        for ch in pd.read_csv(z.open(n), sep=";", encoding="latin-1", usecols=COLS, dtype=str, chunksize=1000000):
            ch = ch[ch.DS_CARGO_PERGUNTA == "Presidente"]
            ch = ch.assign(k=ch.SG_UF + "|" + ch.NM_MUNICIPIO + "|" + ch.NR_ZONA + "|" + ch.NR_SECAO, v=ch.QT_VOTOS.astype(int))
            rs.append(ch)
x = pd.concat(rs)
meta = x.drop_duplicates("k").set_index("k")[["SG_UF", "CD_TIPO_URNA", "DS_TIPO_URNA", "NR_JUNTA_APURADORA", "NR_TURMA_APURADORA", "DS_SECOES_AGREGADAS", "QT_COMPARECIMENTO"]]
meta["comp"] = meta.QT_COMPARECIMENTO.astype(int)
vv = x[x.CD_TIPO_VOTAVEL.isin(["1", "2"])].groupby("k").v.sum()
meta["validos"] = vv
meta["lula"] = x[(x.CD_TIPO_VOTAVEL == "1") & (x.NR_VOTAVEL == "13")].groupby("k").v.sum()
meta["flavio"] = x[(x.CD_TIPO_VOTAVEL == "1") & (x.NR_VOTAVEL == "22")].groupby("k").v.sum()
meta = meta.fillna({"lula": 0, "flavio": 0, "validos": 0})
meta.to_csv(out)
pd.set_option("display.width", 220)
print(meta.groupby(["CD_TIPO_URNA", "DS_TIPO_URNA"]).agg(secoes=("comp", "size"), comp=("comp", "sum"), validos=("validos", "sum"), lula=("lula", "sum"), flavio=("flavio", "sum")).to_string())
print("junta apuradora != -1:", int((meta.NR_JUNTA_APURADORA != "-1").sum()), "| turma != -1:", int((meta.NR_TURMA_APURADORA != "-1").sum()))
print(meta.DS_SECOES_AGREGADAS.value_counts().head(3).to_string())
