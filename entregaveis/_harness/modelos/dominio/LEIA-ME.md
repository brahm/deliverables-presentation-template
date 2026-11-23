# Domínio do projeto

Esta pasta guarda o que é próprio deste projeto: os métodos, os
critérios e as regras que saíram das referências, do contexto e do
objetivo que o consultor forneceu. O template público traz só o esqueleto. O
conteúdo é escrito aqui, dentro do projeto, pela skill
`calibrar-dominio`.

O que está aqui costuma ser propriedade de uma organização ou dizer
respeito a um cliente. Por isso:

- esta pasta só existe em git local ou em repositório privado, e o
  harness bloqueia o projeto em repositório público;
- nada daqui volta ao template, nem como lição, nem como exemplo;
- o material de origem fica em `_intake/materiais/`, fora do git, e
  aqui entra a descrição do método com a referência ao material, sem
  cópia de trechos.

| Arquivo | O que traz |
| --- | --- |
| `dominio.md` | O método do projeto em prosa: contexto, objetivo, métodos, critérios de qualidade, evidência exigida, armadilhas e roteiros |
| `checagens.tsv` | As regras que o validador aplica aos entregáveis deste projeto |
| `casos.tsv` | Os casos de teste: para cada regra, um texto que ela acusa e um que ela deixa passar |
| `checagens_extra.py` | Regras em Python, para o que uma expressão não alcança. Opcional |
| `ferramentas/` | Scripts próprios do projeto, quando o método pede um cálculo ou uma conversão que se repete. Opcional |

`python3 entregaveis/_harness/scripts/dominio.py` roda os casos. O
validador aplica as regras a cada gravação e antes da revisão, e reprova
uma regra que não tem os dois casos.
