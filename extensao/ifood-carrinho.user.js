// ==UserScript==
// @name         Carrinho Barato - iFood Mercados
// @namespace    fg-negocios
// @version      1.0
// @description  Painel que coleta preços das lojas que você abre no iFood e monta o carrinho mais barato.
// @match        https://www.ifood.com.br/*
// @grant        none
// ==/UserScript==

// Tudo roda localmente no seu navegador: nada é enviado para fora.
// Sem Tampermonkey? Cole este arquivo inteiro no Console (F12) de cada página do iFood.

const Nucleo = (() => {
  const UN = { kg: ['g', 1000], g: ['g', 1], l: ['ml', 1000], lt: ['ml', 1000], litro: ['ml', 1000],
    litros: ['ml', 1000], ml: ['ml', 1], un: ['un', 1], und: ['un', 1], unid: ['un', 1], unidade: ['un', 1],
    unidades: ['un', 1], dz: ['un', 12], duzia: ['un', 12] };
  const UN_RE = Object.keys(UN).sort((a, b) => b.length - a.length).join('|');
  const MEDIDA = new RegExp(`(?:(\\d+)\\s*[x×]\\s*)?(\\d+(?:[.,]\\d+)?)\\s*(${UN_RE})\\b`, 'i');
  const CONTEM = /\b(?:c\/|com\s+)\s*(\d+)\b/i;
  const PEN = 10000;

  const normalizar = (t) => t.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const num = (t) => parseFloat(String(t).replace(/\./g, '').replace(',', '.'));
  const r2 = (v) => Math.round(v * 100) / 100;
  const brl = (v) => 'R$ ' + v.toFixed(2).replace('.', ',').replace(/\B(?=(\d{3})+(?!\d))/g, '.');

  function converter(valor, unidade) {
    const u = UN[normalizar(unidade).trim()];
    if (!u) throw new Error('unidade desconhecida: ' + unidade);
    return [valor * u[1], u[0]];
  }
  function extrairMedida(texto) {
    texto = normalizar(texto);
    let m = texto.match(MEDIDA);
    if (m) { const [q, b] = converter(parseFloat(m[2].replace(',', '.')), m[3]); return [q * (m[1] ? +m[1] : 1), b]; }
    m = texto.match(CONTEM);
    return m ? [+m[1], 'un'] : null;
  }
  const radical = (t) => (t.length > 3 && t.endsWith('s') ? t.slice(0, -1) : t);
  const tokens = (t) => new Set((normalizar(t).match(/[a-z0-9]+/g) || []).map(radical));

  function casa(item, p) {
    const alvo = tokens(p.nome);
    for (const t of tokens(item.nome)) if (!alvo.has(t)) return false;
    if ((item.excluir || []).some((x) => alvo.has(radical(normalizar(x))))) return false;
    return item.unidade === 'un' || item.unidade === p.un;
  }
  const precoUnit = (p) => p.preco / p.qtd * (p.un === 'un' ? 1 : 1000);
  const rotulo = (p) => ({ g: 'kg', ml: 'L', un: 'un' })[p.un];

  // "arroz branco | 5 kg", "arroz 5kg", "5 kg arroz", "12 ovos", "arroz -integral 5kg"
  function lerLista(texto) {
    const itens = [];
    for (const bruta of texto.split('\n')) {
      let linha = bruta.split('#')[0].trim();
      if (!linha) continue;
      let nome = linha, q = 1, un = 'un';
      const pipe = linha.match(/^(.*?)[|;]\s*(\d+(?:[.,]\d+)?)\s*([a-zA-Zç]*)\s*$/);
      if (pipe) { nome = pipe[1]; [q, un] = converter(parseFloat(pipe[2].replace(',', '.')), pipe[3] || 'un'); }
      else {
        const med = extrairMedida(linha);
        if (med) {
          [q, un] = med;
          const m = normalizar(linha).match(MEDIDA) || normalizar(linha).match(CONTEM); // mesmo tamanho do original
          nome = linha.slice(0, m.index) + ' ' + linha.slice(m.index + m[0].length);
        }
        else { const n = linha.match(/^(\d+)\s+(.*)$/) || linha.match(/^(.*?)\s+(\d+)$/); if (n) { const lead = /^\d/.test(linha); q = +(lead ? n[1] : n[2]); nome = lead ? n[2] : n[1]; } }
      }
      const termos = nome.trim().split(/\s+/);
      itens.push({ nome: termos.filter((t) => !t.startsWith('-')).join(' '), quantidade: q, unidade: un,
        excluir: termos.filter((t) => t.startsWith('-') && t.length > 1).map((t) => t.slice(1)) });
    }
    return itens;
  }

  function cobrar(l, sub) {
    const c = l.cupom;
    let desc = 0;
    if (c && sub + 1e-9 >= (c.minimo || 0)) {
      desc = c.tipo === 'percent' ? sub * c.valor / 100 : c.valor;
      if (c.teto != null) desc = Math.min(desc, c.teto);
      desc = Math.min(desc, sub);
    }
    const gratis = l.gratis > 0 && sub + 1e-9 >= l.gratis;
    const taxa = gratis ? 0 : (l.taxa || 0);
    return [desc, taxa, sub - desc + taxa];
  }

  function escolha(i, item, p) {
    let pacotes, sobra;
    if (item.unidade === 'un' && p.un !== 'un') { pacotes = Math.ceil(item.quantidade - 1e-9); sobra = 0; }
    else { pacotes = Math.ceil(item.quantidade / p.qtd - 1e-9); sobra = pacotes * p.qtd - item.quantidade; }
    return { item: i, produto: p, pacotes, custo: r2(pacotes * p.preco), sobra };
  }
  const menor = (a, b) => (a.custo - b.custo) || (a.sobra - b.sobra) || (precoUnit(a.produto) - precoUnit(b.produto));

  function* combinacoes(arr, k, ini = 0, atual = []) {
    if (atual.length === k) { yield atual.slice(); return; }
    for (let i = ini; i < arr.length; i++) { atual.push(arr[i]); yield* combinacoes(arr, k, i + 1, atual); atual.pop(); }
  }

  function resolver(itens, lojas, { maxLojas = 3, ganhoMinimo = 5 } = {}) {
    const L = Object.fromEntries(lojas.map((l) => [l.id, l]));
    const cand = itens.map((it, i) => {
      const m = {};
      for (const l of lojas) for (const p of l.produtos) if (casa(it, p)) (m[l.id] = m[l.id] || []).push(escolha(i, it, p));
      return m;
    });
    const op = cand.map((m) => Object.fromEntries(Object.entries(m).map(([s, cs]) => [s, cs.reduce((a, b) => (menor(b, a) < 0 ? b : a))])));
    const cobertos = op.map((o, i) => (Object.keys(o).length ? i : -1)).filter((i) => i >= 0);
    const naoEncontrados = op.map((o, i) => (Object.keys(o).length ? -1 : i)).filter((i) => i >= 0);

    const chave = (atrib) => {
      const g = {};
      for (const [i, s] of Object.entries(atrib)) g[s] = (g[s] || 0) + op[i][s].custo;
      let t = 0;
      for (const [s, sub] of Object.entries(g)) {
        if (sub + 1e-9 < (L[s].minimo || 0)) t += PEN + (L[s].minimo - sub) * 100;
        t += cobrar(L[s], sub)[2];
      }
      return t;
    };
    const plano = (atrib) => {
      const g = {};
      for (const [i, s] of Object.entries(atrib)) (g[s] = g[s] || []).push(op[i][s]);
      const pedidos = Object.entries(g).map(([s, escs]) => {
        const sub = r2(escs.reduce((a, e) => a + e.custo, 0));
        const [desconto, taxa, total] = cobrar(L[s], sub);
        return { loja: L[s], escolhas: escs.sort((a, b) => a.item - b.item), subtotal: sub, desconto, taxa, total: r2(total) };
      }).sort((a, b) => b.total - a.total);
      return { pedidos, total: r2(pedidos.reduce((a, p) => a + p.total, 0)),
        valido: pedidos.every((p) => p.subtotal + 1e-9 >= (L[p.loja.id].minimo || 0)) };
    };
    const melhorar = (atrib, combo) => {
      let k = chave(atrib), mudou = true;
      while (mudou) {
        mudou = false;
        for (const i of cobertos) {
          const atual = atrib[i]; let melhor = null;
          for (const s of combo) {
            if (s === atual || !(s in op[i])) continue;
            atrib[i] = s; const c = chave(atrib);
            if (c < k - 1e-9) { k = c; melhor = s; }
          }
          atrib[i] = melhor || atual; if (melhor) mudou = true;
        }
      }
      return [k, atrib];
    };
    const resolverCombo = (combo) => {
      if (!cobertos.every((i) => combo.some((s) => s in op[i]))) return null;
      const inicios = [Object.fromEntries(cobertos.map((i) => [i,
        combo.filter((s) => s in op[i]).reduce((a, b) => (op[i][b].custo < op[i][a].custo ? b : a))]))];
      for (const s of combo) if (cobertos.every((i) => s in op[i])) inicios.push(Object.fromEntries(cobertos.map((i) => [i, s])));
      return inicios.map((a) => melhorar({ ...a }, combo)).reduce((a, b) => (b[0] < a[0] ? b : a));
    };

    const ids = [...new Set(op.flatMap((o) => Object.keys(o)))].sort();
    const porK = {};
    for (let k = 1; k <= Math.min(maxLojas, ids.length); k++) {
      let achado = null;
      for (const combo of combinacoes(ids, k)) { const r = resolverCombo(combo); if (r && (!achado || r[0] < achado[0])) achado = r; }
      if (achado) porK[k] = plano(achado[1]);
    }
    const ks = Object.keys(porK).map(Number).sort((a, b) => a - b);
    if (!ks.length) return { plano: { pedidos: [], total: 0, valido: true }, porK, naoEncontrados, cand, itens, L, ganhoMinimo };
    let esc = ks[0];
    for (const k of ks.slice(1)) {
      const ref = porK[esc];
      if ((porK[k].valido && !ref.valido) || (porK[k].valido === ref.valido && porK[k].total <= ref.total - ganhoMinimo)) esc = k;
    }
    return { plano: porK[esc], porK, naoEncontrados, cand, itens, L, ganhoMinimo };
  }

  function sugerir(res) {
    const s = [], { plano, porK, itens } = res;
    if (!plano.valido) s.push('⚠️ Algum pedido ficou abaixo do mínimo da loja. Aumente a lista ou use menos lojas.');
    if (plano.pedidos.length > 1 && porK[1] && porK[1].valido)
      s.push(`Dividir em ${plano.pedidos.length} lojas economiza ${brl(porK[1].total - plano.total)} frente a comprar tudo em ${porK[1].pedidos[0].loja.nome} (${brl(porK[1].total)}).`);
    for (const p of plano.pedidos) {
      const g = p.loja.gratis;
      if (g > 0 && p.taxa > 0 && g - p.subtotal <= g * 0.35)
        s.push(`${p.loja.nome}: faltam ${brl(g - p.subtotal)} para frete grátis (entrega ${brl(p.taxa)}). Se for comprar mais algo, complete aqui.`);
    }
    const noPlano = new Set(plano.pedidos.map((p) => p.loja.id));
    for (const p of plano.pedidos) for (const e of p.escolhas) {
      const item = itens[e.item];
      if (item.unidade === 'un' && e.produto.un !== 'un') continue;
      const pu = precoUnit(e.produto);
      let melhor = null;
      for (const [sid, cs] of Object.entries(res.cand[e.item])) if (!noPlano.has(sid)) for (const a of cs)
        if (precoUnit(a.produto) <= pu * 0.9 && (!melhor || precoUnit(a.produto) < precoUnit(melhor.produto))) melhor = a;
      if (melhor) s.push(`${item.nome}: em ${res.L[melhor.produto.loja].nome} sai ${brl(precoUnit(melhor.produto))}/${rotulo(melhor.produto)} (vs ${brl(pu)}), mas entrega/mínimo não compensou.`);
    }
    for (const i of res.naoEncontrados) s.push(`Não encontrei "${itens[i].nome}" nas lojas coletadas — abra mais lojas ou confira o nome.`);
    return s;
  }

  return { extrairMedida, lerLista, resolver, sugerir, cobrar, casa, brl, num, precoUnit, rotulo, normalizar };
})();

