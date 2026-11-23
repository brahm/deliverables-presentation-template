---
name: registrar-dispensa
description: Use quando o consultor diz que algo não será mais feito, que não depende mais de aprovação, que um risco, uma reunião ou um material deixou de existir, ou que não quer mais um aviso. Registra a decisão com o motivo, cancela o item sem apagar nada e leva o efeito a todos os registros que citam o item.
metadata:
  origem: harness-de-entregaveis
---

# Registrar uma dispensa

Uma dispensa nunca é presumida. Ela vem das palavras do consultor, e o
que deixa de ser feito é registrado como decisão, nunca apagado.

1. Peça o motivo uma vez, em uma linha, se ele não veio.
2. Registre a decisão com `registrar-decisao`, com as palavras do
   consultor.
3. Leve o efeito ao registro do item:

| O consultor informa | O que registrar | O que mais muda |
| --- | --- | --- |
| Uma ação não será mais feita | `rotina.py --dispensar T-nnn --motivo "..."` | Os avisos do item param |
| Um material não é mais necessário | `rotina.py --dispensar M-nnn --motivo "..."` | Feche as lacunas que só esperavam por ele |
| Um entregável ou uma análise sai do plano | Uma linha em `_projeto/adiados.tsv` | Cancele as ações que só serviam a ele |
| O item cancelado estava no contrato | O mesmo, e avise o consultor | A mudança pede o acordo do cliente |
| Algo não depende mais de aprovação | `rotina.py --cobrado ID --resposta dispensada --motivo "..."` | As cobranças param e o que esperava volta às próximas ações |
| A aprovação dispensada era aceite do contrato | O mesmo, e um risco em `_projeto/riscos.tsv` | Pergunte se a dispensa está mantida |
| Um risco ou uma dependência não existe mais | Estado `fechado` em `riscos.tsv`, ou `rotina.py --dispensar DP-nnn --motivo "..."` | Libere o que estava travado |
| Um material de governança não é mais lido | `governanca.py --tirar CODIGO --motivo "..."` | O registro interno continua |
| Uma reunião ou um rito acabou | A data em `ate`, em `_projeto/ritos.tsv` | A rotina para de esperar as atas dele |
| O prazo mudou | `rotina.py --remarcar ID DATA --motivo "..."` | A data anterior fica em `prazos.tsv` |
| O projeto parou por um tempo | `rotina.py --pausar AAAA-MM-DD` | Os avisos voltam na data de retomada |

4. O comando é `python3 entregaveis/_harness/scripts/rotina.py`.
5. Procure o item nos outros registros e nos entregáveis: páginas que o
   citam, pedidos de material que só serviam a ele, ações que dependiam
   dele. Atualize cada um.
6. Mudança que toca o contrato, o tipo de trabalho ou a decisão que o
   projeto precisa provocar não é dispensa: siga `evoluir-projeto` ou
   leve ao consultor como mudança de escopo.
7. No relatório seguinte, liste o que saiu do plano, com o motivo.
