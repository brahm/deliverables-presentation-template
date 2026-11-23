---
name: preparar-briefing
description: Use quando um entregável novo é pedido (apresentação, proposta, documento, planilha ou treinamento), antes de qualquer storyline ou página. Define a audiência, a transformação, a grande ideia, o pedido, as resistências e o veículo.
metadata:
  origem: harness-de-entregaveis
---

# Preparar o briefing do entregável

O método está em `entregaveis/_harness/metodo/metodo.md`, seções 1 e 2.

1. Crie a pasta com
   `python3 entregaveis/_harness/scripts/preparar.py --entregavel ID --tipo T --veiculo V --formato F --idiomas I`.
   O id é curto, em minúsculas e com hífen.
2. Audiência. Parta de `_projeto/audiencia.md`, escolha o subgrupo que
   decide e escreva o que ele já sabe, o que quer e o que teme.
3. De e para. Em que essa audiência acredita e como age hoje, e o que
   deve mudar depois do material.
4. Grande ideia. Uma frase completa com o ponto de vista e o que está em
   jogo. Se a audiência pudesse responder "e daí?", falta o que está em
   jogo.
5. Chamada para ação. Uma linha por ação, com dono, prazo e papel.
6. Resistências. Liste as lógicas, as emocionais e as práticas, cada uma
   com a resposta que o material vai dar.
7. Veículo e formato, por `metodo/formatos.md`. Se o dono não disse como
   o material será usado, pergunte: projetado ou lido muda tudo.
8. Pergunte ao dono, uma vez, o que você não tem como saber. O resto
   você assume e registra com `registrar-decisao`.
9. Rode `python3 entregaveis/_harness/scripts/validar.py ID --so briefing`.
   Com o briefing completo, mude o `estado` para `storyline`.
10. Mostre ao dono a grande ideia e o pedido em duas linhas antes de
    seguir. As duas escolhas são dele.
