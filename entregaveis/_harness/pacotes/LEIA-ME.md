# Pacotes por tipo de projeto

Um pacote adapta o harness a um tipo de trabalho. A skill
`iniciar-projeto` pergunta do que é o projeto e ativa os pacotes que
servem. Ativar um pacote é copiar a skill dele para `.claude/skills/` e
citar o nome no campo `pacotes` do brief.

Cada pacote é uma pasta com:

| Arquivo | O que traz |
| --- | --- |
| `PACOTE.md` | Quando usar, os entregáveis típicos, os frameworks, os esqueletos de storyline e as armadilhas |
| `pedido-de-dados.tsv` | A lista padrão de dados a pedir ao cliente |
| `entrevistas.md` | Roteiro de entrevista por tipo de interlocutor |
| `glossario.tsv` | Termos do domínio, para somar ao glossário do projeto |
| `skill/SKILL.md` | A skill que aplica o pacote nos momentos certos |

Quando nenhum pacote serve ao projeto, o agente monta um pacote próprio
em `entregaveis/_projeto/pacote/`, com o mesmo formato, a partir do que o
dono contou e do que ele conhece do domínio. Cada escolha entra em
`decisoes.md` como decisão assumida, para o dono confirmar.
