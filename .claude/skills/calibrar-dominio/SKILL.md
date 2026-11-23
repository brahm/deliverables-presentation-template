---
name: calibrar-dominio
description: Use quando o dono fornece referências, métodos, contexto ou o objetivo do projeto, quando chega um material que muda o método e quando o estado diz que o domínio não foi calibrado. Escreve dentro do projeto o método, as regras de checagem e os casos de teste próprios deste trabalho, sem levar nada disso ao template.
metadata:
  origem: harness-de-entregaveis
---

# Calibrar o domínio do projeto

O template é público e traz só o esqueleto. O conteúdo de domínio
costuma ser propriedade de uma organização ou dizer respeito a um
cliente, e por isso é escrito aqui, em `entregaveis/_dominio/`, e fica
no projeto. Leia `entregaveis/_dominio/LEIA-ME.md` antes da primeira
vez.

1. Confira onde o projeto está guardado:
   `python3 entregaveis/_harness/scripts/repositorio.py`. Só siga em
   git local ou em repositório privado. Se o remoto for público, pare e
   leve ao dono as duas saídas: tornar o repositório privado ou remover
   o remoto.
2. Junte o que o dono forneceu: as referências e os métodos em
   `_intake/materiais/`, o contexto e o objetivo no brief. Registre
   cada material com a skill `receber-materiais`. Leia de cada um só o
   que trata de como o trabalho é feito e julgado.
3. Escreva `_dominio/dominio.md`: contexto e objetivo, métodos e
   frameworks, critérios de qualidade, evidência exigida, armadilhas,
   roteiros e pedidos, e os critérios de revisão próprios. Descreva com
   as suas palavras, sem copiar trechos do material, e diga a origem de
   cada item. O que você supôs entra em `_projeto/decisoes.md` como
   decisão assumida.
4. Um pacote ativo do harness é ponto de partida genérico. Onde o
   método do projeto diz outra coisa, vale o do projeto.
5. Transforme em regra cada critério que um texto consegue provar.
   Uma linha por regra em `_dominio/checagens.tsv`: um termo que não
   pode aparecer, uma seção que precisa existir, duas coisas que andam
   juntas, uma ordem. A mensagem diz o que corrigir. O que pede conta ou
   comparação vira função em `_dominio/checagens_extra.py`. O que só
   uma pessoa julga vai para a tabela de revisão de `dominio.md`.
6. Escreva os casos de teste em `_dominio/casos.tsv`. Para cada regra,
   um texto que ela acusa e um que ela deixa passar, com frases que
   poderiam estar em um entregável deste projeto e sem dado real do
   cliente.
7. Rode `python3 entregaveis/_harness/scripts/dominio.py`. Corrija a
   regra ou o caso até tudo passar. Uma regra sem os dois casos reprova
   o projeto, e é assim que deve ser.
8. Leve os termos do domínio a `_projeto/glossario.tsv`, os dados a
   pedir a `_intake/registro.tsv` e os limites diferentes a
   `_projeto/limites.tsv`.
9. Um cálculo ou uma conversão que o método repete vira um script em
   `_dominio/ferramentas/`, com um teste ao lado e uma linha em
   `dominio.md` que diz quando usar.
10. Rode `python3 entregaveis/_harness/scripts/validar.py` nos
    entregáveis que já existem. Um achado novo em material aprovado é
    uma pergunta para o dono, e não uma correção silenciosa.
11. Marque `estado: rascunho` em `dominio.md` e relate com
    `relatar-ao-dono`: os métodos que você registrou, as regras criadas
    com um exemplo de cada, o que ficou para a revisão humana e o que
    você supôs. Com o sim do dono, marque `estado: confirmado`.
12. Volte a esta skill quando chegar um material novo, quando o dono
    corrigir um método e quando uma revisão pegar o que uma regra
    deveria ter pego. Regra nova nasce com os dois casos.

Nada de `_dominio/` vai para o template, nem como lição proposta. Uma
lição que serve a qualquer projeto é reescrita em termos gerais, sem o
método, o cliente nem o assunto, antes de sair daqui.
