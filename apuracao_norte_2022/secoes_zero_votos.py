"""Conta seções com 0 votos para Lula (13) e Flávio/Bolsonaro (22) para Presidente. Uso: secoes_zero_votos.py DIR TURNO SAIDA.csv"""
import glob, sys, zipfile
import pandas as pd
d, t, out = sys.argv[1:4]
COLS = ["SG_UF", "CD_MUNICIPIO", "NM_MUNICIPIO", "NR_ZONA", "NR_SECAO", "DS_CARGO_PERGUNTA", "CD_TIPO_VOTAVEL", "NR_VOTAVEL", "QT_VOTOS", "QT_APTOS", "QT_COMPARECIMENTO"]
rs = []
for f in sorted(glob.glob(f"{d}/bweb_{t}t_*_*.zip")):
    z = zipfile.ZipFile(f)
    for n in z.namelist():
        if not n.endswith(".csv"): continue
        for ch in pd.read_csv(z.open(n), sep=";", encoding="latin-1", usecols=COLS, dtype=str, chunksize=1000000):
            ch = ch[ch.DS_CARGO_PERGUNTA == "Presidente"].copy()
            ch["v"] = ch.QT_VOTOS.astype(int)
            ch["k"] = ch.SG_UF + "|" + ch.NM_MUNICIPIO + "|" + ch.NR_ZONA + "|" + ch.NR_SECAO
            rs.append(pd.DataFrame({"k": ch.k, "tipo": ch.CD_TIPO_VOTAVEL, "n": ch.NR_VOTAVEL, "v": ch.v, "aptos": ch.QT_APTOS.astype(int), "comp": ch.QT_COMPARECIMENTO.astype(int)}))
x = pd.concat(rs)
meta = x.drop_duplicates("k").set_index("k")[["aptos", "comp"]]
val = x[x.tipo.isin(["1", "2"])].groupby("k").v.sum().rename("validos")
lu = x[(x.tipo == "1") & (x.n == "13")].groupby("k").v.sum().rename("lula")
fl = x[(x.tipo == "1") & (x.n == "22")].groupby("k").v.sum().rename("flavio")
s = meta.join([val, lu, fl]).fillna(0)
s.to_csv(out)
tot = len(s); c = s[s.comp > 0]; v = s[s.validos > 0]
print(f"seções: {tot}; com comparecimento>0: {len(c)}; com votos válidos>0: {len(v)}")
for nome, col in [("Lula", "lula"), ("Flávio/Bolsonaro", "flavio")]:
    print(f"{nome}: 0 votos em {int((s[col]==0).sum())} seções | só entre as com comparecimento>0: {int((c[col]==0).sum())} | só entre as com válidos>0: {int((v[col]==0).sum())}")
print("ambos 0 (válidos>0):", int(((v.lula == 0) & (v.flavio == 0)).sum()))
print("0 votos e ≥50 válidos — Lula:", int(((s.validos >= 50) & (s.lula == 0)).sum()), "Flávio:", int(((s.validos >= 50) & (s.flavio == 0)).sum()))
