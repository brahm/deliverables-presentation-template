---
name: processar-ata
description: Use quando aparece um arquivo novo ou alterado na pasta de atas, quando o consultor cola ou conta o que houve em uma reunião e quando o resumo do dia lista uma ata. Lê a ata, leva cada trecho ao registro certo com a reunião de origem, propõe as tarefas e mostra ao consultor o que mudou.
metadata:
  origem: harness-de-entregaveis
---

# Processar uma ata

O consultor salva as atas em `entregaveis/_atas/`, do jeito que a
ferramenta de reunião exporta. A pasta fica fora do git. Só os itens
extraídos entram nos registros, cada um com a reunião de origem.

1. Leia a ata com `python3 entregaveis/_harness/scripts/rotina.py --ler
   ARQUIVO`. O comando lê texto, transcrição com marca de tempo e
   documento do Word. Outro formato, abra com as suas ferramentas. Na
   ata alterada depois de processada, o comando mostra só a diferença:
   trate só ela.
2. Ligue a ata à reunião: a data, o nome e o rito de
   `_projeto/ritos.tsv`. Uma reunião fora do calendário entra sem rito.
3. Leve cada trecho ao seu registro:

| O que a ata traz | Onde entra | Como |
| --- | --- | --- |
| Decisão tomada | `_projeto/decisoes.md` | `Vigente`, com quem decidiu e a reunião no motivo |
| Decisão adiada ou pedida | `_projeto/acoes.tsv`, tipo `decisao` | Com prazo e o que ela trava |
| Tarefa com dono e prazo | `acoes.tsv`, tipo `tarefa` | `aberta`. Tarefa do cliente leva `lado: cliente` |
| Tarefa sem dono ou sem prazo | `acoes.tsv` | `proposta`, com o dono e o prazo que você sugere |
| Marco, meta ou prazo novo | `acoes.tsv`, tipo `marco` | Prazo que muda usa `rotina.py --remarcar` |
| Pedido novo de escopo | `_projeto/mudancas.tsv` | `proposta`, com o impacto em prazo, esforço e escopo |
| Risco ou preocupação | `_projeto/riscos.tsv` | `proposto`, com causa, efeito, probabilidade e impacto |
| Problema que já ocorreu | `_projeto/issues.tsv` | `aberta`, com o impacto e quem resolve |
| Premissa confirmada ou derrubada | `_projeto/premissas.tsv` | A premissa falsa aponta os entregáveis que dependiam dela |
| O que depende de outra área ou de terceiro | `_projeto/dependencias.tsv` | Com o prazo e o que ela afeta |
| Dado prometido ou entregue | `_intake/registro.tsv` | Prazo novo, ou `recebido` com `receber-materiais` |
| Pessoa nova ou papel que mudou | `_projeto/audiencia.md` e `papeis.tsv` | Com a reação registrada |
| Compromisso da consultoria | `acoes.tsv`, `lado: consultoria` | Com dono na equipe |
| Comentário sobre um entregável | A pasta do entregável | Correção com `redigir-conteudo`, ou `adiar-trabalho` |
| Aprovação dita em reunião | `decisoes.md` | Aceite verbal. Proponha a confirmação por escrito, e só então `rotina.py --cobrado` |
| Fato ou número citado | `_projeto/evidencias.tsv` | Confiança `baixa`, com a reunião como fonte, a confirmar |

4. Ata gerada por IA erra nomes, troca quem disse o quê e inventa
   prazos. Por isso:
   - todo item leva a origem (`A-nnn`) e, em `observacao`, o trecho;
   - a ação e a decisão que já existem são atualizadas, e não criadas
     de novo;
   - o que toca o contrato ou sai do projeto entra como `proposta` e
     espera o sim do consultor: escopo novo, data da linha de base,
     aceite e qualquer mensagem ao cliente;
   - a aprovação de uma storyline só vale quando vem do consultor.
5. Os ids seguem o registro: ações `T-nnn`, riscos `RS-nnn`, decisões
   `D-nnn`, premissas `PR-nnn`, issues `IS-nnn`, dependências `DP-nnn` e
   mudanças `MU-nnn`. Em toda ação, `inicio` é o dia em que ela nasceu,
   `movida_em` é hoje e `depende_de` traz o que precisa terminar antes.
6. Registre a ata processada:
   `rotina.py --ata ARQUIVO --data AAAA-MM-DD --reuniao "NOME" --rito "R"
   --fonte "FERRAMENTA" --participantes "..." --resultado "2 decisões, 3
   ações, 1 risco"`. Um relato sem arquivo usa `--ata` sem o nome do
   arquivo, e a fonte vira relato de memória.
7. Uma decisão nova pode mudar entregáveis: siga o passo 7 de
   `registrar-decisao`.
8. Mostre ao consultor o que mudou por causa desta ata, item por item,
   com o que espera o sim dele. Ele corrige ou desfaz com uma resposta.
9. Redija a nota de decisões e ações da reunião, para o consultor
   enviar se quiser. Quem envia é ele.
