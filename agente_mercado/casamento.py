"""Associa um item da lista aos produtos de uma loja."""
import re
import unicodedata

from .modelos import ItemLista, Produto


def normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return sem_acento.lower()


def _radical(token: str) -> str:
    return token[:-1] if len(token) > 3 and token.endswith("s") else token


def tokens(texto: str) -> set:
    return {_radical(t) for t in re.findall(r"[a-z0-9]+", normalizar(texto))}


def casa(item: ItemLista, produto: Produto) -> bool:
    """Todos os termos do item devem aparecer no produto e nenhum termo excluído."""
    alvo = tokens(produto.nome)
    if not tokens(item.nome) <= alvo:
        return False
    if any(_radical(normalizar(x)) in alvo for x in item.excluir):
        return False
    # Pedido em peso/volume só casa com a mesma grandeza; pedido em "un" aceita qualquer
    # embalagem e é tratado como número de pacotes.
    return item.unidade == "un" or item.unidade == produto.unidade
