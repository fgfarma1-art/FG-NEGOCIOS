# FG-NEGOCIOS
CONSTANTE APRENDIZADO

## Agente de compras de mercado

Monta o carrinho mais barato a partir da sua lista e dos preços de várias lojas (ex.: iFood Mercado).
Considera preço por kg/L, embalagens maiores, taxa de entrega, pedido mínimo, frete grátis e cupons,
e decide se vale dividir a compra em mais de uma loja.

```bash
python -m agente_mercado --ofertas dados/ofertas_exemplo.json --lista dados/lista_exemplo.txt
python -m agente_mercado --ofertas dados/ofertas.csv --lista minha_lista.txt --max-lojas 2 --ganho-minimo 8 --json carrinho.json
python -m unittest discover -s tests -t .
```

### Jeito rápido: painel 🛒 dentro do iFood (sem Python)
1. Instale a extensão **Tampermonkey** no Chrome → "Criar novo script" → cole todo o conteúdo de
   `extensao/ifood-carrinho.user.js` e salve. (Sem Tampermonkey: cole o arquivo no Console, F12, a cada página.)
2. Abra o iFood: aparece o botão 🛒 no canto da tela. Escreva a lista uma vez (`arroz 5kg`, `leite integral 12 L`,
   `ovos 12`, `arroz -integral 5kg`); ela fica salva.
3. Abra cada mercado e clique **Coletar esta loja** (ele rola a página sozinho e lê os preços). Confira entrega,
   mínimo e frete grátis, que podem ser editados na própria caixinha da loja.
4. Clique **Montar carrinho**: mostra quanto comprar em cada loja, total, link para abrir a loja e sugestões.

Tudo roda no seu navegador; nada é enviado para fora. Testes: `node tests/test_extensao.js` (paridade com o Python)
e `node tests/test_painel.js` (painel completo no Chromium com lojas simuladas). **Ainda não foi validado contra o HTML
real do iFood**: se o botão disser "Não achei produtos", o seletor precisa de ajuste com um exemplo real.

### Alternativa: Python + CSV
(Coleta pelo console, para usar o agente de linha de comando.)

### Como obter os preços do iFood
O iFood não tem API pública para consumidores e raspagem automática viola os termos de uso, então a coleta
é feita por você, com a sua sessão:

1. Abra a loja no Chrome, role até o fim da página (para carregar todos os produtos).
2. F12 → Console → cole `coletor/ifood_console.js` → Enter. O CSV é copiado para a área de transferência.
3. Cole em `dados/ofertas.csv`. Repita para cada loja (cabeçalhos repetidos são ignorados).
4. Preencha à mão o que a página não mostra: `pedido_minimo`, `frete_gratis_acima`, cupom
   (`cupom_codigo,cupom_tipo,cupom_valor,cupom_minimo,cupom_teto`).

O coletor usa heurísticas e **não foi testado contra a página real**; confira a saída.
Preços são válidos só para o seu endereço e horário.

### Lista de compras
Uma linha por item: `arroz branco | 5 kg`. Use `-palavra` para excluir (`arroz -integral | 5 kg`).
Pedido em `un` de um produto vendido em peso/volume conta como número de embalagens.
Formato JSON também é aceito (`item`, `quantidade`, `unidade`, `excluir`, `perecivel`).

### Histórico e itens recorrentes
Com `--historico dados/historico.json` o agente grava cada execução (itens comprados e preços vistos) e passa a:
- **avisar sobre preço**: "menor preço que já vi" ou "X% acima da média" para os produtos do carrinho (precisa de 2+ execuções anteriores);
- **lembrar itens recorrentes**: o que você compra a cada ~N dias e já está na hora de repor. `--incluir-recorrentes`
  adiciona esses itens à lista automaticamente; `--nao-registrar` usa o histórico sem gravar a execução.

### Como decide
Para cada combinação de até `--max-lojas` lojas, atribui cada item à opção mais barata e refina por busca local
considerando frete, mínimo e cupom. Uma loja extra só entra se economizar ao menos `--ganho-minimo` reais.
Depois sugere: frete grátis/cupom a poucos reais de distância, embalagens maiores com preço por kg bem menor
(só para itens não perecíveis) e lojas mais baratas por unidade que não compensaram no total.
