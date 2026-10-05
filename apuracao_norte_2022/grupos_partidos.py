# Classificação por partido usada nas análises do Senado (ajustável)
GRUPOS = {
    "PL": "PL",
    **{p: "Direita (outros)" for p in ["NOVO", "PP", "UNIÃO", "REPUBLICANOS", "PRD", "DC", "PRTB", "PMB", "AGIR", "MISSÃO", "DEMOCRATA"]},
    **{p: "Centro" for p in ["PSD", "MDB", "PODE", "PSDB", "CIDADANIA", "AVANTE", "SOLIDARIEDADE", "MOBILIZA", "PATRIOTA"]},
    **{p: "Esquerda" for p in ["PT", "PSB", "PDT", "PSOL", "REDE", "PCDOB", "PC DO B", "PV", "PCB", "PSTU", "PCO", "UP"]},
}

