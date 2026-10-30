"""Seções do 2º turno encerradas depois de HH:MM (horário do campo DT_ENCERRAMENTO) e votos nelas. Uso: votos_apos_17h.py DIR2T SAIDA_PREFIXO"""
import glob, sys, zipfile
import pandas as pd
d, out = sys.argv[1:3]
COLS = ["SG_UF", "NM_MUNICIPIO", "NR_ZONA", "NR_SECAO", "DS_CARGO_PERGUNTA", "CD_TIPO_VOTAVEL", "NR_VOTAVEL", "QT_VOTOS", "QT_APTOS", "QT_COMPARECIMENTO", "DT_ABERTURA", "DT_ENCERRAMENTO"]
rs = []
for f in sorted(glob.glob(f"{d}/bweb_2t_*_*.zip")):
    z = zipfile.ZipFile(f)
    for n in z.namelist():
        if not n.endswith(".csv"): continue
        for ch in pd.read_csv(z.open(n), sep=";", encoding="latin-1", usecols=COLS, dtype=str, chunksize=1000000):
            ch = ch[ch.DS_CARGO_PERGUNTA == "Presidente"]
            ch = ch.assign(k=ch.SG_UF + "|" + ch.NM_MUNICIPIO + "|" + ch.NR_ZONA + "|" + ch.NR_SECAO, v=ch.QT_VOTOS.astype(int))
            rs.append(ch)
x = pd.concat(rs)
meta = x.drop_duplicates("k").set_index("k")[["SG_UF", "NM_MUNICIPIO", "QT_APTOS", "QT_COMPARECIMENTO", "DT_ABERTURA", "DT_ENCERRAMENTO"]]
meta["QT_COMPARECIMENTO"] = meta.QT_COMPARECIMENTO.astype(int); meta["QT_APTOS"] = meta.QT_APTOS.astype(int)
meta["enc"] = pd.to_datetime(meta.DT_ENCERRAMENTO, errors="coerce")
meta["abe"] = pd.to_datetime(meta.DT_ABERTURA, errors="coerce")
# horário gravado na hora local do estado -> converter para Brasília
OFF = {"AC": 2, "AM": 1, "RO": 1, "RR": 1, "MT": 1, "MS": 1}
meta["enc_brt"] = meta.enc + pd.to_timedelta(meta.SG_UF.map(OFF).fillna(0), unit="h")
meta["lula"] = x[(x.CD_TIPO_VOTAVEL == "1") & (x.NR_VOTAVEL == "13")].groupby("k").v.sum()
meta["flavio"] = x[(x.CD_TIPO_VOTAVEL == "1") & (x.NR_VOTAVEL == "22")].groupby("k").v.sum()
meta = meta.fillna({"lula": 0, "flavio": 0})
meta.to_csv(out + "_secoes_encerramento.csv")
print("seções:", len(meta), "sem DT_ENCERRAMENTO:", int(meta.enc.isna().sum()))
print(meta.enc.dt.date.value_counts().head())
meta["h"] = meta.enc_brt.dt.hour
print(pd.crosstab(meta.SG_UF, meta.h).to_string())
