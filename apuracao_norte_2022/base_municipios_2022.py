"""Base por município (UF+código TSE) com o 1º e o 2º turno de 2022 (Presidente), a partir dos boletins de urna."""
import glob, sys, zipfile
import pandas as pd
R1DIRS = sys.argv[1].split(","); R2DIR = sys.argv[2]
COLS = ["SG_UF", "CD_MUNICIPIO", "NM_MUNICIPIO", "NR_ZONA", "NR_SECAO", "DS_CARGO_PERGUNTA", "CD_TIPO_VOTAVEL", "NR_VOTAVEL", "QT_VOTOS", "QT_APTOS", "QT_COMPARECIMENTO"]
def arquivos(dirs, turno):
    a = {}
    for d in dirs:
        for f in glob.glob(f"{d}/bweb_{turno}t_*_*.zip"): a[f.split(f"bweb_{turno}t_")[1][:2]] = f
    return a
def ler(f):
    z = zipfile.ZipFile(f); n = [x for x in z.namelist() if x.endswith(".csv")][0]; v = []; s = []
    with z.open(n) as fh:
        for ch in pd.read_csv(fh, sep=";", encoding="latin-1", usecols=COLS, dtype=str, chunksize=500_000):
            ch = ch[ch.DS_CARGO_PERGUNTA == "Presidente"].copy(); ch["v"] = ch.QT_VOTOS.astype(int)
            ch["cat"] = "outros"; ch.loc[ch.NR_VOTAVEL == "13", "cat"] = "lula"; ch.loc[ch.NR_VOTAVEL == "22", "cat"] = "bolso"
            ch.loc[ch.CD_TIPO_VOTAVEL == "2", "cat"] = "branco"; ch.loc[ch.CD_TIPO_VOTAVEL == "3", "cat"] = "nulo"
            v.append(ch.groupby(["SG_UF", "CD_MUNICIPIO", "NM_MUNICIPIO", "cat"]).v.sum().reset_index())
            s.append(ch.drop_duplicates(["SG_UF", "CD_MUNICIPIO", "NR_ZONA", "NR_SECAO"])[["SG_UF", "CD_MUNICIPIO", "NR_ZONA", "NR_SECAO", "QT_APTOS", "QT_COMPARECIMENTO"]])
    V = pd.concat(v).groupby(["SG_UF", "CD_MUNICIPIO", "NM_MUNICIPIO", "cat"]).v.sum().unstack("cat", fill_value=0).reset_index()
    S = pd.concat(s).drop_duplicates(["SG_UF", "CD_MUNICIPIO", "NR_ZONA", "NR_SECAO"]); S["aptos"] = S.QT_APTOS.astype(int); S["comp"] = S.QT_COMPARECIMENTO.astype(int)
    S = S.groupby(["SG_UF", "CD_MUNICIPIO"])[["aptos", "comp"]].sum().reset_index()
    return V.merge(S, on=["SG_UF", "CD_MUNICIPIO"])
res = {}
for turno, arqs in ((1, arquivos(R1DIRS, 1)), (2, arquivos([R2DIR], 2))):
    assert len(arqs) == 28, (turno, len(arqs))
    partes = []
    for uf, f in sorted(arqs.items()):
        partes.append(ler(f)); print(f"{turno}t {uf}", end=" ", flush=True)
    res[turno] = pd.concat(partes)
M = res[1].merge(res[2], on=["SG_UF", "CD_MUNICIPIO"], suffixes=("_1", "_2"), how="outer")
M["NM"] = M.NM_MUNICIPIO_1.fillna(M.NM_MUNICIPIO_2)
M = M.drop(columns=["NM_MUNICIPIO_1", "NM_MUNICIPIO_2"]); M.to_csv("municipios_2022_1t_2t.csv.gz", index=False)
print("\nmunicípios:", len(M), "| faltando em algum turno:", int(M.isna().any(axis=1).sum()))
for t in ("1", "2"):
    print(f"Turno {t}: Lula {M['lula_'+t].sum():,} | Bolsonaro {M['bolso_'+t].sum():,} | brancos {M['branco_'+t].sum():,} | nulos {M['nulo_'+t].sum():,} | aptos {M['aptos_'+t].sum():,} | comparecimento {M['comp_'+t].sum():,}")
