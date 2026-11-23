---
name: definir-governanca
description: Use depois de fechar o brief de um projeto novo, ao adotar um projeto em andamento, quando o estado diz que o nível de governança não foi definido, quando o consultor pede, tira ou muda um material de governança e quando o projeto cresce ou encolhe. Sugere o nível pelo porte, mostra os materiais que serão emitidos, grava a escolha do consultor e mantém os papéis, a linha de base, as mudanças e as versões.
metadata:
  origem: harness-de-entregaveis
---

# Definir a governança

O nível escolhe só o que é emitido para pessoas lerem: enxuto, padrão ou
completo. Os registros de `entregaveis/_projeto/` são mantidos em
qualquer nível, e por isso subir de nível depois não perde histórico. O
comando é `python3 entregaveis/_harness/scripts/governanca.py`.

1. Leia os sinais com `governanca.py --sugerir`. Passe o que o brief e
   o consultor já disseram: `--semanas`, `--frentes`, `--pessoas`,
   `--comite nenhum|sim|niveis`, `--pagamento marco` e `--beneficio`. Em
   projeto em andamento, o `levantar.py` lista os materiais de
   governança que já circulam.
2. Leve a sugestão ao consultor em uma mensagem: o nível, o motivo em
   uma frase e a lista de materiais, com cadência e destinatário.
   Pergunte uma vez: enxuto, padrão, completo ou personalizado, e o que
   ele quer tirar, incluir ou pedir diferente. Sem resposta, siga com o
   sugerido e registre como decisão assumida.
3. Grave com `governanca.py --nivel NIVEL` e ajuste a lista:
   - `--tirar CODIGO --motivo "..."` para o que ele não quer;
   - `--incluir CODIGO` para algo do catálogo, que sai com `--catalogo`;
   - `--ajustar CODIGO --cadencia "..." --destinatario "..."`;
   - `--sob-medida "NOME" --destinatario "..." --cadencia "..." --traz
     "..." --fontes "..."` para o pedido diferente. Pergunte para quem
     é, com que frequência e o que precisa trazer, e aponte de quais
     registros ele sai.
4. Em projeto em andamento, mantenha o formato que o cliente já usa e
   troque só a fonte: o material existente passa a ser preenchido a
   partir dos registros. Anote o caminho do modelo em `observacao`, em
   `_projeto/governanca.tsv`. Quando dois materiais fazem o mesmo papel,
   o consultor escolhe um.
5. Registre a escolha com `registrar-decisao`: nível, materiais,
   cadência, destinatários e materiais sob medida.
6. Preencha os registros de onde os materiais saem:
   - `_projeto/papeis.tsv`, com quem executa e quem aprova cada
     entregável. Só uma pessoa aprova cada item;
   - `_projeto/premissas.tsv` e `_projeto/dependencias.tsv`, com o que
     o brief e o escopo trazem. Em cada ação, `depende_de` diz o que
     precisa terminar antes;
   - em `_projeto/riscos.tsv`, a probabilidade, o impacto e os itens que
     cada risco ameaça;
   - em `_projeto/cadencias.tsv`, o dia do status e a tolerância de
     prazo.
7. Quando o plano for aprovado, grave a linha de base com
   `governanca.py --linha-de-base --aprovada-por "NOME"`. Ela fotografa
   os prazos dos entregáveis, dos marcos e das ações com `base: sim`.
   `governanca.py --desvios` compara a fotografia com hoje.
8. Pedido fora do combinado, envio e aceite seguem a skill
   `emitir-material`: o ciclo de mudança, com impacto e decisão, e o
   ciclo de aprovação, com o prazo de resposta do aprovador. O aceite
   vem do cliente, nunca do agente.
9. Status semanal, status executivo, pauta, nota de entrega, aceite,
   quadro de aprovações e solicitação de mudança saem prontos de
   `python3 entregaveis/_harness/scripts/emitir.py`, pela mesma skill.
10. Para os outros materiais, leia a linha de cada um em
    `_projeto/governanca.tsv`: o que traz e de quais registros sai.
    Monte a partir dos registros, sem digitar de novo o que já está
    neles, e passe o texto por `humanizar-texto`. Quem envia é o
    consultor.
11. Reveja o nível quando o consultor pedir, quando a lista do dia
    perguntar e a cada fase nova. Suba quando aparecer uma segunda
    frente, um comitê, um pagamento por marco, um compromisso de
    benefício ou dois desvios acima da tolerância. Desça, ou tire o
    material, quando ele deixar de ser lido.
12. Os pacotes ativos podem trazer controles do tipo de projeto.
    `governanca.py --controles` mostra a lista. Pergunte uma vez se
    cada controle condicional vale e responda com `--controle CODIGO` e
    `--pendente`, `--cumprido` ou `--nao-se-aplica`. O controle fecha
    com a evidência e com quem confirmou, nunca por suposição.
13. O esforço fica em `_projeto/esforco.tsv` quando o consultor informa.
    Não pergunte por horas e não avise que falta lançamento.

Relate com `relatar-ao-consultor`: o nível, a lista de materiais e o que
ficou assumido.
