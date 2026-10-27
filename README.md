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

### Como decide
Para cada combinação de até `--max-lojas` lojas, atribui cada item à opção mais barata e refina por busca local
considerando frete, mínimo e cupom. Uma loja extra só entra se economizar ao menos `--ganho-minimo` reais.
Depois sugere: frete grátis/cupom a poucos reais de distância, embalagens maiores com preço por kg bem menor
(só para itens não perecíveis) e lojas mais baratas por unidade que não compensaram no total.
