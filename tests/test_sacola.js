// node tests/test_sacola.js — adiciona itens à "sacola" nos dois estilos de página simulada
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), assert = require('assert');
const script = fs.readFileSync(path.join(__dirname, '../extensao/ifood-carrinho.user.js'), 'utf8');
const fx = (f) => fs.readFileSync(path.join(__dirname, 'fixtures', f), 'utf8');
const mk = (id, nome, itens) => ({ id, nome, url: 'https://www.ifood.com.br/' + id, subtotal: 1, taxa: 0, desconto: 0, total: 1,
  itens: itens.map(([n, p]) => ({ nome: n, pacotes: p, custo: 1, pu: 1, rot: 'kg' })) });
const resultado = { total: 2, dicas: [], pedidos: [
  mk('mercado/loja-a', 'Mercado Alfa', [['Feijão Carioca 1kg', 3], ['Leite Integral 1L', 1], ['Produto Inexistente 9kg', 1]]),
  mk('mercado/loja-b', 'Supermercado Beta', [['Arroz Branco Tipo 1 5kg', 2], ['Café Torrado 500g', 1]]) ] };

(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  const erros = []; page.on('pageerror', (e) => erros.push(e.message));
  await page.route('https://www.ifood.com.br/**', (r) =>
    r.fulfill({ contentType: 'text/html', body: r.request().url().includes('loja-a') ? fx('loja_a.html') : fx('loja_b.html') }));

  for (const [id, esperado] of [['loja-a', { 'Feijão Carioca 1kg': 3, 'Leite Integral 1L': 1 }],
                                ['loja-b', { 'Arroz Branco Tipo 1 5kg': 2, 'Café Torrado 500g': 1 }]]) {
    await page.goto('https://www.ifood.com.br/mercado/' + id);
    await page.evaluate((r) => localStorage.setItem('agente_mercado_v1', JSON.stringify({ lista: '', lojas: {}, resultado: r })), resultado);
    await page.evaluate(script);
    await page.locator('#agente-mercado [data-add]').click();   // abre sozinho porque há pedido pendente
    await page.waitForFunction(() => /✔|não foram/.test(document.querySelector('#agente-mercado').shadowRoot.querySelector('#st').textContent), null, { timeout: 40000 });
    const cart = await page.evaluate(() => window.__cart);
    assert.deepStrictEqual(cart, esperado, id + ': ' + JSON.stringify(cart));
    assert.strictEqual(await page.evaluate(() => window.__finalizou), false, 'nunca pode finalizar');
    console.log(id, 'ok', JSON.stringify(cart), '|', await page.locator('#agente-mercado #st').innerText());
  }
  assert.deepStrictEqual(erros, []);
  await browser.close();
  console.log('sacola ok');
})().catch((e) => { console.error(e); process.exit(1); });
