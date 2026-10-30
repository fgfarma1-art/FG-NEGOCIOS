"""Corta as seções de 2022 em cada UF no horário do PRÓPRIO arquivo de 2026 daquela UF.
(Cada UF tem hora de geração um pouco diferente; usar um único horário para a região distorce a comparação.)"""
from datetime import datetime
import pandas as pd

def secoes_ate(s22, linhas):
    """s22: seções 2022 (coluna uf, recebido). linhas: DataFrame com colunas uf e gerado_em (dd/mm/aaaa hh:mm:ss), só UFs."""
    partes = []
    for r in linhas.itertuples():
        t = datetime.strptime(r.gerado_em, "%d/%m/%Y %H:%M:%S")
        partes.append(s22[(s22.uf == r.uf) & (s22.recebido <= datetime(2022, 10, 2, t.hour, t.minute, t.second))])
    return pd.concat(partes)
