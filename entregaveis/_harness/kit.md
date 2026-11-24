# O harness neste projeto

| | |
| --- | --- |
| Origem | <https://github.com/brahm/deliverables-presentation-template> |
| Versão | veja o arquivo `VERSAO` |

## Como as peças se encaixam

| Peça | O que faz | Quando roda |
| --- | --- | --- |
| `REGRAS.md` | As regras e o momento de cada skill | Lida por todo agente no início da sessão |
| `guia.md` | O guia de uso para o consultor, com todos os recursos | Lido pelo consultor, e pelo agente quando ele pergunta como usar |
| `.claude/skills/` | Um procedimento curto por momento | Aberta pelo agente quando o momento chega |
| `.claude/settings.json` | Liga os seis hooks | Pelo Claude Code |
| `hooks/mensagem.py` | Lembra o agente do ponto em que cada entregável está e da skill do momento, quando a mensagem fala de uma mudança de fase, de uma ata, de uma dispensa ou de um follow-up com o cliente. Guarda o que o segundo cérebro já tinha por absorver no começo do turno | A cada mensagem, no Claude Code |
| `scripts/estado.py` | O estado do projeto em poucas linhas | No início da sessão |
| `scripts/validar.py` | As checagens em script | A cada gravação (hook), antes da revisão e no pull request |
| `scripts/rotina.py` | A rotina do dia: acha atas e arquivos novos, compara a data de hoje com os prazos do cronograma, guarda o histórico de cada data mudada, monta a lista do dia, registra o follow-up com o cliente e grava o diário | No início e no fim do dia, e quando um prazo muda |
| `scripts/afazeres.py` | O que a lista do dia usa: os itens abertos, quem trava quem, a exposição dos riscos, as cobranças e as perguntas de cada frequência | Chamado pelo `rotina.py --lista` |
| `scripts/governanca.py` | Sugere o nível de governança pelo porte, grava a escolha e os materiais, e mantém a linha de base, os desvios, as versões e o aceite. Conduz o ciclo de aprovação, que o envio abre e o aceite fecha, e o ciclo de mudança: pedido, impacto e decisão | Depois do brief, quando o porte muda, a cada envio e a cada pedido fora do combinado |
| `scripts/emitir.py` | Monta dos registros o status semanal, o status executivo, a pauta, a nota de entrega, o aceite, o quadro de aprovações e a solicitação de mudança, com o semáforo pela regra | No dia do status e quando o consultor pede um material |
| `scripts/cerebro.py` | O segundo cérebro: busca nas notas e nos registros, mostra o que falta absorver, marca o que cada nota absorveu, refaz o índice e confere as notas | A cada ação do projeto e antes de escrever |
| `governanca/catalogo.tsv` | O catálogo dos materiais de governança, com o nível em que cada um entra, a cadência, o destinatário e os registros de onde sai | Lido pelo `governanca.py` |
| `scripts/ambiente.py` | Confere se a máquina tem o Python, o Git e os programas do gerador, e diz como instalar o que falta em cada sistema | Antes de instalar e no início do projeto |
| `scripts/preparar.py` | Cria os registros e as pastas de entregável e ativa pacotes | No início do projeto e a cada entregável novo |
| `scripts/fase.py` | Mostra as fases do projeto e abre uma fase nova, guardando o brief da anterior e criando a página de passagem | Quando o projeto muda de natureza |
| `scripts/levantar.py` | Levanta o que já existe em um projeto em andamento | Na adoção |
| `scripts/gerar.py` | Gera PowerPoint, Word, PDF e Excel a partir da fonte em Markdown, sobre o modelo do projeto. Pede `python-pptx`, `python-docx` e `openpyxl` | Depois da redação e a cada correção da fonte |
| `scripts/empacotar.py` | Monta o pacote de instruções e de conhecimento para Claude desktop, ChatGPT desktop e Microsoft Copilot, com ou sem os registros do projeto | Quando o trabalho vai para outro ambiente e depois de mudar o método ou uma skill |
| `scripts/repositorio.py` | Diz se o remoto do git é local, privado ou público, e registra a confirmação do consultor | No início do projeto, a cada gravação de registro e a cada envio |
| `scripts/dominio.py` | Aplica as regras do domínio do projeto e roda os casos de teste delas | A cada gravação, na validação e quando uma regra muda |
| `scripts/conferir_interativo.js` | Abre um HTML interativo em um navegador sem interface, bloqueia a rede, lista os erros e grava as imagens. Opcional, pede Node e Playwright | Antes de entregar uma peça interativa |
| `metodo/` | O método, as práticas de texto, o visual, os formatos, o HTML interativo, a rubrica e o segundo cérebro | Aberto quando a tarefa toca no assunto |
| `listas/` | Os padrões das checagens de texto, por idioma | Lidas pelo `validar.py` |
| `modelos/` | Os modelos dos registros, dos entregáveis e dos HTML interativos | Copiados pelo `preparar.py` |
| `pacotes/` | A adaptação a cada tipo de projeto, com os controles de governança próprios do tipo | Ativados no início do projeto |

