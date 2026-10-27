import tempfile
import unittest
from datetime import date

from agente_mercado.carregar import carregar_lista, carregar_ofertas
from agente_mercado import historico
from agente_mercado.modelos import Cupom, ItemLista, Loja, Produto
from agente_mercado.otimizador import Otimizador
from agente_mercado.unidades import extrair_medida


def prod(nome, preco, loja):
    q, u = extrair_medida(nome)
    return Produto(nome, preco, q, u, loja)


class Unidades(unittest.TestCase):
    def test_medidas(self):
        self.assertEqual(extrair_medida("Arroz 5kg"), (5000, "g"))
        self.assertEqual(extrair_medida("Refri 6x350ml"), (2100, "ml"))
        self.assertEqual(extrair_medida("Ovos c/12"), (12, "un"))
        self.assertEqual(extrair_medida("Leite 1,5L"), (1500, "ml"))


class Otimizacao(unittest.TestCase):
    def test_frete_e_divisao(self):
        a = Loja("a", "A", 10, produtos=[prod("Arroz 5kg", 20, "a"), prod("Feijão 1kg", 10, "a")])
        b = Loja("b", "B", 10, produtos=[prod("Arroz 5kg", 19, "b"), prod("Feijão 1kg", 12, "b")])
        itens = [ItemLista("arroz", 5000, "g"), ItemLista("feijao", 1000, "g")]
        r = Otimizador(itens, [a, b], ganho_minimo=5).resolver()
        self.assertEqual(len(r.plano.pedidos), 1)  # dividir não compensa por causa de 2 fretes
        self.assertEqual(r.plano.total, 40.0)

    def test_pedido_minimo_invalida_loja(self):
        a = Loja("a", "A", 0, pedido_minimo=50, produtos=[prod("Arroz 1kg", 5, "a")])
        b = Loja("b", "B", 0, produtos=[prod("Arroz 1kg", 6, "b")])
        r = Otimizador([ItemLista("arroz", 1000, "g")], [a, b]).resolver()
        self.assertEqual(r.plano.pedidos[0].loja.id, "b")

    def test_cupom_e_frete_gratis(self):
        a = Loja("a", "A", 8, frete_gratis_acima=50, cupom=Cupom("X", "percent", 10, 40),
                 produtos=[prod("Arroz 5kg", 60, "a")])
        r = Otimizador([ItemLista("arroz", 5000, "g")], [a]).resolver()
        self.assertEqual(r.plano.total, 54.0)

    def test_exclusao_e_nao_encontrado(self):
        a = Loja("a", "A", 0, produtos=[prod("Arroz Integral 1kg", 5, "a")])
        o = Otimizador([ItemLista("arroz", 1000, "g", ("integral",))], [a])
        self.assertEqual(o.resolver().nao_encontrados, [0])

    def test_embalagem_maior_mais_barata_que_o_necessario(self):
        a = Loja("a", "A", 0, produtos=[prod("Ovos c/12", 30, "a"), prod("Ovos c/30", 25, "a")])
        r = Otimizador([ItemLista("ovos", 12, "un")], [a]).resolver()
        self.assertEqual(r.plano.pedidos[0].escolhas[0].produto.nome, "Ovos c/30")


class Exemplo(unittest.TestCase):
    def test_dados_de_exemplo(self):
        lojas = carregar_ofertas("dados/ofertas_exemplo.json")
        itens = carregar_lista("dados/lista_exemplo.txt")
        r = Otimizador(itens, lojas).resolver()
        self.assertTrue(r.plano.valido)
        self.assertEqual(r.nao_encontrados, [])


class Historico(unittest.TestCase):
    def _rodar(self, caminho, preco, dia, itens):
        loja = Loja("a", "A", 0, produtos=[prod("Arroz 5kg", preco, "a"), prod("Café 500g", 20, "a")])
        o = Otimizador(itens, [loja])
        r = o.resolver()
        h = historico.carregar(caminho)
        avisos = historico.alertas_de_preco(h, o, r)
        historico.registrar(caminho, h, o, r, dia)
        return avisos

    def test_alerta_de_preco_e_recorrentes(self):
        arroz = lambda: [ItemLista("arroz", 5000, "g")]
        with tempfile.TemporaryDirectory() as d:
            c = d + "/h.json"
            self._rodar(c, 25, date(2026, 9, 1), arroz() + [ItemLista("cafe", 500, "g")])
            self._rodar(c, 27, date(2026, 9, 11), arroz() + [ItemLista("cafe", 500, "g")])
            avisos = self._rodar(c, 35, date(2026, 9, 21), arroz())
            self.assertTrue(any("acima da média" in a for a in avisos))
            venc = historico.recorrentes_vencidos(historico.carregar(c), arroz(), date(2026, 10, 1))
            self.assertEqual([r[0].nome for r in venc], ["cafe"])  # a cada 10 dias, já passou
            self.assertEqual(historico.recorrentes_vencidos(historico.carregar(c), arroz(), date(2026, 9, 15)), [])


if __name__ == "__main__":
    unittest.main()
