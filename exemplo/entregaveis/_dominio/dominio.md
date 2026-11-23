---
estado: confirmado
calibrado_em: 2026-09-21
materiais: M-003, M-006
---
# Domínio do projeto

Campos do cabeçalho. `estado`: rascunho (você montou e o consultor ainda não
viu) ou confirmado (o consultor leu e concordou). `materiais`: os
identificadores do intake que serviram de base, como M-003. Cada item
desta página diz de onde veio: o material, a fala do consultor ou uma
suposição sua, que então também entra em `_projeto/decisoes.md`.

Este domínio é inventado para o exemplo do template. Em um projeto de
verdade, o que está aqui sai dos materiais e do método de quem conduz o
trabalho, e fica em repositório privado.

## Contexto e objetivo

A rede comprou plataformas de marketing por área durante seis anos, e
dois contratos vencem em março de 2027. A diretoria precisa decidir o
que sai antes do fim da janela de aviso, em 15 de janeiro. Conta como
resultado uma decisão por plataforma, com dono e data. Origem: brief do
projeto e proposta (M-003).

## Métodos e frameworks

**Inventário por capacidade.** Uma linha por plataforma contratada, com
a capacidade principal, a área dona, o custo anual e as datas do
contrato. Entra o extrato de contratos e faturas. Sai a contagem de
plataformas por capacidade, usada na leitura executiva. Origem: roteiro
de avaliação (M-006) e pacote de martech e adtech.

**Repetição de capacidade.** Duas plataformas pagas para a mesma
capacidade contam como repetidas depois de a pergunta ser feita aos dois
donos. Marcas ou regiões com necessidades diferentes não contam.
Origem: roteiro de avaliação (M-006) e decisão D-004.

**Escala de maturidade.** Cinco notas, da inicial à otimizada, com o
critério de cada nota escrito antes da avaliação. Uma nota entra no
material ao lado do critério que a justifica. Origem: pacote de martech
e adtech.

**Caminho do dado em um caso real.** O projeto segue o dado de carrinho
abandonado da coleta ao envio da campanha e mede o tempo de cada trecho.
Origem: fala da consultora em 2026-09-21.

## Critérios de qualidade

- Toda nota de maturidade vem com o critério (regra R-001).
- Toda recomendação de desligar, substituir ou consolidar diz quando o
  contrato vence (regra R-002).
- O material mostra o custo evitado, que é o número em que a diretoria
  financeira acredita primeiro (regra R-003).

## Evidência exigida

| Afirmação | Fonte aceita |
| --- | --- |
| Custo de uma plataforma | Contrato ou fatura (M-004) |
| Repetição de capacidade | Inventário validado pelos dois donos |
| Nota de maturidade | Critério declarado mais entrevista ou dado de uso |
| Tempo entre o evento e a campanha | Medição em um caso real, com data |

## Armadilhas

- Contar como repetição o uso por marcas diferentes.
- Recomendar a saída de uma plataforma fora da janela do contrato.
- Mostrar o nome comercial das plataformas em material projetado, o que
  as regras de material proíbem.

## Roteiros e pedidos

Perguntas a cada dono de plataforma: quem usa, para quê, com que
frequência, o que para se ela sair e quando o contrato vence. Os dados
pedidos estão em `_intake/registro.tsv`, de M-004 a M-009.

## Revisão própria do projeto

| Critério | Passa quando |
| --- | --- |
| Pergunta antes da conta | Cada par de plataformas repetidas foi confirmado com os dois donos. |
| Janela do contrato | Cada recomendação cabe na janela de aviso do contrato dela. |
| Rescisão | Toda recomendação de desligar diz se o contrato tem multa. Entrou com a lição L-002. |
