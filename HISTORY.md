# Histórico do kit

A skill `atualizar-harness` lê este arquivo a partir da versão instalada
no projeto. Cada versão diz o que mudou e o que o projeto precisa fazer.

## 0.3.0

- Seis pacotes novos, no mesmo formato do primeiro:
  `transformacao-marketing`, `midia`, `retail-media`,
  `processos-agenticos`, `proposta` e `treinamento`. O de treinamento
  cobre cursos, workshops, material didático, exercícios e exames.
- Os pacotes se somam: um projeto pode ativar mais de um.

O que o projeto precisa fazer: ative com `preparar.py --pacote NOME` os
pacotes do seu tipo de trabalho. Se o projeto montou um pacote próprio
em `_projeto/pacote/` para um desses tipos, compare os dois e leve ao
dono o que mudar.

## 0.2.0

- Primeiro pacote por tipo de projeto: `martech-adtech`, para assessment
  de arquitetura de martech e adtech. Traz as perguntas de início, os
  entregáveis típicos, dez frameworks, três esqueletos de storyline, a
  evidência que cada afirmação pede, as armadilhas, a lista de pedido de
  dados, os roteiros de entrevista e o glossário.
- `preparar.py --pacote NOME` ativa um pacote: copia a skill, soma os
  termos ao glossário do projeto e preenche o campo `pacotes` do brief.
- O instalador atualiza a skill de um pacote já ativado no projeto.

O que o projeto precisa fazer: se o trabalho é um assessment de martech
e adtech, rode `preparar.py --pacote martech-adtech`.

## 0.1.0

Primeira versão.

- Regras em `entregaveis/_harness/REGRAS.md` e 17 skills aplicadas pelo
  momento do trabalho.
- Fluxo em etapas: briefing, storyline aprovada pelo dono, storyboard,
  redação, revisão e entrega.
- Checagens em script (`validar.py`): briefing, storyline, densidade,
  evidência, texto em português, espanhol e inglês, termos, estrutura,
  confidencialidade e intake.
- Cinco hooks do Claude Code. Dois bloqueiam: gravar páginas sem briefing
  completo e storyline aprovada, e encerrar o turno com conteúdo alterado
  e sem revisão. Os outros avisam.
- Instalador para projeto vazio ou em andamento (`install.sh`), com nome
  de pasta configurável e sem sobrescrever arquivo do projeto.

O que o projeto precisa fazer: nada.
