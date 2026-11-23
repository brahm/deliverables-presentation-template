# Pacote: definição de processos de mídia digital

## Quando usar

O projeto define ou redesenha os processos de mídia digital de uma
empresa: como um pedido vira plano, como o plano é aprovado, executado,
medido e pago, e quem responde por cada passo entre o anunciante, a
agência e as plataformas.

Este pacote traz só a governança deste tipo de projeto: os controles que
precisam estar registrados e aprovados. Ele não traz método, etapas de
trabalho, lista de dados nem roteiro de entrevista. O método e o que é
do cliente chegam durante o projeto e ficam em `entregaveis/_dominio/`,
pela skill `calibrar-dominio`.

Quando o projeto também avalia o investimento ou o resultado da mídia,
some o pacote de mídia. Quando avalia as plataformas, some o de martech
e adtech.

## O que perguntar ao consultor no início

Além das perguntas de `iniciar-projeto`:

- Quais processos estão no escopo, e quem é o dono de cada um hoje?
- Quais partes participam: anunciante, agência, plataformas, outras
  áreas da empresa? Quem fala por cada uma?
- Quem aprova o processo novo no anunciante, e a agência precisa dar o
  de acordo?
- O contrato com a agência já traz níveis de serviço ou alçadas que o
  processo novo precisa respeitar?
- O processo novo muda o trabalho, o papel ou a ferramenta de alguém?

## Controles de governança

Os controles estão em `controles.tsv` e aparecem com
`governanca.py --controles`. Cada um diz o que precisa ficar registrado,
antes de que etapa do entregável e que evidência o fecha.

| Controle | Vale | Antes de | O que protege |
| --- | --- | --- | --- |
| Taxonomia de campanhas e dicionário de métricas aprovados | Sempre | Storyline | Todos contam a mesma coisa do mesmo jeito antes de o processo ser desenhado |
| Papéis e níveis de serviço entre anunciante, agência e plataformas | Sempre | Revisão | Cada passagem entre as partes tem responsável e prazo aceitos pelos dois lados |
| Alçadas de aprovação de planos e autorizações de mídia | Sempre | Revisão | O processo diz quem aprova o quê e até que valor |
| Validação de cada processo com o dono | Sempre | Envio | O material não sai com erro de fato sobre o trabalho de alguém |
| Plano e registro de entrevistas e workshops | Quando o levantamento ouve mais de uma área ou empresa | Storyline | O levantamento ouviu quem precisava, e cada conversa deixou registro |
| Avaliação de impacto da mudança | Quando o processo muda o trabalho de alguém | Envio | As áreas afetadas sabem o que muda e que apoio terão |

O controle condicional começa como "a confirmar", e o consultor diz se
vale. Um controle só é dado como cumprido com a evidência e com o nome
de quem confirmou. A dispensa é do consultor, com o motivo.

## O que este pacote não traz

- O desenho dos processos, a notação e o nível de detalhe.
- A lista de dados e de documentos a pedir.
- O roteiro das entrevistas e dos workshops.
- Os termos e as métricas do cliente.

Tudo isso é fornecido pelo consultor durante a execução do projeto.
