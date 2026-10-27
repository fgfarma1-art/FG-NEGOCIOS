/*
 * Coletor de preços para rodar no CONSOLE do Chrome, na página de uma loja do iFood
 * (F12 > Console > cole este arquivo > Enter). Lê só o que já está na tela, com a sua
 * própria sessão; não envia nada para lugar nenhum.
 *
 * ATENÇÃO: o iFood muda o HTML com frequência e eu não testei contra a página real.
 * O script usa heurísticas (cartões com "R$") e pode precisar de ajuste. Confira o
 * resultado antes de confiar nele.
 *
 * Uso: abra a loja, role até o fim para carregar todos os produtos, rode o script.
 * O CSV vai para a área de transferência; cole no arquivo dados/ofertas.csv.
 * Repita em cada loja (linhas de cabeçalho repetidas são ignoradas pelo agente).
 */
(() => {
  const PRECO = /R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2})/g;
  const num = (t) => parseFloat(t.replace(/\./g, "").replace(",", "."));
  const csv = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;

  const loja = (document.querySelector("h1")?.innerText || document.title.split("|")[0]).trim();
  const taxaTxt = [...document.querySelectorAll("*")]
    .map((e) => e.children.length === 0 ? e.textContent : "")
    .find((t) => /entrega/i.test(t) && /R\$\s*\d/.test(t));
  const taxa = taxaTxt ? num(taxaTxt.match(/R\$\s*([\d.,]+)/)[1]) : "";

  // Menor elemento que contém exatamente um grupo de preço e um texto de nome = cartão.
  const vistos = new Set();
  const linhas = [];
  const folhas = [...document.querySelectorAll("body *")].filter(
    (e) => e.children.length === 0 && /R\$\s*\d/.test(e.textContent)
  );
  for (const folha of folhas) {
    let card = folha;
    for (let i = 0; i < 5 && card.parentElement; i++) {
      card = card.parentElement;
      const precos = card.innerText.match(PRECO) || [];
      const nome = card.innerText.split("\n").map((s) => s.trim())
        .filter((s) => s.length > 3 && !PRECO.test(s) && !/^\d+%/.test(s)).sort((a, b) => b.length - a.length)[0];
      PRECO.lastIndex = 0;
      if (nome && precos.length >= 1 && precos.length <= 2 && card.innerText.length < 400) {
        if (vistos.has(card)) break;
        vistos.add(card);
        const valores = precos.map(num);
        const riscado = [...card.querySelectorAll("*")].some(
          (e) => e.children.length === 0 && /R\$/.test(e.textContent) &&
            getComputedStyle(e).textDecorationLine.includes("line-through"));
        const preco = riscado ? Math.max(...valores) : valores[0];
        const promo = valores.length === 2 ? Math.min(...valores) : "";
        linhas.push([loja, nome, preco, promo, taxa]);
        break;
      }
    }
  }
  const unicos = [...new Map(linhas.map((l) => [l[1] + l[2], l])).values()];
  const cab = "loja,produto,preco,preco_promocional,taxa_entrega";
  const fix = [cab, ...unicos.map((l) => [csv(l[0]), csv(l[1]), l[2], l[3], l[4]].join(","))].join("\n");
  console.log(`${unicos.length} produtos de "${loja}"`, unicos.slice(0, 5));
  try { copy(fix); console.log("CSV copiado para a área de transferência."); }
  catch { console.log(fix); }
})();
