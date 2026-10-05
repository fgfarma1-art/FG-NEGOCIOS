"""Câmara dos Deputados: eleitos em 2022 (consulta_cand_2022, situação final) x cadeiras conquistadas em 2026 (TSE ao vivo).
Para comparar, os partidos de 2022 são agrupados nas federações/partidos de 2026. Fusões (de memória, não verificadas):
PSC->PODE, PTB+PATRIOTA->PRD, PROS->SOLIDARIEDADE. Comparação ELEIÇÃO x ELEIÇÃO (não é a composição durante o mandato)."""
import pandas as pd
e22 = pd.read_csv("camara_2022_eleitos.csv"); c26 = pd.read_csv("camara_2026_cadeiras.csv")
MAPA22 = {"PT": "PCDOB / PT / PV", "PC do B": "PCDOB / PT / PV", "PV": "PCDOB / PT / PV", "UNIÃO": "PP / UNIÃO", "PP": "PP / UNIÃO",
          "PSDB": "CIDADANIA / PSDB", "CIDADANIA": "CIDADANIA / PSDB", "PSOL": "PSOL / REDE", "REDE": "PSOL / REDE",
          "PSC": "PODE", "PTB": "PRD / SOLIDARIEDADE", "PATRIOTA": "PRD / SOLIDARIEDADE", "PROS": "PRD / SOLIDARIEDADE", "SOLIDARIEDADE": "PRD / SOLIDARIEDADE"}
e22["agr"] = e22.SG_PARTIDO.map(lambda p: MAPA22.get(p, p))
raw = e22.SG_PARTIDO.value_counts()
t22 = e22.agr.value_counts().rename("c2022")
T = c26.set_index("agr")[["vag", "grupo"]].rename(columns={"vag": "c2026"}).join(t22, how="outer")
T["c2022"] = T.c2022.fillna(0).astype(int); T["c2026"] = T.c2026.fillna(0).astype(int)
T["grupo"] = T.grupo.fillna("?"); T["dif"] = T.c2026 - T.c2022
T = T.sort_values("c2026", ascending=False); T.to_csv("camara_comparativo_2022_2026.csv")
print(T.to_string())
print("\nTotais:", T.c2022.sum(), T.c2026.sum())
G = T.groupby("grupo")[["c2022", "c2026", "dif"]].sum(); print(G.to_string())
dir22 = G.loc["PL", "c2022"] + G.loc["Direita (outros)", "c2022"]; dir26 = G.loc["PL", "c2026"] + G.loc["Direita (outros)", "c2026"]
print(f"\nDireita total: 2022 {dir22} -> 2026 {dir26} ({dir26-dir22:+d})")
print("Sem mapeamento (grupo ?):", T[T.grupo == "?"].index.tolist())
print("\n2022 bruto (partido na eleição):", raw.to_dict())