## As checagens

`python3 entregaveis/_harness/scripts/validar.py` roda todas. O hook roda
as mesmas no arquivo que acabou de ser gravado.

| Checagem | O que pega |
| --- | --- |
| Briefing | Seção sem preencher, pedido sem dono ou sem prazo |
| Storyline | Título que é rótulo e não mensagem, falta de resumo ou de pedido, página escrita sem aprovação |
| Densidade | Título e corpo acima do limite do veículo |
| Evidência | Número sem fonte, fonte que não está no registro, marca de rascunho esquecida |
| Texto | Vícios de texto gerado por IA, por idioma |
| Termos | Variante proibida pelo glossário, sigla sem definição |
| Estrutura | Numeração, tipo de página, referência cruzada quebrada |
| Confidencialidade | Termo proibido, credencial, falta da marcação obrigatória, material recebido dentro do git |
| Interativo | HTML que depende de arquivo, biblioteca ou rede de fora, animação sem movimento reduzido, peça sem mensagem ou sem fonte |
| Domínio | As regras que o projeto escreveu em `_dominio/`, e regra sem caso de teste que acusa e que passa |
| Repositório | Projeto com conteúdo em remoto público ou não verificado |
| Prazos | Ação aberta sem dono ou sem prazo, data ou estado inválido, item vencido sem resposta do consultor |
| Segundo cérebro | Nota com ligação quebrada, id que não existe, sem fonte, sem resumo ou órfã, nota que copia a linha de um registro e item do projeto fora das notas. Só avisa |
| Governança | Nível ou estado inválido, material fora do catálogo, id citado que não existe, ação concluída antes da confirmação do cliente, entregável sem aprovador |

## As três travas

No Claude Code, três pontos bloqueiam o agente. O resto são avisos que
ele recebe e corrige.

| Trava | Hook |
| --- | --- |
| Página, arquivo final ou peça interativa sem briefing completo e storyline aprovada pelo consultor | `hooks/antes_de_gravar.py` |
| Fim de turno com conteúdo alterado e sem revisão registrada | `hooks/fim_do_turno.py` |
| Registro de projeto gravado, ou envio feito, com o remoto público ou não verificado | `hooks/antes_de_gravar.py` e `hooks/antes_de_comando.py` |

## Os gatilhos do segundo cérebro

Cada ação do projeto leva à atualização das notas. Nenhum gatilho
bloqueia: o de fim de turno segura o turno uma vez por item, e o agente
pode seguir dizendo que a absorção ficou para o fechamento do dia.

| Gatilho | O que acontece |
| --- | --- |
| Gravação de registro, material ou entregável | `hooks/depois_de_gravar.py` diz ao agente o item novo que nenhuma nota guarda, uma vez por item |
| Gravação de uma nota | O mesmo hook confere a nota e devolve os avisos dela |
| Fim de turno | `hooks/fim_do_turno.py` pede a absorção do que o turno registrou. O que já estava pendente antes não segura o turno |
| Início de sessão | `scripts/estado.py` conta as notas e o que falta absorver |
| Lista do dia | A caixa de entrada mostra o que está fora das notas |
| Validação | `scripts/validar.py` avisa, sem reprovar |
| Agente sem hooks | A regra 22 de `REGRAS.md` e o fechamento do dia da skill `rotina-diaria` |

Em outros agentes que leem `AGENTS.md` e rodam comandos, valem as
regras, as skills e as checagens. Sem hooks, as regras mandam rodar
`estado.py` no início e `validar.py` antes de entregar.

## De quem é cada arquivo

O que está em `_harness/` e as skills que vieram do kit pertencem ao kit:
uma atualização os substitui. Uma adaptação feita para este projeto fica
registrada em `_projeto/licoes.md`, para ser reaplicada depois de
atualizar. A licença do kit está em `LICENCA.txt`.

O que está em `_projeto/`, em `_intake/`, em `_dominio/`, em `_atas/`,
em `_cerebro/` e nas pastas de entregável é do projeto. O kit nunca substitui esses
arquivos.

## Os registros do dia a dia

Ficam em `_projeto/` e são mantidos pelo agente a partir das atas e do
que o consultor diz. O consultor corrige no resumo do dia.

