# Lições

Quando o consultor corrige o agente, ou um erro se repete, a lição entra aqui
com a guarda que a impede de voltar. A ordem de preferência das guardas:
uma checagem em script, uma linha em uma skill, uma regra mais precisa e,
por último, uma regra nova.

| Id | Data | O que deu errado | Causa | Guarda e onde ela está | Estado |
| --- | --- | --- | --- | --- | --- |
| L-001 | 2026-10-27 | Dois títulos do primeiro rascunho diziam "ferramenta", e a diretoria só fala "plataforma" | O glossário tinha o termo e não tinha a variante a evitar | A coluna `evitar` do termo "plataforma" em `_projeto/glossario.tsv`. A checagem de termos reprova a variante | guardada |
| L-002 | 2026-11-05 | A diretora financeira perguntou pela multa de rescisão, e a página do pedido não respondia | As resistências do briefing não traziam a do financeiro sobre o custo de sair | O critério "Rescisão" na revisão própria de `_dominio/dominio.md`, que a skill `revisar-entregavel` aplica a todo entregável do projeto | guardada |
