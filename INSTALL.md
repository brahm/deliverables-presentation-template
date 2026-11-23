# Instalar o harness em um projeto que já existe

O harness entra em qualquer projeto: vazio, repositório de código, pasta
só com apresentações, com ou sem git, com ou sem regras de agente
próprias. Ele não supõe como o projeto foi organizado e nunca
sobrescreve um arquivo do projeto.

Para um projeto novo, use o botão "Use this template" do GitHub, crie o
repositório como privado e abra o agente. Esta página é para o projeto
que já está em andamento.

Um projeto de cliente só fica em pasta sem git, em git local ou em
repositório privado. O instalador roda em qualquer lugar, mas o harness
bloqueia a gravação dos registros do projeto e o envio enquanto o remoto
for público.

## O prompt pronto

Cole no agente, dentro do projeto:

```text
Instale neste projeto o harness de entregáveis que está em
https://github.com/brahm/deliverables-presentation-template

Siga a seção "Passos para o agente" do INSTALL.md desse repositório.
Este projeto já está em andamento: não suponha como ele foi organizado
e não mova, renomeie nem apague nada do que existe. Antes de instalar,
me mostre o que a simulação diz que vai mudar.

Depois de instalar, levante o que o projeto já tem (apresentações,
documentos, dados, modelos, guia de marca, regras para agentes), encaixe
o harness nisso e me pergunte só o que os arquivos não respondem e onde
houver conflito. Ao terminar, relate o que foi instalado, o que você
encontrou e o que precisa de mim.
```

Se o agente não tem acesso à internet, baixe o repositório como ZIP,
descompacte fora do projeto e troque o endereço pelo caminho da pasta.

## Passos para o agente

1. Traga o kit para fora do projeto. Clone em uma pasta temporária
   (`git clone --depth 1 https://github.com/brahm/deliverables-presentation-template KIT`)
   ou use a cópia local que o consultor indicar. Nunca clone dentro do
   projeto.
2. Olhe o projeto antes de instalar: as pastas da raiz, os arquivos de
   instrução para agentes (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`,
   `.github/copilot-instructions.md`, `.cursorrules`) e
   `.claude/settings.json`. Você só lê nesta etapa.
3. Escolha o nome da pasta do harness. O padrão é `entregaveis`. Se o
   projeto já usa esse nome para outra coisa, ou se o consultor prefere outro,
   use `--pasta NOME`. Uma pasta `entregaveis/` que já existe pode ser
   usada: o harness só ocupa as subpastas que começam por `_` e as que
   têm `briefing.md`.
4. Simule e mostre a saída ao consultor:
   `sh KIT/install.sh --destino RAIZ_DO_PROJETO --simular`
5. Instale, com as mesmas opções e sem `--simular`. Acrescente `--ci`
   quando o projeto está no GitHub e o consultor quer as checagens em cada
   pull request.
6. Leia a seção "Atenção" da saída e resolva cada linha com o consultor. Uma
   skill do projeto com o mesmo nome de uma do kit é mantida, e o consultor
   decide qual fica.
7. Rode `python3 PASTA/_harness/scripts/repositorio.py`. Se o remoto for
   público, pare e leve ao consultor as saídas: tornar o repositório privado
   ou remover o remoto. Depois rode
   `python3 PASTA/_harness/scripts/estado.py`. Ele vai dizer que o
   projeto não foi iniciado.
8. Siga `.claude/skills/adotar-projeto/SKILL.md` se o projeto já tinha
   apresentações, documentos, dados ou regras antes do harness. Siga
   `.claude/skills/iniciar-projeto/SKILL.md` se ele estava vazio.
9. Apague a pasta temporária do kit. Mostre ao consultor o que mudou
   (`git status`, quando há git) e só faça commit quando ele pedir.

## O que o instalador faz

| Onde | O que acontece |
| --- | --- |
| `PASTA/_harness/` | Criada com as regras, o método, os scripts, os hooks e os modelos. |
| `PASTA/_projeto/`, `PASTA/_intake/` e `PASTA/_dominio/` | Criadas com os registros e o esqueleto de domínio em branco. Arquivo que já existe fica como está. |
| `.claude/skills/` | Recebe as 19 skills do kit. Skill do projeto com o mesmo nome é mantida. |
| `.claude/settings.json` | Criado, ou mesclado: os hooks e as permissões do harness entram ao lado dos que o projeto já tem. |
| `AGENTS.md` e `CLAUDE.md` | Criados, ou recebem no fim um bloco entre duas linhas marcadoras. O texto do projeto fica intacto. |
| `GEMINI.md`, `.github/copilot-instructions.md`, `.cursorrules`, `.windsurfrules` | Recebem o mesmo bloco, só quando já existem. |
| `.gitignore` | Recebe um bloco que deixa os materiais recebidos fora do git. Só quando o projeto usa git. |
| `.github/workflows/entregaveis.yml` | Só com `--ci`. |

Rodar de novo não duplica nada. `--atualizar` troca o que pertence ao
kit por uma versão mais nova e não toca nos registros nem nos
entregáveis do projeto.

## Requisitos

- Python 3.9 ou mais novo, sem pacotes extras, para o instalador, as
  checagens e os hooks.
- O gerador de arquivos (`gerar.py`) é a única peça que pede pacotes de
  fora: `python-pptx`, `python-docx` e `openpyxl`, um por formato. O PDF
  e as imagens de conferência pedem o LibreOffice.
- Os hooks rodam no Claude Code. Em outros agentes, as regras mandam
  rodar `estado.py` no início e `validar.py` antes de entregar.

## Sem Python

Em um ambiente sem Python, a instalação é uma cópia:

1. Copie `entregaveis/_harness/` do kit para `PASTA/_harness/` no
   projeto.
2. Copie as pastas de `.claude/skills/` do kit que ainda não existem no
   projeto.
3. Cole o bloco de `PASTA/_harness/instalacao/bloco-agents.md` no fim do
   arquivo de instruções do agente que o projeto usa.
4. Copie `PASTA/_harness/modelos/projeto/` para `PASTA/_projeto/`,
   `PASTA/_harness/modelos/intake/` para `PASTA/_intake/` e
   `PASTA/_harness/modelos/dominio/` para `PASTA/_dominio/`.

Sem Python não há checagem automática. O agente aplica à mão as páginas
de `PASTA/_harness/metodo/` e a rubrica de revisão, e diz isso no
relatório.

## Desinstalar

Apague `PASTA/_harness/`, as skills que têm
`origem: harness-de-entregaveis` no cabeçalho, os blocos entre as linhas
`harness-de-entregaveis: inicio` e `harness-de-entregaveis: fim`, e as
entradas de `.claude/settings.json` que apontam para `_harness/hooks/`.
Os registros de `PASTA/_projeto/`, o domínio de `PASTA/_dominio/` e os
entregáveis são do projeto e ficam.
