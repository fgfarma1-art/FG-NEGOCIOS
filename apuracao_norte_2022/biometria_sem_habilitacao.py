"""QT_ELEI_BIOM_SEM_HABILITACAO (eleitores com biometria que não foram habilitados por ela) por seção, Presidente. Uso: DIR TURNO SAIDA.csv"""
import glob, sys, zipfile
import pandas as pd
d, t, out = sys.argv[1:4]
COLS = ["SG_UF", "NM_MUNICIPIO", "NR_ZONA", "NR_SECAO", "DS_CARGO_PERGUNTA", "CD_TIPO_VOTAVEL", "NR_VOTAVEL", "QT_VOTOS", "QT_COMPARECIMENTO", "QT_ELEI_BIOM_SEM_HABILITACAO"]
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
m = x.drop_duplicates("k").set_index("k")[["SG_UF", "NM_MUNICIPIO", "QT_COMPARECIMENTO", "QT_ELEI_BIOM_SEM_HABILITACAO"]]
m["comp"] = m.QT_COMPARECIMENTO.astype(int); m["nh"] = pd.to_numeric(m.QT_ELEI_BIOM_SEM_HABILITACAO, errors="coerce")
m["lula"] = x[(x.CD_TIPO_VOTAVEL == "1") & (x.NR_VOTAVEL == "13")].groupby("k").v.sum()
m["flavio"] = x[(x.CD_TIPO_VOTAVEL == "1") & (x.NR_VOTAVEL == "22")].groupby("k").v.sum()
m = m.fillna({"lula": 0, "flavio": 0}).drop(columns=["QT_COMPARECIMENTO", "QT_ELEI_BIOM_SEM_HABILITACAO"])
m.to_csv(out)
print("seções:", len(m), "| nh nulo:", int(m.nh.isna().sum()), "| total nh:", int(m.nh.sum()), "| comparecimento:", int(m.comp.sum()), "| %:", round(100 * m.nh.sum() / m.comp.sum(), 3))
print("seções com nh>0:", int((m.nh > 0).sum()), "| nh>comp:", int((m.nh > m.comp).sum()))
