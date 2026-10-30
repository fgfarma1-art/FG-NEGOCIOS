"""Municípios com mudança 1T->2T (2026) fora do padrão esperado pelo histórico (modelo + 2022). Saída: anomalias_municipios_2t.csv"""
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import KFold
b = pd.read_csv("municipios_2026_analise.csv")
h = pd.read_csv("municipios_2022_1t_2t.csv.gz")
b["CD"] = b.cod_tse.astype(int)
d = b.merge(h, left_on=["uf", "CD"], right_on=["SG_UF", "CD_MUNICIPIO"], how="left", suffixes=("", "_22"))
d = d[(d.sec_1t == d.sec_tot_1t) & (d.sec_2t == d.sec_tot_2t)].copy()
d["vv1"] = d.lula_1t + d.fla_1t + (d.vv_1t - d.lula_1t - d.fla_1t)
# 2026
d["L1"] = d.lula_1t / d.vv_1t; d["F1"] = d.fla_1t / d.vv_1t; d["O1"] = 1 - d.L1 - d.F1
d["inv1"] = (d.br_1t + d.nu_1t) / d.comp_1t; d["ab1"] = d.abst_1t / d.aptos_1t
d["la"] = np.log(d.aptos_1t)
# 2022 (continuidade local)
v1 = d.bolso_1 + d.lula_1 + d.outros; v2 = d.bolso_2 + d.lula_2
d["L22_1"] = d.lula_1 / v1; d["B22_1"] = d.bolso_1 / v1
d["dL22"] = d.lula_2 / v2 - d.L22_1
d["dab22"] = (1 - d.comp_2 / d.aptos_2) - (1 - d.comp_1 / d.aptos_1)
d["sw1"] = d.L1 - d.L22_1
d["ufc"] = d.uf.astype("category").cat.codes
# alvos 2T
d["L2"] = d.lula_2t / (d.lula_2t + d.fla_2t); d["ab2"] = d.abst_2t / d.aptos_2t
d["inv2"] = (d.br_2t + d.nu_2t) / d.comp_2t
X = ["L1", "F1", "O1", "inv1", "ab1", "la", "L22_1", "B22_1", "dL22", "dab22", "sw1", "ufc"]
res = {}
for y, base, n in [("L2", None, d.lula_2t + d.fla_2t), ("ab2", None, d.aptos_2t), ("inv2", None, d.comp_2t)]:
    ok = d[X].notna().all(axis=1) & d[y].notna()
    pred = pd.Series(np.nan, index=d.index)
    idx = d.index[ok]
    for tr, te in KFold(5, shuffle=True, random_state=0).split(idx):
        m = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, max_leaf_nodes=15, categorical_features=[len(X) - 1], random_state=0)
        m.fit(d.loc[idx[tr], X], d.loc[idx[tr], y]); pred[idx[te]] = m.predict(d.loc[idx[te], X])
    r = d[y] - pred
    # escala robusta por faixa de tamanho (inclui o erro do próprio modelo, não só o ruído binomial)
    q = pd.qcut(np.log(n), 15, labels=False, duplicates="drop")
    sd = r.groupby(q).transform(lambda v: 1.4826 * (v - v.median()).abs().median())
    z = (r - r.groupby(q).transform("median")) / sd
    d["exc_" + y] = r * n          # votos a mais/menos do que o esperado
    d["esp_" + y] = pred; d["res_" + y] = r; d["z_" + y] = z
d["zmax"] = d[["z_L2", "z_ab2", "z_inv2"]].abs().max(axis=1)
d["zsoma"] = np.sqrt((d[["z_L2", "z_ab2", "z_inv2"]] ** 2).sum(axis=1))
# integridade
d["int_comp_gt_aptos"] = d.comp_2t > d.aptos_2t
d["int_soma"] = (d.lula_2t + d.fla_2t + d.br_2t + d.nu_2t) != d.comp_2t
d["int_aptos_dif"] = (d.aptos_2t - d.aptos_1t).abs() / d.aptos_1t > 0.01
cols = ["uf", "municipio", "aptos_1t", "L1", "L2", "esp_L2", "res_L2", "z_L2", "ab1", "ab2", "esp_ab2", "z_ab2", "inv1", "inv2", "esp_inv2", "z_inv2", "exc_L2", "exc_ab2", "exc_inv2", "zmax", "zsoma", "int_comp_gt_aptos", "int_soma", "int_aptos_dif"]
d.sort_values("zsoma", ascending=False)[cols].to_csv("anomalias_municipios_2t.csv", index=False)
print(len(d), "municípios;", d.dropna(subset=["z_L2"]).shape[0], "com modelo")
for c in ["int_comp_gt_aptos", "int_soma", "int_aptos_dif"]: print(c, int(d[c].sum()))
print("R2 fora da amostra (L2, ab2, inv2):", [round(1 - ((d[y] - d["esp_" + y]) ** 2).sum() / ((d[y] - d[y].mean()) ** 2).sum(), 3) for y in ["L2", "ab2", "inv2"]])
for c in ["z_L2", "z_ab2", "z_inv2"]: print(c, "|z|>4:", int((d[c].abs() > 4).sum()), "|z|>6:", int((d[c].abs() > 6).sum()))
pd.set_option("display.width", 250)
print(d.sort_values("zsoma", ascending=False)[cols[:14]].head(25).round(3).to_string(index=False))
