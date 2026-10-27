// node tests/test_extensao.js  — confere o núcleo JS contra os dados de exemplo e o Python
const assert = require('assert');
const fs = require('fs');
const N = require('../extensao/ifood-carrinho.user.js');

const dados = JSON.parse(fs.readFileSync(__dirname + '/../dados/ofertas_exemplo.json', 'utf8'));
const lojas = dados.lojas.map((l) => ({ id: l.id, nome: l.nome, taxa: l.taxa_entrega, minimo: l.pedido_minimo,
  gratis: l.frete_gratis_acima || 0, cupom: l.cupom, url: '#',
  produtos: l.produtos.map((p) => { const [qtd, un] = N.extrairMedida(p.nome) || [1, 'un']; return { nome: p.nome, preco: p.preco, qtd, un, loja: l.id }; }) }));

const itens = N.lerLista(fs.readFileSync(__dirname + '/../dados/lista_exemplo.txt', 'utf8'));
const r = N.resolver(itens, lojas);
assert.strictEqual(r.plano.total, 183.78);
assert.deepStrictEqual(r.plano.pedidos.map((p) => p.loja.id).sort(), ['alfa', 'beta']);
assert.strictEqual(r.naoEncontrados.length, 0);

// formatos livres de lista
const l = N.lerLista('arroz 5kg\n5 kg feijão\n12 ovos\narroz -integral | 5 kg\nleite integral 12 L');
assert.deepStrictEqual(l.map((i) => [i.nome.trim(), i.quantidade, i.unidade]),
  [['arroz', 5000, 'g'], ['feijão', 5000, 'g'], ['ovos', 12, 'un'], ['arroz', 5000, 'g'], ['leite integral', 12000, 'ml']]);
assert.deepStrictEqual(l[3].excluir, ['integral']);
console.log('extensao ok — total', r.plano.total);