if (typeof module !== 'undefined') module.exports = Nucleo;
else if (typeof document !== 'undefined') (() => {
  const { brl, num, extrairMedida, lerLista, resolver, sugerir, precoUnit, rotulo } = Nucleo;
  const K = 'agente_mercado_v1';
  const estado = (() => { try { return JSON.parse(localStorage.getItem(K)) || { lista: '', lojas: {} }; } catch { return { lista: '', lojas: {} }; } })();
  const salvar = () => { try { localStorage.setItem(K, JSON.stringify(estado)); } catch {} };
  if (document.getElementById('agente-mercado')) return;

  const PRECO = /R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2})/g;
  const esperar = (ms) => new Promise((r) => setTimeout(r, ms));

  async function rolarTudo(aviso) {
    let ultimo = -1;
    for (let i = 0; i < 60; i++) {
      window.scrollTo(0, document.documentElement.scrollHeight);
      aviso(`Rolando a página… (${i + 1})`);
      await esperar(700);
      const h = document.documentElement.scrollHeight;
      if (h === ultimo) break;
      ultimo = h;
    }
    window.scrollTo(0, 0);
  }

  function coletar() {
    const corpo = document.body.innerText;
    const nome = (document.querySelector('h1')?.innerText || document.title.split('|')[0]).trim();
    const taxaT = corpo.match(/entrega[^\n]{0,40}?R\$\s*([\d.,]+)/i);
    const minT = corpo.match(/m[ií]nimo[^\n]{0,30}?R\$\s*([\d.,]+)/i);
    const gratT = corpo.match(/gr[aá]tis[^\n]{0,40}?R\$\s*([\d.,]+)/i);
    const vistos = new Set(), produtos = [], chaves = new Set();
    const folhas = [...document.querySelectorAll('body *')].filter((e) => e.children.length === 0 && /R\$\s*\d/.test(e.textContent));
    for (const folha of folhas) {
      let card = folha;
      for (let i = 0; i < 5 && card.parentElement; i++) {
        card = card.parentElement;
        const txt = card.innerText || '';
        const precos = txt.match(PRECO) || [];
        const nomeP = txt.split('\n').map((s) => s.trim())
          .filter((s) => s.length > 3 && !/R\$/.test(s) && !/^\d+%/.test(s) && !/entrega|frete|m[ií]nimo|taxa|min$/i.test(s))
          .sort((a, b) => b.length - a.length)[0];
        if (nomeP && precos.length >= 1 && precos.length <= 2 && txt.length < 400) {
          if (vistos.has(card)) break;
          vistos.add(card);
          const vals = precos.map((t) => num(t.replace(/R\$\s*/, '')));
          const riscado = [...card.querySelectorAll('*')].some((e) => e.children.length === 0 && /R\$/.test(e.textContent) && getComputedStyle(e).textDecorationLine.includes('line-through'));
          const preco = vals.length === 2 ? (riscado ? Math.min(...vals) : vals[0]) : vals[0];
          const [qtd, un] = extrairMedida(nomeP) || [1, 'un'];
          const k = nomeP + preco;
          if (!chaves.has(k) && preco > 0) { chaves.add(k); produtos.push({ nome: nomeP, preco, qtd, un }); }
          break;
        }
      }
    }
    return { id: location.pathname.split('/').filter(Boolean).slice(0, 4).join('/') || nome, nome, url: location.href,
      taxa: taxaT ? num(taxaT[1]) : 0, minimo: minT ? num(minT[1]) : 0, gratis: gratT ? num(gratT[1]) : 0, produtos };
  }

  // --- interface ---
  const host = document.createElement('div');
  host.id = 'agente-mercado';
  document.body.appendChild(host);
  const sh = host.attachShadow({ mode: 'open' });
  sh.innerHTML = `<style>
    *{box-sizing:border-box;font-family:system-ui,sans-serif}
    #fab{position:fixed;right:16px;bottom:16px;z-index:2147483647;width:52px;height:52px;border-radius:50%;border:0;background:#ea1d2c;color:#fff;font-size:24px;cursor:pointer;box-shadow:0 2px 10px #0006}
    #p{position:fixed;right:16px;bottom:78px;z-index:2147483647;width:min(430px,calc(100vw - 32px));max-height:80vh;overflow:auto;background:#fff;color:#222;border-radius:12px;padding:14px;box-shadow:0 4px 24px #0005;font-size:13px}
    #p[hidden]{display:none} h3{margin:0 0 8px;font-size:15px} textarea{width:100%;height:110px;font-size:13px;padding:6px}
    button.b{background:#ea1d2c;color:#fff;border:0;border-radius:8px;padding:8px 12px;margin:6px 6px 6px 0;cursor:pointer;font-size:13px}
    button.s{background:#eee;color:#222} .loja{border:1px solid #ddd;border-radius:8px;padding:6px 8px;margin:6px 0}
    .loja input{width:62px;padding:2px} .ped{border-left:4px solid #ea1d2c;padding-left:8px;margin:10px 0}
    .sug{background:#fff8e1;border-radius:6px;padding:6px 8px;margin:4px 0} .tot{font-size:16px;font-weight:700;margin:8px 0}
    .st{color:#666;min-height:18px} small{color:#666}
  </style>
  <button id="fab" title="Carrinho Barato">🛒</button>
  <div id="p" hidden>
    <h3>🛒 Carrinho Barato</h3>
    <small>1) escreva a lista · 2) abra cada mercado e clique "Coletar esta loja" · 3) "Montar carrinho"</small>
    <textarea id="lista" placeholder="arroz branco 5kg&#10;feijão carioca 2kg&#10;leite integral 12 L&#10;ovos 12&#10;arroz -integral | 5 kg"></textarea>
    <div><button class="b" id="col">Coletar esta loja</button><button class="b" id="mon">Montar carrinho</button><button class="b s" id="lim">Limpar lojas</button></div>
    <div class="st" id="st"></div><div id="lojas"></div><div id="res"></div>
  </div>`;
  const $ = (id) => sh.getElementById(id);
  const aviso = (t) => { $('st').textContent = t; };
  $('lista').value = estado.lista;
  $('fab').onclick = () => { $('p').hidden = !$('p').hidden; };
  $('lista').oninput = () => { estado.lista = $('lista').value; salvar(); };

  function desenharLojas() {
    const ls = Object.values(estado.lojas);
    $('lojas').innerHTML = ls.length ? ls.map((l) => `<div class="loja" data-id="${l.id.replace(/"/g, '')}"><b>${l.nome}</b> — ${l.produtos.length} produtos
      <button class="b s" data-rm="1" style="padding:2px 8px">x</button><br>
      <small>entrega R$ <input data-f="taxa" value="${l.taxa}"> mínimo R$ <input data-f="minimo" value="${l.minimo}"> frete grátis ≥ R$ <input data-f="gratis" value="${l.gratis}"></small></div>`).join('')
      : '<small>Nenhuma loja coletada ainda.</small>';
    sh.querySelectorAll('.loja').forEach((el) => {
      const l = estado.lojas[el.dataset.id];
      el.querySelector('[data-rm]').onclick = () => { delete estado.lojas[l.id]; salvar(); desenharLojas(); };
      el.querySelectorAll('input').forEach((inp) => { inp.onchange = () => { l[inp.dataset.f] = num(String(inp.value).includes(',') ? inp.value : String(inp.value).replace('.', ',')) || 0; salvar(); }; });
    });
  }

  $('col').onclick = async () => {
    $('col').disabled = true;
    try {
      await rolarTudo(aviso);
      const l = coletar();
      if (!l.produtos.length) aviso('Não achei produtos nesta página. Abra a página de uma loja (com a lista de produtos) e tente de novo.');
      else { estado.lojas[l.id] = l; salvar(); desenharLojas(); aviso(`✔ ${l.produtos.length} produtos coletados de ${l.nome}. Confira entrega/mínimo abaixo.`); }
    } catch (e) { aviso('Erro: ' + e.message); }
    $('col').disabled = false;
  };

  // --- montar a sacola no iFood (só adiciona; nunca finaliza nem paga) ---
  const lojaIdAtual = () => location.pathname.split('/').filter(Boolean).slice(0, 4).join('/');
  const vis = (e) => !!(e.offsetParent || e.getClientRects().length);
  const PROIBIDO = /finalizar|pagar|pagamento|checkout|concluir|fazer pedido|confirmar|cupom|trocar|remover|excluir|limpar|esvaziar/i;
  const rot = (b) => `${b.getAttribute('aria-label') || ''} ${b.innerText || b.textContent || ''}`;
  const botoes = (raiz) => [...raiz.querySelectorAll('button,[role=button]')].filter((b) => vis(b) && !PROIBIDO.test(rot(b)));
  const MAIS = /aument|mais |increase|^\s*\+\s*$/i;
  let cancelar = false;

  function achaCartao(nome) {
    const alvo = Nucleo.normalizar(nome).trim();
    const folhas = [...document.querySelectorAll('body *')].filter((e) => !host.contains(e) && e.children.length === 0 && Nucleo.normalizar(e.textContent).trim() === alvo);
    for (const f of folhas) {
      let c = f;
      for (let i = 0; i < 5 && c.parentElement; i++) {
        c = c.parentElement;
        const t = c.innerText || '';
        if ((t.match(PRECO) || []).length >= 1 && t.length < 400) return c;
      }
    }
    return null;
  }

  async function adicionar(nome, pacotes) {
    const card = achaCartao(nome);
    if (!card) return 'produto não encontrado na tela';
    card.scrollIntoView({ block: 'center' });
    await esperar(300);
    const direto = botoes(card).find((b) => /adicionar|^\s*add\b|^\s*\+\s*$/i.test(rot(b)));
    if (direto) direto.click(); else card.click();
    await esperar(900);
    const dlg = [...document.querySelectorAll('[role=dialog],[aria-modal=true]')].find((d) => vis(d) && !host.contains(d));
    if (!dlg) {
      if (!direto) return 'não consegui abrir o produto';
      for (let i = 1; i < pacotes; i++) {
        const mais = botoes(card).find((b) => MAIS.test(rot(b))) || direto;
        mais.click(); await esperar(500);
      }
      return 'ok';
    }
    for (let i = 1; i < pacotes; i++) {
      const mais = botoes(dlg).find((b) => MAIS.test(rot(b)));
      if (!mais) return 'não achei o botão de quantidade';
      mais.click(); await esperar(300);
    }
    const add = botoes(dlg).find((b) => /adicionar|^\s*add\b/i.test(rot(b)));
    if (!add) return 'não achei o botão "Adicionar"';
    add.click(); await esperar(1000);
    return 'ok';
  }

  async function preencherSacola(ped, el) {
    cancelar = false;
    for (const it of ped.itens) {
      if (cancelar) { it.status = 'cancelado'; continue; }
      if (it.status === 'ok') continue;
      aviso(`Adicionando ${it.pacotes}x ${it.nome}…`);
      try { it.status = await adicionar(it.nome, it.pacotes); } catch (e) { it.status = 'erro: ' + e.message; }
      salvar(); desenharResultado();
    }
    const falhas = ped.itens.filter((i) => i.status !== 'ok').length;
    aviso(falhas ? `${falhas} item(ns) não foram adicionados — adicione à mão (marcados em vermelho).`
      : '✔ Itens adicionados. Confira a sacola e finalize o pedido no iFood.');
  }

  function desenharResultado() {
    const r = estado.resultado;
    if (!r) { $('res').innerHTML = ''; return; }
    const aqui = lojaIdAtual();
    $('res').innerHTML = r.pedidos.map((p, n) => `<div class="ped"><b>${p.nome}</b> <a href="${p.url}" target="_blank">abrir loja</a><br>
      ${p.itens.map((e) => `${e.status === 'ok' ? '✅' : e.status ? '❌' : '▫️'} ${e.pacotes}x ${e.nome} — ${brl(e.custo)} <small>(${brl(e.pu)}/${e.rot})${e.status && e.status !== 'ok' ? ' — ' + e.status : ''}</small>`).join('<br>')}
      <br><small>subtotal ${brl(p.subtotal)} · entrega ${p.taxa ? brl(p.taxa) : 'grátis'}${p.desconto ? ' · cupom -' + brl(p.desconto) : ''}</small><br><b>${brl(p.total)}</b><br>
      ${p.id === aqui ? `<button class="b" data-add="${n}">Adicionar à sacola do iFood</button><button class="b s" data-stop="1">Parar</button>`
        : '<small>Abra esta loja para adicionar os itens.</small>'}</div>`).join('') +
      `<div class="tot">Total: ${brl(r.total)}</div>` + r.dicas.map((d) => `<div class="sug">${d}</div>`).join('') +
      '<small>Só adiciono à sacola. Finalizar e pagar é com você.</small>';
    sh.querySelectorAll('[data-add]').forEach((b) => { b.onclick = () => preencherSacola(r.pedidos[+b.dataset.add]); });
    sh.querySelectorAll('[data-stop]').forEach((b) => { b.onclick = () => { cancelar = true; }; });
  }

  $('mon').onclick = () => {
    const itens = lerLista($('lista').value), lojas = Object.values(estado.lojas);
    if (!itens.length || !lojas.length) { aviso('Preencha a lista e colete pelo menos uma loja.'); return; }
    const res = resolver(itens, lojas);
    estado.resultado = {
      total: res.plano.total, dicas: sugerir(res),
      pedidos: res.plano.pedidos.map((p) => ({ id: p.loja.id, nome: p.loja.nome, url: p.loja.url, subtotal: p.subtotal,
        taxa: p.taxa, desconto: p.desconto, total: p.total,
        itens: p.escolhas.map((e) => ({ nome: e.produto.nome, pacotes: e.pacotes, custo: e.custo, pu: precoUnit(e.produto), rot: rotulo(e.produto) })) })),
    };
    salvar(); desenharResultado(); aviso('');
  };
  $('lim').onclick = () => { estado.lojas = {}; estado.resultado = null; salvar(); desenharLojas(); desenharResultado(); };
  desenharLojas();
  desenharResultado();
  if (estado.resultado && estado.resultado.pedidos.some((p) => p.id === lojaIdAtual())) { $('p').hidden = false; aviso('Pedido pendente nesta loja: clique em "Adicionar à sacola do iFood".'); }
})();
