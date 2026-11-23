# O harness neste projeto

| | |
| --- | --- |
| Origem | <https://github.com/brahm/deliverables-presentation-template> |
| Versão | veja o arquivo `VERSAO` |

## Como as peças se encaixam

| Peça | O que faz | Quando roda |
| --- | --- | --- |
| `REGRAS.md` | As regras e o momento de cada skill | Lida por todo agente no início da sessão |
| `.claude/skills/` | Um procedimento curto por momento | Aberta pelo agente quando o momento chega |
| `.claude/settings.json` | Liga os cinco hooks | Pelo Claude Code |
| `scripts/estado.py` | O estado do projeto em poucas linhas | No início da sessão |
| `scripts/validar.py` | As checagens em script | A cada gravação (hook), antes da revisão e no pull request |
| `scripts/preparar.py` | Cria os registros e as pastas de entregável | No início do projeto e a cada entregável novo |
| `scripts/levantar.py` | Levanta o que já existe em um projeto em andamento | Na adoção |
| `metodo/` | O método, as práticas de texto, o visual, os formatos e a rubrica | Aberto quando a tarefa toca no assunto |
| `listas/` | Os padrões das checagens de texto, por idioma | Lidas pelo `validar.py` |
| `modelos/` | Os modelos dos registros e dos entregáveis | Copiados pelo `preparar.py` |
| `pacotes/` | A adaptação a cada tipo de projeto | Ativados no início do projeto |

## De quem é cada arquivo

O que está em `_harness/` e as skills que vieram do kit pertencem ao kit:
uma atualização os substitui. Uma adaptação feita para este projeto fica
registrada em `_projeto/licoes.md`, para ser reaplicada depois de
atualizar. A licença do kit está em `LICENCA.txt`.

O que está em `_projeto/`, em `_intake/` e nas pastas de entregável é do
projeto. O kit nunca substitui esses arquivos.

## Adaptar o harness ao projeto

- Um limite de densidade muda em `_projeto/limites.tsv`.
- Um termo proibido entra em `_projeto/confidencial.tsv`.
- Um vício de texto que o dono quer barrar entra em uma lista própria,
  `listas/texto-pt.tsv` por exemplo, com uma linha em `licoes.md`.
- Um procedimento que o projeto repete vira uma skill nova em
  `.claude/skills/`, com uma linha na tabela de momentos de `REGRAS.md`.
  A descrição de uma skill começa por "Use quando" e diz o momento.

## Skills de terceiros

Uma skill escrita por outra pessoa é um conjunto de instruções que o
agente vai seguir. Leia inteira antes de instalar, confira a licença,
instale só a que o projeto precisa agora e registre a origem, a versão,
a licença e o motivo em `_projeto/decisoes.md`.

As skills do kit trazem `origem: harness-de-entregaveis` no cabeçalho. O
instalador só troca as que têm essa linha. Uma skill do projeto com o
mesmo nome é mantida e aparece no relatório da instalação.

## Arquivos só do kit

Servem ao repositório do template e não a um projeto. Em um projeto
criado a partir do template, apague-os ao iniciar:

- `README.md` (escreva o do projeto no lugar)
- `INSTALL.md` e `install.sh`
- `HISTORY.md`
- `LICENSE` (a licença do kit segue em `_harness/LICENCA.txt`)
- `tools/testar_kit.py`
- `.github/workflows/kit.yml`

## Fontes do método

- Nancy Duarte, *HBR Guide to Persuasive Presentations* (Harvard Business
  Review Press, 2012): audiência como protagonista, grande ideia,
  contraste entre o que é e o que poderia ser, chamada para ação, teste
  dos três segundos, tipos de página e de diagrama, clareza de dados. As
  técnicas estão descritas com palavras próprias. O texto do livro não
  faz parte deste repositório.
- Barbara Minto, o princípio da pirâmide: resposta primeiro e argumentos
  que não se sobrepõem.
- Práticas de texto adaptadas da skill Humanizer
  (<https://github.com/blader/humanizer>, licença MIT, copyright 2025
  Siqi Chen) e da página "Signs of AI writing" da Wikipédia. Só entraram
  as práticas que não conflitam com as técnicas de apresentação acima.
- Processo de trabalho com agentes adaptado de
  <https://github.com/brahm/project-template> (licença MIT).
