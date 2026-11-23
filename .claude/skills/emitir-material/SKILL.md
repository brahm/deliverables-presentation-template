---
name: emitir-material
description: Use quando chega o dia do status, quando o consultor pede o status semanal, o status executivo, a pauta de uma reunião, a nota de entrega, o pedido ou o termo de aceite ou o quadro de aprovações, quando um entregável é enviado ou aceito e quando surge um pedido fora do combinado. Monta o material a partir dos registros, sem digitar de novo o que já está neles, e conduz o ciclo de aprovação e o ciclo de mudança.
metadata:
  origem: harness-de-entregaveis
---

# Emitir um material de governança

O material sai dos registros de `entregaveis/_projeto/`. O comando é
`python3 entregaveis/_harness/scripts/emitir.py`, e sem argumento ele
lista o que monta e quais materiais estão na lista do projeto. O
resultado é um rascunho: o consultor revisa e é ele quem envia.

## Antes de emitir

1. Atualize os registros. O material repete o que eles dizem: ação
   concluída sem `rotina.py --concluir` e ata sem `processar-ata` ficam
   fora do status.
2. Confira a lista do projeto com `governanca.py`. Para um material fora
   da lista, o comando monta o rascunho e avisa. Passar a emitir é
   escolha do consultor: `governanca.py --incluir CODIGO`.

## Os materiais

| Pedido | Comando |
| --- | --- |
| Status da semana | `emitir.py status-semanal` |
| Status para o comitê | `emitir.py status-executivo` |
| Pauta de reunião que decide | `emitir.py pauta --reuniao "NOME" --data AAAA-MM-DD` |
| Nota que acompanha um envio | `emitir.py nota-de-entrega ID` |
| Pedido, confirmação ou termo de aceite | `emitir.py aceite ID` |
| Quem aprova e como está cada envio | `emitir.py ciclo-de-aprovacao` |
| Solicitação de mudança | `emitir.py mudanca MU-nnn` |

3. Rode com `--gravar`. O rascunho fica em `_projeto/emitidos/` e a
   emissão em `_projeto/emitidos.tsv`. O status seguinte conta o período
   a partir da última emissão.
4. Complete com o consultor cada ponto que saiu com a marca de dado
   ausente: objetivo da reunião, opções e recomendação de uma decisão,
   leitura do prognóstico. Não invente o que os registros não trazem.
5. O semáforo segue a regra. Vermelho: desvio da linha de base acima da
   tolerância ou issue escalada. Amarelo: desvio dentro da tolerância,
   item vencido sem data nova ou risco de exposição alta. Verde: nada
   disso. A cor diz se o compromisso está ameaçado, e não quanto foi
   feito. O consultor pode trocar a cor com `--cor COR --motivo "..."`,
   e o material mostra a cor dele, o motivo e a cor da regra.
6. Passe o texto por `humanizar-texto` e leve ao consultor. Depois do
   envio, troque a situação para `enviado` em `_projeto/emitidos.tsv`.

## O ciclo de aprovação

7. A cada envio ao cliente, rode `governanca.py --versao ID --mudou
   "..." --enviada-a "NOME"`. O comando abre uma aprovação do cliente em
   `_projeto/acoes.tsv`, para quem aprova o entregável em
   `_projeto/papeis.tsv`, com o prazo de resposta combinado ou o padrão
   de `_projeto/cadencias.tsv`. Emita a nota de entrega quando ela
   estiver na lista.
8. O silêncio não vale como aceite. A aprovação sem resposta aparece na
   lista do dia, é cobrada com `rotina.py --cobrado` e entra no status
   como pendência do cliente.
9. Quando o cliente aceitar, rode `governanca.py --aceite ID --quem
   "NOME" --ressalvas "..."`. O comando fecha a aprovação. A confirmação
   sai com `emitir.py aceite ID` e leva o aviso de faturamento quando um
   marco de pagamento está ligado ao entregável. O aceite vem do
   cliente, nunca do agente.

## O ciclo de mudança

10. Pedido fora do combinado não é atendido direto. Abra com
    `governanca.py --mudanca "PEDIDO" --solicitante "NOME"`. Quando o
    pedido vem de uma ata, passe `--origem A-nnn`.
11. Meça o impacto contra a linha de base e grave com `governanca.py
    --analisar MU-nnn --impacto-prazo "..." --impacto-esforco "..."
    --impacto-escopo "..."`. Onde não há impacto, escreva "nenhum".
12. Leve a quem decide com `emitir.py mudanca MU-nnn`. A decisão é do
    consultor com o cliente. Grave com `governanca.py --decidir MU-nnn
    --decisao aprovada|rejeitada --quem "NOME" --motivo "..."`.
13. Aprovada: mude as datas com `rotina.py --remarcar` e grave a versão
    nova da linha de base com `--motivo "MU-nnn"`. O comando recusa a
    linha de base que cita mudança sem aprovação. Rejeitada: o pedido
    vai sozinho para `_projeto/adiados.tsv`. Nos dois casos, registre
    com `registrar-decisao`.

Relate com `relatar-ao-consultor`: o material montado, os pontos que
faltam completar e o que espera resposta do cliente.
