# Histórico do kit

A skill `atualizar-harness` lê este arquivo a partir da versão instalada
no projeto. Cada versão diz o que mudou e o que o projeto precisa fazer.

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
