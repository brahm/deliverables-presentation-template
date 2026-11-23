# Harness de entregáveis de consultoria

Um template de projeto que ensina um agente de IA a produzir
apresentações, propostas, documentos, planilhas e materiais de
treinamento do jeito que um bom time de consultoria produz: primeiro a
audiência e a decisão, depois a história, e só então as páginas.

Foi pensado para projetos de transformação de marketing, assessment de
arquitetura de martech e adtech, mídia, retail media e desenho de
processos agênticos e de automação de marketing. O harness chega sem
marca e sem cliente. No início de cada projeto ele pergunta do que é o
trabalho, pede os materiais e se adapta.

## Como começar

Projeto novo:

1. Clique em "Use this template" no GitHub e clone o repositório criado.
2. Abra o agente na pasta e diga, com as suas palavras, do que é o
   projeto. Ele segue a skill `iniciar-projeto`: confirma o que
   entendeu, pede modelos, guia de marca, apresentações de referência,
   escopo e as regras de material do cliente, e fecha o brief.

Projeto que já está em andamento: cole no agente o prompt pronto de
[INSTALL.md](INSTALL.md). O instalador não supõe como o projeto foi
organizado, não sobrescreve nada, e a skill `adotar-projeto` levanta o
que já existe antes de perguntar.

## Como o trabalho corre

| Etapa | O que sai | Quem aprova |
| --- | --- | --- |
| Briefing | Audiência que decide, de e para, grande ideia, pedido e resistências | O agente preenche e o dono confirma |
| Storyline | Abertura, resumo executivo e a sequência de títulos de ação | O dono |
| Storyboard | Uma ideia por página, com tipo de página e evidência | O agente |
| Redação | O conteúdo, com as checagens rodando a cada gravação | O agente |
| Revisão | A rubrica aplicada e registrada | O agente relata e o dono decide |
| Entrega | Versão curta, perguntas previstas, notas, idiomas e arquivo final | O dono envia |

Dois pontos bloqueiam o agente no Claude Code. Ele não consegue gravar
páginas sem briefing completo e storyline aprovada pelo dono, e não
consegue encerrar o turno com conteúdo alterado e sem revisão. O resto
são avisos que ele recebe e corrige.

## O que o harness pede a você

- Do que é o projeto e que decisão ele precisa provocar. Ele pergunta
  sempre, mesmo quando acha que sabe.
- Modelo de apresentação, documento e planilha, guia de marca e
  apresentações de referência.
- Escopo contratado, dados e a lista de pedido de dados ao cliente.
- As regras da sua organização e do cliente para materiais. Elas ficam
  como referência no intake, fora do git.
- Uma amostra de texto seu, se quiser que o material soe como você.
- A aprovação da storyline de cada entregável.

O material recebido fica em `entregaveis/_intake/materiais/`, que o git
ignora. O registro do que foi pedido e do que chegou fica em
`entregaveis/_intake/registro.tsv`.

## O que há no repositório

| Caminho | O que é |
| --- | --- |
| `AGENTS.md`, `CLAUDE.md` | A porta de entrada para o agente. Apontam para as regras. |
| `entregaveis/_harness/REGRAS.md` | As 19 regras e a tabela que diz quando cada skill se aplica. |
| `entregaveis/_harness/metodo/` | O método por etapa, as práticas de texto, o visual, os formatos e a rubrica de revisão. |
| `.claude/skills/` | 17 skills, uma por momento do trabalho. O dono nunca precisa citar uma. |
| `entregaveis/_harness/scripts/` | Estado do projeto, checagens, criação de registros, levantamento de projeto existente e instalador. |
| `entregaveis/_harness/hooks/` | Os cinco hooks do Claude Code. |
| `entregaveis/_harness/listas/` | Os padrões das checagens de texto em português, espanhol e inglês. |
| `entregaveis/_harness/modelos/` | Os modelos dos registros do projeto e dos entregáveis. |
| `entregaveis/_harness/pacotes/` | A adaptação por tipo de projeto: perguntas, frameworks, esqueletos de storyline, pedido de dados, entrevistas e glossário. |
| `tools/testar_kit.py` | Os testes do próprio kit. |

Os registros do projeto (`entregaveis/_projeto/`) e a pasta de cada
entregável nascem quando o projeto é iniciado.

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
| Confidencialidade | Termo proibido, credencial, falta da marcação obrigatória |

As práticas de texto são próprias do harness e estão em
[texto.md](entregaveis/_harness/metodo/texto.md). Elas cortam o que
denuncia texto genérico e preservam os recursos de uma apresentação
persuasiva, como o contraste entre o que é e o que poderia ser, desde
que planejados na storyline.

## Onde funciona

- Claude Code: tudo, incluindo os hooks.
- Outros agentes que leem `AGENTS.md` e rodam comandos: regras, skills e
  checagens. Sem hooks, as regras mandam rodar `estado.py` no início e
  `validar.py` antes de entregar.
- Aplicativos de conversa sem acesso a arquivos (Claude desktop, ChatGPT
  desktop, Microsoft Copilot): ainda não há pacote pronto. Está na lista
  abaixo.

Requisito: Python 3.9 ou mais novo, sem pacotes extras.

## O que esta versão ainda não tem

- Os pacotes de transformação de marketing, mídia, retail media,
  processos agênticos, proposta e treinamento. Já existe o de martech e
  adtech. Para os outros tipos, o agente monta o pacote do projeto com o
  que o dono conta.
- O gerador de PowerPoint, Word, PDF e Excel sobre o modelo do projeto.
  Hoje o agente gera o arquivo final com as ferramentas que tiver, a
  partir da fonte em Markdown.
- Os pacotes de instruções para Claude desktop, ChatGPT desktop e
  Microsoft Copilot.
- Um exemplo completo, do brief à entrega.

## Testar o kit

```sh
python3 tools/testar_kit.py
```

## Fontes e licença

O método junta as técnicas de Nancy Duarte no *HBR Guide to Persuasive
Presentations*, o princípio da pirâmide de Barbara Minto e práticas de
texto adaptadas da skill Humanizer e da página "Signs of AI writing" da
Wikipédia. O processo de trabalho com agentes vem de
[brahm/project-template](https://github.com/brahm/project-template). Os
créditos completos estão em [kit.md](entregaveis/_harness/kit.md).

Licença MIT. Veja [LICENSE](LICENSE).
