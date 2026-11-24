---
name: atualizar-harness
description: Use quando o consultor disser que o harness tem versão nova, ou quando uma lição deste projeto vale para qualquer projeto. Traz as regras, skills e checagens novas sem perder o que foi adaptado aqui, e leva as lições propostas ao template.
metadata:
  origem: harness-de-entregaveis
---

# Manter o projeto e o harness em dia

`entregaveis/_harness/kit.md` diz de onde o harness veio, e
`_harness/VERSAO` diz a versão instalada.

## Trazer a versão nova

1. Clone a origem em uma pasta temporária, ou use a cópia local que o
   consultor indicar. Sem acesso, diga isso em uma linha e pare. O
   consultor também pode atualizar sozinho, com a instalação em uma
   linha do INSTALL.md da origem e a opção `--atualizar`.
2. Leia o `HISTORY.md` da origem a partir da versão instalada. Sem nada
   novo, diga isso em uma linha e pare.
3. Rode o instalador da origem com `--simular` e leia o que ele faria.
   Depois rode
   `install.sh --destino RAIZ_DO_PROJETO --atualizar`. Ele substitui o
   que pertence ao kit e não toca em `_projeto/`, `_intake/`,
   `_dominio/`, `_cerebro/` nem nas pastas de entregável.
4. Reaplique as adaptações do projeto que viviam em arquivos do kit. A
   lista delas está em `_projeto/licoes.md`.
5. Uma regra nova que conflita com uma decisão do projeto é uma pergunta
   para o consultor.
6. Rode `python3 entregaveis/_harness/scripts/validar.py` e relate o que
   entrou e o que você deixou de fora, com o motivo.

## Levar lições ao template

1. Liste as linhas de `_projeto/licoes.md` com o estado `proposta`.
2. Escreva cada uma como ela ficaria no template: a mudança na regra, na
   skill ou na checagem, em termos gerais, sem o nome do cliente nem o
   assunto do projeto. Nada de `_dominio/` nem de `_cerebro/` sai do
   projeto: nem método, nem regra, nem caso de teste, nem nota. O
   template é público.
3. Abra um pull request no repositório do template só quando o consultor
   pedir ou concordar. Sem acesso, entregue ao consultor o texto a aplicar.
4. Depois da fusão, marque as linhas como `no template`.
