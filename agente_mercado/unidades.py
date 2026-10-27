"""Leitura de quantidades ("5kg", "12x350ml", "c/12") normalizadas para g, ml ou un."""
import re

# unidade -> (unidade base, fator de conversão)
UNIDADES = {
    "kg": ("g", 1000), "g": ("g", 1),
    "l": ("ml", 1000), "lt": ("ml", 1000), "litro": ("ml", 1000), "litros": ("ml", 1000), "ml": ("ml", 1),
    "un": ("un", 1), "und": ("un", 1), "unid": ("un", 1), "unidade": ("un", 1), "unidades": ("un", 1),
    "dz": ("un", 12), "duzia": ("un", 12), "dúzia": ("un", 12),
}

_UNID_RE = "|".join(sorted((re.escape(u) for u in UNIDADES), key=len, reverse=True))
_MEDIDA = re.compile(
    rf"(?:(\d+)\s*[x×]\s*)?(\d+(?:[.,]\d+)?)\s*({_UNID_RE})\b", re.IGNORECASE
)
_CONTEM = re.compile(r"\b(?:c/|com\s+)\s*(\d+)\b", re.IGNORECASE)


def _num(texto: str) -> float:
    return float(texto.replace(",", "."))


def converter(valor: float, unidade: str):
    """(valor, 'kg') -> (valor_em_base, 'g'). Levanta ValueError se a unidade for desconhecida."""
    chave = unidade.strip().lower()
    if chave not in UNIDADES:
        raise ValueError(f"unidade desconhecida: {unidade!r}")
    base, fator = UNIDADES[chave]
    return valor * fator, base


def extrair_medida(texto: str):
    """Procura a embalagem em um texto. Retorna (quantidade_base, unidade_base) ou None."""
    m = _MEDIDA.search(texto)
    if m:
        mult = int(m.group(1)) if m.group(1) else 1
        qtd, base = converter(_num(m.group(2)), m.group(3))
        return qtd * mult, base
    m = _CONTEM.search(texto)
    if m:
        return float(m.group(1)), "un"
    return None
