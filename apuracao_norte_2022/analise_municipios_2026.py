"""Abstenção por município e evolução de Lula e Flávio do 1º para o 2º turno de 2026 (lê municipios_2026_1t_2t.csv)."""
import pandas as pd
pd.set_option("display.width", 220); pd.set_option("display.max_columns", 30)
D = pd.read_csv("municipios_2026_1t_2t.csv")
D["abst_pct_1t"] = D.abst_1t / D.aptos_1t * 100; D["abst_pct_2t"] = D.abst_2t / D.aptos_2t * 100
D["lula_pct_1t"] = D.lula_1t / D.vv_1t * 100; D["lula_pct_2t"] = D.lula_2t / D.vv_2t * 100
D["fla_pct_1t"] = D.fla_1t / D.vv_1t * 100; D["fla_pct_2t"] = D.fla_2t / D.vv_2t * 100
D["d_lula_votos"] = D.lula_2t - D.lula_1t; D["d_fla_votos"] = D.fla_2t - D.fla_1t
D["d_lula_pp"] = D.lula_pct_2t - D.lula_pct_1t; D["d_fla_pp"] = D.fla_pct_2t - D.fla_pct_1t
D["d_abst_pp"] = D.abst_pct_2t - D.abst_pct_1t; D["d_abst"] = D.abst_2t - D.abst_1t
D["apur_2t"] = D.sec_2t / D.sec_tot_2t * 100
BR = D[D.uf != "ZZ"].copy(); EX = D[D.uf == "ZZ"]
f = lambda x: f"{int(x):,}".replace(",", ".")
print(f"Municípios: {len(D)} ({len(BR)} no Brasil + {len(EX)} no exterior) | seções apuradas 2º turno: {D.sec_2t.sum()/D.sec_tot_2t.sum()*100:.2f}% | municípios com <99% apurado: {int((D.apur_2t<99).sum())} (maior atraso: {D.apur_2t.min():.1f}%)")
print(f"Brasil+exterior: abstenção 1º turno {D.abst_1t.sum()/D.aptos_1t.sum()*100:.2f}% ({f(D.abst_1t.sum())}) | 2º turno {D.abst_2t.sum()/D.aptos_2t.sum()*100:.2f}% ({f(D.abst_2t.sum())})")
cols = ["uf", "municipio", "aptos_2t", "abst_1t", "abst_2t", "abst_pct_1t", "abst_pct_2t", "d_abst_pp"]
print("\n== ABSTENÇÃO: maiores números absolutos no 2º turno (Brasil) =="); print(BR.nlargest(12, "abst_2t")[cols].round(2).to_string(index=False))
G = BR[BR.aptos_2t >= 50000]
print("\n== ABSTENÇÃO: maiores taxas no 2º turno (cidades com 50 mil+ eleitores) =="); print(G.nlargest(8, "abst_pct_2t")[cols].round(2).to_string(index=False))
print("\n== ABSTENÇÃO: menores taxas (50 mil+ eleitores) =="); print(G.nsmallest(5, "abst_pct_2t")[cols].round(2).to_string(index=False))
print("\n== ABSTENÇÃO: maior queda e maior alta da taxa 1º->2º turno (50 mil+) ==")
print(G.nsmallest(5, "d_abst_pp")[cols].round(2).to_string(index=False)); print(G.nlargest(5, "d_abst_pp")[cols].round(2).to_string(index=False))
print(f"\nCidades (Brasil) em que a abstenção caiu: {int((BR.d_abst_pp<0).sum())} | subiu: {int((BR.d_abst_pp>0).sum())} | igual: {int((BR.d_abst_pp==0).sum())}")
print("\n== EVOLUÇÃO LULA e FLÁVIO, 1º -> 2º turno ==")
print(f"Cidades em que Lula ganhou votos: {int((BR.d_lula_votos>0).sum())} / {len(BR)} | % de Lula subiu: {int((BR.d_lula_pp>0).sum())} | caiu: {int((BR.d_lula_pp<0).sum())}")
print(f"Cidades em que Flávio ganhou votos: {int((BR.d_fla_votos>0).sum())} / {len(BR)} | % de Flávio subiu: {int((BR.d_fla_pp>0).sum())} | caiu: {int((BR.d_fla_pp<0).sum())}")
print(f"Lula na frente no 1º turno em {int((BR.lula_1t>BR.fla_1t).sum())} cidades e no 2º em {int((BR.lula_2t>BR.fla_2t).sum())} | Flávio: {int((BR.fla_1t>BR.lula_1t).sum())} e {int((BR.fla_2t>BR.lula_2t).sum())}")
mudou_l = BR[(BR.fla_1t > BR.lula_1t) & (BR.lula_2t > BR.fla_2t)]; mudou_f = BR[(BR.lula_1t > BR.fla_1t) & (BR.fla_2t > BR.lula_2t)]
print(f"Cidades que passaram de Flávio (1º turno) para Lula (2º): {len(mudou_l)} | de Lula para Flávio: {len(mudou_f)}")
c2 = ["uf", "municipio", "lula_1t", "lula_2t", "d_lula_votos", "lula_pct_1t", "lula_pct_2t", "d_lula_pp"]
c3 = ["uf", "municipio", "fla_1t", "fla_2t", "d_fla_votos", "fla_pct_1t", "fla_pct_2t", "d_fla_pp"]
print("\nLula: maiores ganhos de votos (Brasil)"); print(BR.nlargest(8, "d_lula_votos")[c2].round(1).to_string(index=False))
print("\nFlávio: maiores ganhos de votos (Brasil)"); print(BR.nlargest(8, "d_fla_votos")[c3].round(1).to_string(index=False))
print("\nLula: maior alta em pontos % (50 mil+ eleitores)"); print(G.nlargest(6, "d_lula_pp")[c2].round(1).to_string(index=False))
print("\nFlávio: maior alta em pontos % (50 mil+ eleitores)"); print(G.nlargest(6, "d_fla_pp")[c3].round(1).to_string(index=False))
CAP = {("AC","RIO BRANCO"),("AL","MACEIÓ"),("AP","MACAPÁ"),("AM","MANAUS"),("BA","SALVADOR"),("CE","FORTALEZA"),("DF","BRASÍLIA"),("ES","VITÓRIA"),("GO","GOIÂNIA"),("MA","SÃO LUÍS"),("MT","CUIABÁ"),("MS","CAMPO GRANDE"),("MG","BELO HORIZONTE"),("PA","BELÉM"),("PB","JOÃO PESSOA"),("PR","CURITIBA"),("PE","RECIFE"),("PI","TERESINA"),("RJ","RIO DE JANEIRO"),("RN","NATAL"),("RS","PORTO ALEGRE"),("RO","PORTO VELHO"),("RR","BOA VISTA"),("SC","FLORIANÓPOLIS"),("SP","SÃO PAULO"),("SE","ARACAJU"),("TO","PALMAS")}
K = BR[[(u, m.upper()) in CAP for u, m in zip(BR.uf, BR.municipio)]]
print(f"\n== CAPITAIS ({len(K)} encontradas) ==")
print(K.sort_values("aptos_2t", ascending=False)[["uf","municipio","apur_2t","abst_pct_1t","abst_pct_2t","lula_pct_1t","lula_pct_2t","fla_pct_1t","fla_pct_2t","d_lula_votos","d_fla_votos"]].round(1).to_string(index=False))
D.to_csv("municipios_2026_analise.csv", index=False)
