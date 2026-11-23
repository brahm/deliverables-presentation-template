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
| `martech-adtech` | Assessment de arquitetura de martech e adtech, arquitetura alvo, roadmap de plataformas |

Estão previstos os pacotes de transformação de marketing, mídia, retail
media, processos agênticos, proposta e treinamento.

## O que um pacote traz

Cada pacote é uma pasta com:

| Arquivo | O que traz |
| --- | --- |
| `PACOTE.md` | Quando usar, o que perguntar ao dono, os entregáveis típicos, os frameworks, os esqueletos de storyline, a evidência que cada afirmação pede e as armadilhas |
| `pedido-de-dados.tsv` | A lista padrão de dados a pedir ao cliente, com a análise que usa cada item e a prioridade |
| `entrevistas.md` | Roteiro de entrevista por tipo de interlocutor |
| `glossario.tsv` | Termos do domínio, para somar ao glossário do projeto |
| `skill/SKILL.md` | A skill `pacote-NOME`, que diz que parte do pacote abrir em cada momento |

Quando nenhum pacote serve ao projeto, o agente monta um pacote próprio
em `entregaveis/_projeto/pacote/`, com o mesmo formato, a partir do que o
dono contou e do que ele conhece do domínio. Cada escolha entra em
`decisoes.md` como decisão assumida, para o dono confirmar.
