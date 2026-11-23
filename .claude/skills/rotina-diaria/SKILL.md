---
name: rotina-diaria
description: Use na primeira sessão de cada dia de trabalho, quando o estado mostra a linha da rotina do dia, quando o consultor pergunta o que há para hoje e quando ele encerra o dia. Coleta atas e materiais novos, confere os prazos pelo cronograma, mostra o resumo do dia em uma tela e grava o diário do projeto.
metadata:
  origem: harness-de-entregaveis
---

# Rotina diária

O consultor só confirma. Você coleta, atualiza os registros e mostra o
que mudou. Os avisos seguem o cronograma: o prazo de cada item manda, e
os limites de `entregaveis/_projeto/cadencias.tsv` só dizem quando
avisar dentro da janela dele.

## Abertura do dia

1. Rode `python3 entregaveis/_harness/scripts/rotina.py --abrir`. A
   saída é o resumo do dia.
2. Trate o que chegou antes de falar com o consultor. Cada ata nova ou
   alterada segue `processar-ata`. Cada arquivo da pasta de entrada, e
   cada arquivo que o consultor fez ou mudou à mão nas pastas de
   trabalho, segue `incorporar-material`.
3. Mostre o resumo em uma mensagem só, nesta ordem: os vencidos, o que
   cada ata mudou, o que espera o sim dele, os prazos próximos, o que
   parece parado e os avisos de cadência. Um resumo por dia, e não um
   aviso por item.
4. Vencido pede uma de três respostas, e não existe adiar sem data:
   - concluído: `rotina.py --concluir T-nnn`. Material que chegou segue
     `receber-materiais`;
   - nova data: `rotina.py --remarcar ID AAAA-MM-DD --motivo "..."`. O
     comando guarda a data anterior em `_projeto/prazos.tsv`;
   - não é mais necessário: siga `registrar-dispensa`.
5. Depois de remarcar, leia o que o comando disse. Na segunda
   remarcação, o item ganha destaque no status. Na terceira, abra um
   risco em `_projeto/riscos.tsv` e pergunte se é caso de escalar. Prazo
   da linha de base ou do contrato pede o acordo do cliente: registre
   com `registrar-decisao` e deixe a conversa com o consultor. Mostre os
   itens que dependem do remarcado e peça a data de cada um.
6. Prazo próximo: pergunte se o item vai cumprir, precisa de ajuda ou
   já pede data nova.
7. Parece parado: o aviso é leve e aparece uma vez. Se o item está
   andando, rode `rotina.py --andando T-nnn`. Se travou, abra um risco.
   Se não é mais necessário, siga `registrar-dispensa`.
8. Cadência:
   - reunião sem ata: pergunte se ela ocorreu. Peça a ata na pasta, ou
     faça três perguntas (o que foi decidido, quem ficou de fazer o quê
     e até quando, o que mudou) e siga `processar-ata` com o relato. Se
     não ocorreu, rode `rotina.py --sem-ata DATA --rito R --motivo "..."`;
   - rito sem ata há dois ciclos: pergunte se as atas pararam ou se o
     rito mudou, e ajuste `_projeto/ritos.tsv`;
   - projeto sem registro: pergunte se ele está pausado. Em pausa, rode
     `rotina.py --pausar AAAA-MM-DD`, com a data de retomada.

## Fechamento do dia

9. Quando o consultor encerrar o dia, pergunte em uma linha se houve
   reunião ou conversa que não está registrada e se algo deixou de ser
   necessário. Trate a resposta com `processar-ata` e
   `registrar-dispensa`.
10. Grave o diário: `rotina.py --fechar "o que chegou, o que mudou e o
    que ficou à espera"`.
11. Para um status, `rotina.py --datas` lista as datas deslocadas.

Nada sai do projeto por esta rotina. Mensagem ao cliente, cobrança e
envio são do consultor. Relate com `relatar-ao-consultor`.
