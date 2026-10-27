// node tests/test_painel.js — painel completo no Chromium com lojas simuladas (sem rede)
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), assert = require('assert');
const script = fs.readFileSync(path.join(__dirname, '../extensao/ifood-carrinho.user.js'), 'utf8');
const fx = (f) => fs.readFileSync(path.join(__dirname, 'fixtures', f), 'utf8');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const erros = [];
  page.on('pageerror', (e) => erros.push(e.message));
  await page.route('https://www.ifood.com.br/**', (r) => {
    const u = r.request().url();
    r.fulfill({ contentType: 'text/html', body: u.includes('/loja-a') ? fx('loja_a.html') : fx('loja_b.html') });
  });
  const painel = async () => { await page.evaluate(script); return page; };

  await page.goto('https://www.ifood.com.br/mercado/loja-a');
  await painel();
  await page.locator('#agente-mercado #fab').click();
  await page.locator('#agente-mercado #lista').fill('arroz branco 5kg\nfeijão carioca 2kg\nleite integral 6 L\ncafé torrado 500g');
  await page.locator('#agente-mercado #col').click();
  await page.locator('#agente-mercado .loja').waitFor();

  await page.goto('https://www.ifood.com.br/mercado/loja-b');
  await painel();                       // lista e lojas voltam do localStorage
  await page.locator('#agente-mercado #fab').click();
  await page.locator('#agente-mercado #col').click();
  await page.waitForFunction(() => document.querySelector('#agente-mercado').shadowRoot.querySelectorAll('.loja').length === 2);
  await page.locator('#agente-mercado #mon').click();
  const res = await page.locator('#agente-mercado #res').innerText();
  console.log(res);
  assert(/Total: R\$ \d/.test(res), 'sem total');
  assert(/Mercado Alfa|Supermercado Beta/.test(res));
  assert(/Feij/.test(res) && /Arroz/.test(res) && /Leite/.test(res) && /Café/.test(res));
  const estado = JSON.parse(await page.evaluate(() => localStorage.getItem('agente_mercado_v1')));
  const feijaoA = estado.lojas['mercado/loja-a'].produtos.find((p) => /Feij/.test(p.nome));
  assert.strictEqual(feijaoA.preco, 8.49, 'deveria usar o preço promocional (menor) e não o riscado');
  assert.strictEqual(estado.lojas['mercado/loja-a'].taxa, 7.99);
  assert.deepStrictEqual(erros, []);
  console.log('painel ok');
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
