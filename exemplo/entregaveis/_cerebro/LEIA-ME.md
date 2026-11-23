# Segundo cérebro do projeto

Esta pasta guarda o que o projeto aprendeu, em notas curtas de Markdown
que qualquer editor abre. O agente escreve e mantém as notas. Você lê,
corrige e pergunta.

| Pasta | O que guarda |
| --- | --- |
| `1-projetos/` | O que tem prazo e fim: cada entregável em andamento e cada frente de trabalho |
| `2-areas/` | O que é acompanhado enquanto o projeto existir: o cliente, as pessoas, as plataformas, os processos e o contrato |
| `3-recursos/` | O que serve de consulta: métodos, conceitos, referências e o resumo de cada material recebido |
| `4-arquivo/` | O que deixou de estar ativo: entregável entregue, frente encerrada e fase anterior |

Comece pelo `indice.md`, que traz uma linha por nota. O `registro.md`
diz o que entrou e quando. O `absorvido.tsv` é o controle do agente: ele
marca o que já foi lido em cada registro do projeto.

Os registros do projeto continuam sendo a fonte dos dados. A nota cita o
id do registro e diz o que o dado significa. Decisões, mudanças de data,
cobranças e avisos ficam nos registros e não são copiados para cá.

Para achar algo, peça ao agente ou rode na raiz do projeto:

```sh
python3 entregaveis/_harness/scripts/cerebro.py --buscar multa rescisão
```
