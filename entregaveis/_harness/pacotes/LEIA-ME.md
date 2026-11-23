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
| `midia` | Auditoria de mídia, estratégia e plano, alocação de orçamento, medição, modelo de operação com agências |
| `retail-media` | Rede de mídia de um varejista, ou o investimento de uma marca nas redes dos varejistas |
| `processos-agenticos` | Desenho de processos com agentes de IA e automação de marketing, do mapa de oportunidades ao piloto |
| `proposta` | Proposta comercial, resposta a concorrência, apresentação oral, escopo de trabalho |
| `treinamento` | Cursos, workshops, material didático, exercícios e exames |

Os pacotes se somam. Uma proposta de assessment de martech ativa
`proposta` e `martech-adtech`. Um projeto de transformação com
capacitação das equipes ativa `transformacao-marketing` e `treinamento`.

## O que um pacote traz

Cada pacote é uma pasta com:

| Arquivo | O que traz |
| --- | --- |
| `PACOTE.md` | Quando usar, o que perguntar ao consultor, os entregáveis típicos, os frameworks, os esqueletos de storyline, a evidência que cada afirmação pede e as armadilhas |
| `pedido-de-dados.tsv` | A lista padrão de dados a pedir ao cliente, com a análise que usa cada item e a prioridade |
| `entrevistas.md` | Roteiro de entrevista por tipo de interlocutor |
| `glossario.tsv` | Termos do domínio, para somar ao glossário do projeto |
| `skill/SKILL.md` | A skill `pacote-NOME`, que diz que parte do pacote abrir em cada momento |

## O que um pacote não traz

Um pacote é ponto de partida genérico, escrito com prática corrente de
mercado. Ele não traz o método de nenhuma organização nem o contexto de
nenhum cliente, porque o template é público.

O que é próprio de um projeto é escrito dentro dele, em
`entregaveis/_dominio/`, pela skill `calibrar-dominio`: o método, as
regras de checagem e os casos de teste, a partir das referências, do
contexto e do objetivo que o consultor fornece. Onde o domínio do projeto e
um pacote dizem coisas diferentes, vale o do projeto.
