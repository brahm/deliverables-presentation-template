---
name: rotina-diaria
description: Use na primeira sessão de cada dia de trabalho, quando o estado mostra a linha da rotina do dia, quando o consultor pergunta o que há para hoje ou o que fazer primeiro e quando ele encerra o dia. Coleta atas e materiais novos, confere os prazos pelo cronograma, monta a lista do dia com o que pede atenção primeiro, faz as perguntas de cada frequência e grava o diário do projeto.
metadata:
  origem: harness-de-entregaveis
---

# Rotina diária

O consultor responde a uma lista, e não a um questionário. Você coleta,
atualiza os registros e mostra o que mudou. O prazo de cada item manda
nos avisos, e os limites de `entregaveis/_projeto/cadencias.tsv` só
dizem quando avisar. O comando é
`python3 entregaveis/_harness/scripts/rotina.py`.

## Abertura do dia

1. Rode `rotina.py --lista --abrir`. A saída é a lista do dia, gravada
   também em `_projeto/afazeres.md`.
2. Trate a caixa de entrada antes de falar com o consultor. Cada ata
   nova ou alterada segue `processar-ata`. Cada arquivo da pasta de
   entrada, e cada arquivo feito ou mudado à mão, segue
   `incorporar-material`. Depois rode `rotina.py --lista` de novo.
3. Mostre a lista em uma mensagem só, com o bloco de atenção no topo.
   Sobem no máximo três itens, nesta ordem: vencido sem data nova, item
   que trava outros ou é ameaçado por um risco de exposição alta, prazo
   com menos folga e item que espera o cliente há mais tempo sem
   cobrança. Depois vêm as próximas ações, o que aguarda o cliente, a
   agenda e o que há a confirmar.
4. Vencido pede uma de três respostas, e não existe adiar sem data:
   - concluído: `rotina.py --concluir ID`. Material que chegou segue
     `receber-materiais`;
   - nova data: `rotina.py --remarcar ID AAAA-MM-DD --motivo "..."`. A
     data anterior fica em `_projeto/prazos.tsv`;
   - não é mais necessário: siga `registrar-dispensa`.
5. Depois de remarcar, leia o que o comando disse. A segunda remarcação
   ganha destaque no status. Na terceira, abra um risco e pergunte se é
   caso de escalar. Prazo da linha de base ou do contrato pede o acordo
   do cliente: abra a mudança em `_projeto/mudancas.tsv` e siga
   `definir-governanca`. Mostre os itens que dependem do remarcado e
   peça a data de cada um.
6. O que aguarda o cliente traz a pergunta do follow-up, com quatro
   respostas:
   - aprovou: `rotina.py --cobrado ID --resposta aprovou`. O comando diz
     o que volta às próximas ações;
   - cobrei hoje: `rotina.py --cobrado ID`;
   - ainda não cobrei: `rotina.py --cobrado ID --resposta nao-cobrei` dá
     os fatos. Redija a mensagem de cobrança para o consultor enviar;
   - não depende mais de aprovação: `--resposta dispensada --motivo
     "..."`, e siga `registrar-dispensa`.

   Trabalho que depende do cliente não é concluído nem andado antes da
   confirmação: o comando recusa.
7. Prazo próximo: pergunte se o item vai cumprir, precisa de ajuda ou
   pede data nova. Parece parado: o aviso aparece uma vez. Se está
   andando, rode `rotina.py --andando ID`. Se travou, abra uma linha em
   `_projeto/issues.tsv`.
8. Cadência:
   - reunião sem ata: pergunte se ela ocorreu. Peça a ata na pasta, ou
     faça três perguntas (o que foi decidido, quem ficou de fazer o quê
     e até quando, o que mudou) e siga `processar-ata` com o relato. Se
     não ocorreu, rode `rotina.py --sem-ata DATA --rito R --motivo "..."`;
   - rito sem ata há dois ciclos: pergunte se as atas pararam ou se o
     rito mudou, e ajuste `_projeto/ritos.tsv`;
   - projeto sem registro: pergunte se ele está pausado. Em pausa, rode
     `rotina.py --pausar AAAA-MM-DD`, com a data de retomada.
9. As perguntas de calendário trazem a chave entre colchetes. As
   semanais aparecem na véspera do status: os três riscos principais, o
   retorno do cliente, as premissas a validar e os adiados. As de marco
   aparecem quando um marco é concluído ou um entregável é aceito. Leve
   cada resposta ao registro e marque com
   `rotina.py --respondida CHAVE`. A frequência de cada uma fica em
   `_projeto/perguntas.tsv`. Nunca pergunte por horas trabalhadas.

## Fechamento do dia

10. Quando o consultor encerrar o dia, pergunte em uma linha se houve
    reunião ou conversa que não está registrada e se algo deixou de ser
    necessário. Trate a resposta com `processar-ata` e
    `registrar-dispensa`, e marque
    `rotina.py --respondida reuniao,dispensa`.
11. Absorva o que o dia registrou com `manter-cerebro` e grave o
    diário: `rotina.py --fechar "o que chegou, mudou e ficou à espera"`.
12. Para um status, `rotina.py --datas` lista as datas deslocadas e
    `governanca.py --desvios` compara com a linha de base.

Nada sai do projeto por esta rotina. Mensagem ao cliente, cobrança e
envio são do consultor. Relate com `relatar-ao-consultor`.
