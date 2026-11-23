---
name: registrar-decisao
description: Use quando o consultor decide algo, quando uma tarefa conflita com uma decisão registrada e quando você resolve o que o consultor deixou em aberto. Mantém o registro de decisões do projeto, que nunca é apagado.
metadata:
  origem: harness-de-entregaveis
---

# Registrar uma decisão

O registro é `entregaveis/_projeto/decisoes.md`. Se o projeto já mantém
decisões em outro lugar, use esse lugar.

1. Antes de registrar, procure uma decisão anterior sobre o mesmo
   assunto.
2. Decisão do consultor: uma linha nova com o próximo id `D-nnn`, a data, a
   decisão com as palavras dele, o motivo e o estado `Vigente`.
3. Decisão sua, sobre o que o consultor deixou em aberto: a mesma linha, com
   o estado `Vigente (assumida)` e o motivo da escolha. Ela entra no
   próximo relatório para o consultor confirmar ou trocar.
4. Decisão que troca outra: a antiga passa a `Substituída por D-nnn`.
   Nenhuma linha é apagada.
5. Conflito: se uma tarefa contraria uma decisão vigente ou uma
   instrução anterior do consultor, pare essa parte e pergunte, com as opções
   e a que você recomenda. Não escolha um lado em silêncio.
6. Uma decisão que muda o contrato, o tipo de trabalho ou a decisão que
   o projeto precisa provocar abre uma fase nova: aplique
   `evoluir-projeto`. Mudança de entregáveis, de prazo ou de audiência
   dentro da mesma fase é escopo, e fica aqui.
7. Depois de uma decisão nova, mude o que dependia dela: o briefing, a
   storyline, as páginas. Uma mudança na grande ideia ou na sequência de
   títulos pede nova aprovação da storyline.
