"""Apuração por hora do 1º turno de 2022 (Presidente) na região Norte.

Fonte: TSE, Boletim de Urna (BU na Web) 1º turno 2022 -
https://dadosabertos.tse.jus.br/dataset/resultados-2022-boletim-de-urna
Hora da apuração = DT_BU_RECEBIDO (horário em que o BU foi recebido na totalização).
"""
import glob, sys, zipfile
import pandas as pd

SRC = sys.argv[1]
OUT = sys.argv[2]
REGIAO = sys.argv[3] if len(sys.argv) > 3 else "norte"
UFS = (sys.argv[4].split(",") if len(sys.argv) > 4 else ["AC", "AM", "AP", "PA", "RO", "RR", "TO"])
COLS = ["SG_UF", "CD_MUNICIPIO", "NR_ZONA", "NR_SECAO", "DS_CARGO_PERGUNTA",
        "DT_BU_RECEBIDO", "QT_COMPARECIMENTO", "CD_TIPO_VOTAVEL", "NR_VOTAVEL", "QT_VOTOS"]

frames = []
for uf in UFS:
    z = zipfile.ZipFile(glob.glob(f"{SRC}/bweb_1t_{uf}_*.zip")[0])
    nome = [n for n in z.namelist() if n.endswith(".csv")][0]
    with z.open(nome) as f:
        for ch in pd.read_csv(f, sep=";", encoding="latin-1", usecols=COLS, dtype=str, chunksize=500_000):
            frames.append(ch[ch.DS_CARGO_PERGUNTA == "Presidente"].drop(columns="DS_CARGO_PERGUNTA"))
df = pd.concat(frames, ignore_index=True)
df["QT_VOTOS"] = df.QT_VOTOS.astype(int)
df["QT_COMPARECIMENTO"] = df.QT_COMPARECIMENTO.astype(int)
df["recebido"] = pd.to_datetime(df.DT_BU_RECEBIDO, format="%d/%m/%Y %H:%M:%S")
df["secao_id"] = df.SG_UF + "-" + df.CD_MUNICIPIO + "-" + df.NR_ZONA + "-" + df.NR_SECAO

# Uma linha por seção: horário de recebimento (menor, se repetido) e comparecimento
sec = df.groupby("secao_id").agg(uf=("SG_UF", "first"), recebido=("recebido", "min"),
                                 comparecimento=("QT_COMPARECIMENTO", "first")).reset_index()

# Votos por seção: Lula (13), Bolsonaro (22), outros nominais, brancos/nulos
# CD_TIPO_VOTAVEL: 1=nominal, 2=branco, 3=nulo
nome = df.NR_VOTAVEL.map({"13": "lula", "22": "bolsonaro"})
nome = nome.where(nome.notna() | (df.CD_TIPO_VOTAVEL != "1"), "outros")
nome = nome.fillna(df.CD_TIPO_VOTAVEL.map({"2": "branco", "3": "nulo"}))
df["grupo"] = nome
pv = df.pivot_table(index="secao_id", columns="grupo", values="QT_VOTOS", aggfunc="sum", fill_value=0)
sec = sec.merge(pv, left_on="secao_id", right_index=True, how="left").fillna(0)
for c in ["lula", "bolsonaro", "outros", "branco", "nulo"]:
    if c not in sec: sec[c] = 0
sec["hora"] = sec.recebido.dt.floor("h")
sec.to_csv(f"{OUT}/secoes_{REGIAO}_1t_2022.csv.gz", index=False)

def acumular(g):
    h = g.groupby("hora")[["lula", "bolsonaro", "outros", "branco", "nulo", "comparecimento"]].sum()
    h["secoes"] = g.groupby("hora").size()
    h = h.reindex(pd.date_range(sec.hora.min(), sec.hora.max(), freq="h"), fill_value=0)
    c = h.cumsum()
    total = len(g)
    c["pct_secoes"] = (c.secoes / total * 100).round(2)
    c["validos"] = c.lula + c.bolsonaro + c.outros
    c["lula_pct_validos"] = (c.lula / c.validos * 100).round(2)
    c["bolsonaro_pct_validos"] = (c.bolsonaro / c.validos * 100).round(2)
    c["dif_lula_menos_bolsonaro_pp"] = (c.lula_pct_validos - c.bolsonaro_pct_validos).round(2)
    c.insert(0, "secoes_novas_na_hora", h.secoes)
    c.index.name = "hora_brasilia"
    c["total_secoes"] = total
    return c.fillna(0)

res = {}
for uf, g in sec.groupby("uf"):
    r = acumular(g); r.insert(0, "uf", uf); res[uf] = r
r = acumular(sec); r.insert(0, "uf", REGIAO.upper()); res[REGIAO.upper()] = r
out = pd.concat(res.values()).reset_index()
out.to_csv(f"{OUT}/apuracao_por_hora_{REGIAO}_1t_2022.csv", index=False)
print(out[out.uf == REGIAO.upper()][["hora_brasilia","secoes_novas_na_hora","secoes","pct_secoes","lula_pct_validos","bolsonaro_pct_validos"]].to_string(index=False))
print(sec.groupby("uf").size())
print(sec[["lula","bolsonaro","outros","branco","nulo"]].sum())