| Registro | O que guarda |
| --- | --- |
| `reunioes.tsv` | Cada ata processada e cada reunião que ficou sem ata, com o que saiu dela |
| `ritos.tsv` | As reuniões que se repetem e a cadência de cada uma |
| `acoes.tsv` | As tarefas, os marcos, as decisões pedidas e as aprovações, com dono, prazo e a reunião de origem |
| `riscos.tsv` | Os riscos, com causa, efeito, dono, probabilidade, impacto, o item que ameaçam e a resposta |
| `premissas.tsv` | As premissas, com quem valida, até quando e o que acontece se forem falsas |
| `issues.tsv` | Os problemas que já aconteceram, com dono, ação, prazo e escalada |
| `dependencias.tsv` | O que o projeto espera de outra pessoa ou área, e o que fica travado enquanto isso |
| `mudancas.tsv` | Os pedidos fora do combinado, com o impacto e a decisão |
| `papeis.tsv` | Quem executa, quem aprova, quem é consultado e quem é informado em cada item |
| `linha-de-base.tsv` | As datas combinadas, por versão, com o motivo e quem aprovou |
| `versoes.tsv` | Cada versão enviada de um entregável, com o que mudou, quem recebeu e o aceite |
| `cobrancas.tsv` | Cada follow-up feito com o cliente e a resposta |
| `esforco.tsv` | As horas, quando o consultor quer registrar. Não gera pergunta nem aviso |
| `controles.tsv` | A resposta do projeto a cada controle de governança que os pacotes ativos trazem: cumprido com a evidência, pendente ou não se aplica |
| `insumos.tsv` | As informações que os pacotes ativos pedem ao consultor, com o que já foi recebido, de quem e onde ficou |
| `emitidos.tsv` | Cada material montado pelo `emitir.py`, com a data e o arquivo. Os rascunhos ficam em `emitidos/` |
| `governanca.tsv` | O nível escolhido, material por material, com o que foi tirado, incluído ou feito sob medida |
| `perguntas.tsv` | A frequência de cada pergunta da lista do dia |
| `afazeres.md` | A lista do dia gravada, com uma caixa por item |
| `prazos.tsv` | O histórico de cada data mudada: a original, a anterior, a nova, quem mudou e o motivo |
| `cadencias.tsv` | Os limites dos avisos, o dia do status, a tolerância de prazo, o prazo de resposta do aprovador e a pausa do projeto |
| `alertas.tsv` | Os avisos já mostrados, para o aviso leve não se repetir |
| `diario.md` | O fechamento de cada dia |

## O que fica no template e o que fica no projeto

O template é público e não tem cliente. Ele traz o esqueleto: o motor
das regras, o formato dos arquivos, os modelos em branco e os pacotes
genéricos. O conteúdo de domínio é escrito em cada projeto, em
`_dominio/`, a partir das referências, dos métodos, do contexto e do
objetivo que o consultor fornece. Esse conteúdo costuma ser propriedade de
uma organização ou dizer respeito a um cliente, e por isso:

- um projeto iniciado só vive em pasta sem git, em git local ou em
  repositório privado. `scripts/repositorio.py` faz ao remoto o pedido
  de clone sem credencial, seguindo os redirecionamentos: se o servidor
  entrega, o repositório é público e o harness bloqueia a gravação dos
  registros e o envio. O endereço de envio do remoto e o endereço
  escrito no próprio comando de envio passam pela mesma conferência;
- quando o remoto não responde, vale a confirmação do consultor, registrada
  em `_projeto/repositorio.tsv`;
- nada de `_dominio/` nem de `_cerebro/` volta ao template, nem como
  lição proposta.

## Adaptar o harness ao projeto

- O método, as regras e os casos de teste do trabalho ficam em
  `_dominio/`, escritos pela skill `calibrar-dominio`.
- Um limite de densidade muda em `_projeto/limites.tsv`.
- Um termo proibido entra em `_projeto/confidencial.tsv`.
- Um vício de texto que o consultor quer barrar entra em uma lista própria,
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
- `.github/about.md`
- `LICENSE` (a licença do kit segue em `_harness/LICENCA.txt`)
- `tools/testar_kit.py` e `tools/abrir_exemplo.py`
- `exemplo/`, o projeto fictício do brief à entrega
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
- Nos pacotes: a taxonomia de objetivos de aprendizagem de Benjamin
  Bloom, na revisão de Anderson e Krathwohl, e os quatro níveis de
  avaliação de treinamento de Donald Kirkpatrick, no pacote de
  treinamento. O conteúdo de domínio dos pacotes é prática corrente de
  mercado, escrita com palavras próprias e sem material de terceiros.
- No segundo cérebro: as quatro pastas PARA e os quatro passos CODE, de
  Tiago Forte, *Building a Second Brain* (2022), e o índice, o registro
  de atualizações e a conferência mantidos pelo agente, da nota "LLM
  wiki", de Andrej Karpathy (2026). As práticas estão descritas com
  palavras próprias.
- Processo de trabalho com agentes adaptado de
  <https://github.com/brahm/project-template> (licença MIT).
