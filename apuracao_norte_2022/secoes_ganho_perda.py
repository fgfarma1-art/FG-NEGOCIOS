"""Seções com maior ganho de Lula e maior perda do 2º candidato (Bolsonaro 2022 / Flávio 2026) entre 1º e 2º turno.
Uso: secoes_ganho_perda.py DIR_1T DIR_2T SAIDA_PREFIXO [UFs] [ANO]
Só seções com votos válidos nos dois turnos, mesmo local de votação e eleitorado similar (evita troca de endereço)."""
import glob, sys, zipfile
import pandas as pd
d1, d2, out = sys.argv[1:4]
ufs = sys.argv[4].split(",") if len(sys.argv) > 4 and sys.argv[4] else None
COLS = ["SG_UF", "CD_MUNICIPIO", "NM_MUNICIPIO", "NR_ZONA", "NR_SECAO", "NR_LOCAL_VOTACAO", "DS_CARGO_PERGUNTA", "CD_TIPO_VOTAVEL", "NR_VOTAVEL", "QT_VOTOS", "QT_APTOS", "QT_COMPARECIMENTO", "DT_ABERTURA", "DT_ENCERRAMENTO"]
def ler(d, t):
    fs = []
    for f in sorted(glob.glob(f"{d}/bweb_{t}t_*_*.zip")):
        uf = f.split(f"bweb_{t}t_")[1][:2]
        if ufs is None or uf in ufs: fs.append(f)
    r = []
    for f in fs:
        z = zipfile.ZipFile(f)
        for n in z.namelist():
            if not n.endswith(".csv"): continue
            for ch in pd.read_csv(z.open(n), sep=";", encoding="latin-1", usecols=COLS, dtype=str, chunksize=500000):
                ch = ch[ch.DS_CARGO_PERGUNTA == "Presidente"]
                r.append(ch)
    x = pd.concat(r)
    x["v"] = x.QT_VOTOS.astype(int)
    x["k"] = x.SG_UF + "-" + x.CD_MUNICIPIO + "-" + x.NR_ZONA + "-" + x.NR_SECAO
    meta = x.drop_duplicates("k").set_index("k")[["SG_UF", "NM_MUNICIPIO", "NR_LOCAL_VOTACAO", "QT_APTOS", "QT_COMPARECIMENTO", "DT_ABERTURA", "DT_ENCERRAMENTO"]]
    meta[["QT_APTOS", "QT_COMPARECIMENTO"]] = meta[["QT_APTOS", "QT_COMPARECIMENTO"]].astype(int)
    val = x[x.CD_TIPO_VOTAVEL.isin(["1", "2"])].groupby("k").v.sum().rename("validos")
    lu = x[(x.CD_TIPO_VOTAVEL == "1") & (x.NR_VOTAVEL == "13")].groupby("k").v.sum().rename("lula")
    ou = x[(x.CD_TIPO_VOTAVEL == "1") & (x.NR_VOTAVEL == "22")].groupby("k").v.sum().rename("outro")
    return meta.join([val, lu, ou]).fillna({"lula": 0, "outro": 0, "validos": 0})
a, b = ler(d1, 1), ler(d2, 2)
m = a.join(b, how="inner", lsuffix="_1", rsuffix="_2")  # noqa
n0 = len(m)
m = m[(m.validos_1 >= 50) & (m.validos_2 >= 50)]
m = m[m.NR_LOCAL_VOTACAO_1 == m.NR_LOCAL_VOTACAO_2]
m = m[((m.QT_APTOS_2 - m.QT_APTOS_1).abs() / m.QT_APTOS_1) <= 0.10]
print(f"seções nos dois turnos: {n0}; após filtros (válidos>=50, mesmo local, aptos ±10%): {len(m)}")
m["d_lula"] = m.lula_2 - m.lula_1; m["d_outro"] = m.outro_2 - m.outro_1
m["d_lula_pp"] = 100 * (m.lula_2 / m.validos_2 - m.lula_1 / m.validos_1)
m["d_outro_pp"] = 100 * (m.outro_2 / m.validos_2 - m.outro_1 / m.validos_1)
m["d_lula_pct"] = 100 * (m.lula_2 / m.lula_1.where(m.lula_1 > 0) - 1)
m["d_outro_pct"] = 100 * (m.outro_2 / m.outro_1.where(m.outro_1 > 0) - 1)
c = ["SG_UF_1", "NM_MUNICIPIO_1", "NR_LOCAL_VOTACAO_1", "validos_1", "validos_2", "lula_1", "lula_2", "d_lula", "d_lula_pp", "d_lula_pct", "outro_1", "outro_2", "d_outro", "d_outro_pp", "d_outro_pct", "DT_ENCERRAMENTO_2"]
m.sort_values("d_lula", ascending=False).head(50)[c].to_csv(out + "_lula_ganho_votos.csv")
m.sort_values("d_lula_pp", ascending=False).head(50)[c].to_csv(out + "_lula_ganho_pp.csv")
m.sort_values("d_outro").head(50)[c].to_csv(out + "_outro_perda_votos.csv")
m.sort_values("d_outro_pp").head(50)[c].to_csv(out + "_outro_perda_pp.csv")
pd.set_option("display.width", 250)
for t, f in [("Lula: maior ganho em votos", "d_lula"), ("Lula: maior ganho em p.p.", "d_lula_pp")]:
    print("\n", t); print(m.sort_values(f, ascending=False).head(10)[c[:10]].round(1).to_string())
for t, f in [("2º cand.: maior perda em votos", "d_outro"), ("2º cand.: maior perda em p.p.", "d_outro_pp")]:
    print("\n", t); print(m.sort_values(f).head(10)[["SG_UF_1", "NM_MUNICIPIO_1", "NR_LOCAL_VOTACAO_1", "validos_1", "validos_2", "outro_1", "outro_2", "d_outro", "d_outro_pp", "d_outro_pct"]].round(1).to_string())
