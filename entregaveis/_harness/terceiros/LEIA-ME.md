# Skills de terceiros

O kit instala junto com as suas as skills de design de interface de Emil
Kowalski, publicadas em <https://github.com/emilkowalski/skills> com a
licença MIT. A cópia é do commit `64eb3deb9a5fbfa041faf783e0bc3fd635872e9c`, de 15 de novembro de 2026.

Elas cuidam do acabamento de todo HTML de entrega: a curva e a duração
do movimento, a ordem em que as partes entram, o retorno ao toque, o
foco, a tipografia e o comportamento no celular. O momento de cada uma e
os limites que o harness impõe estão na seção "As skills de design de
interface" de [metodo/interativo.md](../metodo/interativo.md).

## Como a cópia é guardada

- Cada skill fica em `.claude/skills/NOME/`, com os arquivos do original
  sem mudar uma linha.
- O arquivo `.origem`, ao lado de cada uma, traz a marca do kit, a
  fonte e o commit. É por ele que o instalador sabe que a skill veio do
  kit e pode trocá-la com `--atualizar`. Uma skill do projeto com o
  mesmo nome e sem esse arquivo nunca é trocada.
- [skills.tsv](skills.tsv) lista cada arquivo com o seu hash SHA-256. O
  `tools/testar_kit.py` confere que nada mudou e que nenhum arquivo
  entrou fora da lista.
- A licença do original está em
  [LICENCA-emilkowalski-skills.txt](LICENCA-emilkowalski-skills.txt).

## Revisão antes de copiar

O conteúdo é de terceiros e foi lido antes de entrar no kit. São só
arquivos Markdown, sem script, sem comando de instalação a rodar e sem
instrução escondida. Os dois caracteres invisíveis que aparecem servem
de exemplo: um separa blocos de código aninhados em
`improve-animations/PLAN-TEMPLATE.md` e o outro compõe um emoji de teste
em `break-ui/CATALOG.md`.

## Trazer uma versão nova

1. Baixe o repositório original em uma pasta fora do projeto.
2. Leia o que mudou desde o commit acima, como na revisão desta página.
3. Copie as pastas de `skills/` para `.claude/skills/`, mantendo o
   `.origem` de cada uma com o commit novo.
4. Refaça `skills.tsv` com o hash de cada arquivo e atualize o commit
   nesta página.
5. Rode `python3 tools/testar_kit.py` e registre a versão nova em
   `HISTORY.md`.
