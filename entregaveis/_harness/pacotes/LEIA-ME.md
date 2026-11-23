# Pacotes por tipo de projeto

Um pacote adapta o harness a um tipo de trabalho. A skill
`iniciar-projeto` pergunta do que é o projeto e ativa os pacotes que
servem, com `python3 entregaveis/_harness/scripts/preparar.py --pacote NOME`.
A ativação copia a skill do pacote para `.claude/skills/pacote-NOME/`,
soma os termos dele ao glossário do projeto e cita o nome no campo
`pacotes` do brief. Um projeto pode ativar mais de um.

## Pacotes disponíveis

| Nome | Tipo de projeto |
| --- | --- |
| `transformacao-marketing` | Diagnóstico, modelo operacional, roadmap de transformação e plano de mudança |
| `martech-adtech` | Assessment de arquitetura de martech e adtech, arquitetura alvo, roadmap de plataformas |
| `processos-midia` | Definição ou redesenho de processos de mídia digital. Traz só os controles de governança |
| `midia` | Auditoria de mídia, estratégia e plano, alocação de orçamento, medição, modelo de operação com agências |
| `retail-media` | Rede de mídia de um varejista, ou o investimento de uma marca nas redes dos varejistas |
| `processos-agenticos` | Desenho de processos com agentes de IA e automação de marketing, do mapa de oportunidades ao piloto |
| `proposta` | Proposta comercial, resposta a concorrência, apresentação oral. Traz dois controles e as informações a pedir ao consultor, sem método |
| `treinamento` | Cursos, workshops, material didático, exercícios e exames |

Os pacotes se somam. Uma proposta de assessment de martech ativa
`proposta` e `martech-adtech`, e os controles do segundo esperam a
venda. Um projeto de transformação com
capacitação das equipes ativa `transformacao-marketing` e `treinamento`.

## O que um pacote traz

Cada pacote é uma pasta com:

| Arquivo | O que traz |
| --- | --- |
| `PACOTE.md` | Quando usar, o que perguntar ao consultor, os entregáveis típicos, os frameworks, os esqueletos de storyline, a evidência que cada afirmação pede e as armadilhas |
| `pedido-de-dados.tsv` | A lista padrão de dados a pedir ao cliente, com a análise que usa cada item e a prioridade |
| `entrevistas.md` | Roteiro de entrevista por tipo de interlocutor |
| `glossario.tsv` | Termos do domínio, para somar ao glossário do projeto |
| `insumos.tsv` | As informações que só o consultor fornece para este tipo de projeto: o que perguntar, antes de que etapa e onde a resposta fica |
| `controles.tsv` | Os controles de governança do tipo de projeto: o que precisa ficar registrado e aprovado, antes de que etapa e com que evidência |
| `skill/SKILL.md` | A skill `pacote-NOME`, que diz que parte do pacote abrir em cada momento |

`PACOTE.md` e a skill existem em todo pacote. Os outros arquivos são
opcionais. Um pacote pode trazer só os controles de governança, e nesse
caso o método, os dados a pedir e os roteiros vêm do consultor durante o
projeto.

## As informações que o consultor fornece

Há trabalho em que o método e o conteúdo são do consultor e não podem
estar em um template público. O pacote então diz só o que pedir.
`governanca.py --insumos` mostra as informações dos pacotes ativos, com
a pergunta de cada uma. O estado e a lista do dia dizem o que falta. Um
entregável que chega à etapa sem a informação é acusado como erro, e o
agente não a escreve no lugar do consultor. A resposta fica no projeto,
com quem forneceu e onde ficou.

## Os controles de governança

Um controle não descreve atividade. Ele diz o que o tipo de projeto
precisa ter registrado e aprovado, antes de que etapa do entregável, e
que evidência o fecha. `governanca.py --controles` mostra os controles
dos pacotes ativos. O estado conta os pendentes, a lista do dia pergunta
pelos que chegaram à etapa sem evidência e pelos condicionais, e o
registro de um envio avisa quando algum ficou para trás. O controle fecha
com a evidência e com quem confirmou, ou sai com o motivo, por decisão
do consultor.

## O que um pacote não traz

Um pacote é ponto de partida genérico, escrito com prática corrente de
mercado. Ele não traz o método de nenhuma organização nem o contexto de
nenhum cliente, porque o template é público.

O que é próprio de um projeto é escrito dentro dele, em
`entregaveis/_dominio/`, pela skill `calibrar-dominio`: o método, as
regras de checagem e os casos de teste, a partir das referências, do
contexto e do objetivo que o consultor fornece. Onde o domínio do projeto e
um pacote dizem coisas diferentes, vale o do projeto.
