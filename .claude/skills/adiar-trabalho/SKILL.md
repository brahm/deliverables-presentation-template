---
name: adiar-trabalho
description: Use quando algo que foi pedido não será feito agora, quando um item muda de entregável ou de prazo e quando uma lacuna de dado impede terminar uma página. Registra o item para que nada suma em silêncio.
metadata:
  origem: harness-de-entregaveis
---

# Adiar um trabalho

1. Acrescente uma linha a `entregaveis/_projeto/adiados.tsv` com o
   próximo id `B-nnn`, o item, o motivo, para quando ele fica e o estado
   `aberto`.
2. Se o item depende de um material, cite o id do intake (`M-nnn`).
3. Deixe a lacuna visível no entregável: "A confirmar (M-nnn)" na
   página, ou a linha de pendência em `revisao.md`.
4. Diga no relatório, com todas as letras: qual item, por que e para
   quando.
5. Quando o item for feito, mude o estado para `feito`. A linha fica.
6. Antes de marcar um entregável como `entregue`, cada item aberto que é
   dele foi feito ou foi movido com o dono avisado.
