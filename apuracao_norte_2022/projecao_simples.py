"""Projeção SIMPLES: aplica ao placar de 2026 o quanto o placar de cada estado mudou em 2022
entre este mesmo horário e o fim da apuração. Pressupõe a mesma ordem de chegada das urnas de 2022."""
import pandas as pd
from corte2022 import secoes_ate
from datetime import datetime
AQUI = __file__.rsplit("/", 1)[0]
h = pd.read_csv(f"{AQUI}/historico_2026_top10.csv").tail(11).set_index("uf")
inst = datetime.strptime(h.loc["SP"].gerado_em, "%d/%m/%Y %H:%M:%S")
s = pd.read_csv(f"{AQUI}/secoes_top10_1t_2022.csv.gz", parse_dates=["recebido"])
corte = datetime(2022, 10, 2, inst.hour, inst.minute, inst.second)
def pct(d):
    g = d.groupby("uf")[["lula", "bolsonaro", "outros"]].sum(); v = g.sum(axis=1)
    return g.div(v, axis=0) * 100, g.sum(axis=1)
agora22, _ = pct(secoes_ate(s, h.drop("TOP10").reset_index()[["uf", "gerado_em"]])); final22, vot22 = pct(s)
linhas = []
for uf in ["SP", "MG", "RJ", "BA", "RS", "PR", "PE", "CE", "PA", "SC"]:
    r = h.loc[uf]; vv = r.votos_validos
    l26, b26 = r.v_LULA / vv * 100, r["v_FLAVIO BOLSONARO"] / vv * 100
    dl, db = final22.loc[uf, "lula"] - agora22.loc[uf, "lula"], final22.loc[uf, "bolsonaro"] - agora22.loc[uf, "bolsonaro"]
    pl, pb = l26 + dl, b26 + db
    # peso do estado = votos válidos finais estimados (2026 hoje / fração apurada)
    peso = vv / (r.pct_secoes / 100)
    linhas.append(dict(uf=uf, apurado=r.pct_secoes, lula_hoje=l26, flavio_hoje=b26, ajuste_lula=dl, ajuste_bolso=db, lula_proj=pl, flavio_proj=pb, peso=peso))
d = pd.DataFrame(linhas).set_index("uf")
tl = (d.lula_proj * d.peso).sum() / d.peso.sum(); tb = (d.flavio_proj * d.peso).sum() / d.peso.sum()
print(f"Hoje {inst:%H:%M}\n", d.drop(columns="peso").round(1).to_string())
print(f"\nSoma ponderada dos 10 estados: Lula {tl:.1f}% | Flávio {tb:.1f}%  (hoje: Lula {(d.lula_hoje*d.peso).sum()/d.peso.sum():.1f}% | Flávio {(d.flavio_hoje*d.peso).sum()/d.peso.sum():.1f}%)")
d.to_csv(f"{AQUI}/projecao_simples_top10.csv")
