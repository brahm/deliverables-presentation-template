# Harness de entregáveis de consultoria

Um template que ensina um agente de IA a produzir apresentações,
propostas, documentos, planilhas, treinamentos e peças interativas em
HTML do jeito que um bom time de consultoria produz: primeiro a
audiência e a decisão, depois a história, e só então as páginas.

O template é público, sem marca e sem cliente. O método, as regras e os
testes de cada trabalho são escritos dentro do projeto, que só vive em
git local ou em repositório privado.

## Instalar

Projeto novo:

1. Clique em "Use this template" no GitHub e crie o repositório como
   **Private**. O harness não inicia projeto em repositório público.
2. Clone o repositório e abra o agente na pasta.

Projeto que já está em andamento: cole no agente, dentro do projeto.

```text
Instale neste projeto o harness de entregáveis que está em
https://github.com/brahm/deliverables-presentation-template
seguindo a seção "Passos para o agente" do INSTALL.md desse repositório.
Não mova, renomeie nem apague nada do que existe, e me mostre a
simulação antes de instalar.
```

O prompt completo e a instalação sem Python estão em
[INSTALL.md](INSTALL.md). Requisito: Python 3.9 ou mais novo, sem
pacotes extras. Só o gerador de arquivos pede `python-pptx`,
`python-docx` e `openpyxl`, e o LibreOffice para o PDF.

## Usar

1. Diga ao agente, com as suas palavras, do que é o projeto e que
   decisão ele precisa provocar. Ele confirma o que entendeu, confere se
   o repositório é privado e pede modelos, guia de marca, escopo e as
   regras de material.
2. Entregue as referências, os métodos, o contexto e o objetivo. O
   agente escreve o domínio do projeto em `entregaveis/_dominio/`: o
   método, as regras de checagem e um caso de teste que acusa e outro
   que passa para cada regra.
3. Peça um entregável. O agente fecha o briefing e traz a storyline: a
   sequência de títulos que conta a história.
4. Aprove a storyline. Só depois disso o agente escreve páginas,
   documentos, planilhas e peças interativas.
5. Receba o material revisado e o arquivo final gerado sobre o seu
   modelo, com o que foi checado, o que foi assumido e o que ficou por
   fazer. Quem envia ao cliente é você.

Você não precisa citar skill nem comando. Os que ajudam a acompanhar:

```sh
python3 entregaveis/_harness/scripts/estado.py        # onde cada entregável está
python3 entregaveis/_harness/scripts/validar.py       # todas as checagens
python3 entregaveis/_harness/scripts/gerar.py ID      # PowerPoint, Word, PDF ou Excel sobre o seu modelo
python3 entregaveis/_harness/scripts/dominio.py       # os casos de teste do domínio
python3 entregaveis/_harness/scripts/repositorio.py   # o remoto é local, privado ou público
```

## O que o harness segura

Três travas bloqueiam o agente no Claude Code:

- página, arquivo final ou peça interativa sem briefing completo e
  storyline aprovada por você;
- fim de turno com conteúdo alterado e sem revisão registrada;
- registro de projeto gravado, ou envio feito, com o remoto público ou
  não verificado.

O resto são checagens que rodam a cada gravação e devolvem o que
corrigir: título que é rótulo, texto acima do limite do veículo, número
sem fonte, vício de texto gerado por IA em português, espanhol e inglês,
termo fora do glossário, material confidencial, HTML que depende de
arquivo externo e as regras do domínio do projeto.

Em outros agentes que leem `AGENTS.md` e rodam comandos, valem as
regras, as skills e as checagens, sem os hooks.

## Onde ler mais

| Para saber | Leia |
| --- | --- |
| As regras e o momento de cada skill | [REGRAS.md](entregaveis/_harness/REGRAS.md) |
| O método, etapa por etapa | [metodo.md](entregaveis/_harness/metodo/metodo.md) |
| As práticas de texto | [texto.md](entregaveis/_harness/metodo/texto.md) |
| Formatos, veículos e idiomas | [formatos.md](entregaveis/_harness/metodo/formatos.md) |
| HTML interativo em arquivo único | [interativo.md](entregaveis/_harness/metodo/interativo.md) |
| Os pacotes por tipo de projeto | [LEIA-ME.md](entregaveis/_harness/pacotes/LEIA-ME.md) |
| As peças do kit, as checagens e os créditos | [kit.md](entregaveis/_harness/kit.md) |
| O que mudou em cada versão | [HISTORY.md](HISTORY.md) |

## O que esta versão ainda não tem

- Os pacotes de instruções para Claude desktop, ChatGPT desktop e
  Microsoft Copilot.
- Um exemplo completo, do brief à entrega.

## Testar o kit

```sh
python3 tools/testar_kit.py
```

## Licença

MIT. Veja [LICENSE](LICENSE). As fontes do método estão em
[kit.md](entregaveis/_harness/kit.md).
