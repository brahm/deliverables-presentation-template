---
name: registrar-licao
description: Use quando o consultor corrige você ou precisa repetir uma instrução, quando uma checagem ou uma revisão pega o que uma regra deveria ter evitado, quando o mesmo erro acontece duas vezes e quando uma apresentação ensina algo sobre a audiência. Registra a lição e cria a guarda que impede a repetição.
metadata:
  origem: harness-de-entregaveis
---

# Transformar uma lição em guarda

O consultor não deveria precisar dizer a mesma coisa duas vezes.

1. Corrija primeiro o que deu errado, ou registre com `adiar-trabalho`.
2. Ache a causa. Faltava regra? A regra era vaga? Era clara e não foi
   aplicada? Algo nunca foi definido? Uma regra clara que não foi
   aplicada pede uma checagem, e não outra regra.
3. Escolha a guarda mais barata que teria pegado o erro, nesta ordem:
   - uma linha em uma lista de `entregaveis/_harness/listas/`, em
     `_projeto/confidencial.tsv` ou em `_projeto/glossario.tsv`;
   - um limite em `_projeto/limites.tsv`;
   - um critério na rubrica ou uma linha na skill do momento;
   - uma redação mais precisa de uma regra;
   - uma regra nova, em último caso.
4. Crie a guarda na mesma mudança e mostre que ela funciona: a checagem
   nova reprova o erro antigo.
5. Acrescente a linha a `entregaveis/_projeto/licoes.md` com o próximo
   id `L-nnn`: o que deu errado, a causa, a guarda e onde ela está, e o
   estado `guardada`. Sem guarda possível agora, o estado é `aberta`.
6. Se a lição serve a qualquer projeto, o estado é `proposta`: vale
   levá-la ao template com `atualizar-harness`.
7. Conte ao consultor em uma linha: o que deu errado e o que agora impede.
