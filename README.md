# Harness de entregáveis de consultoria

Um template que ensina um agente de IA a produzir apresentações,
propostas, documentos, planilhas, treinamentos e peças interativas em
HTML do jeito que um bom time de consultoria produz: primeiro a
audiência e a decisão, depois a história, e só então as páginas.

O template é público, sem marca e sem cliente. O método, as regras e os
testes de cada trabalho são escritos dentro do projeto, que só vive em
git local ou em repositório privado.

## Instalar

Você precisa de uma conta no GitHub, do Git e de um agente que leia a
pasta do projeto, como o Claude Code. O harness pede Python 3.9 ou mais
novo, sem pacotes extras. Só o gerador de arquivos pede `python-pptx`,
`python-docx` e `openpyxl`, e o LibreOffice para o PDF.

Você não precisa conferir isso à mão. Antes de instalar e no início do
projeto, o agente confere a máquina, mostra o que falta com o comando do
seu sistema e pergunta se instala ele mesmo ou se você prefere seguir o
passo a passo. Quem não pode instalar nada, ou só tem o Microsoft
Copilot no navegador, usa o método sem instalação:
[ambientes/LEIA-ME.md](entregaveis/_harness/ambientes/LEIA-ME.md).

### Projeto novo, pelo site do GitHub

1. Entre na sua conta do GitHub e abra o formulário
   [Criar um repositório a partir deste template](https://github.com/brahm/deliverables-presentation-template/generate).
   O mesmo formulário abre pela
   [página do repositório](https://github.com/brahm/deliverables-presentation-template):
   botão verde **Use this template**, no alto à direita, e depois
   **Create a new repository**.
2. Em **Repository name**, escreva o nome do projeto. Se o nome do
   cliente é sigiloso, use um codinome.
3. Na visibilidade, marque **Private**. O harness não inicia projeto em
   repositório público.
4. Clique em **Create repository from template**. O GitHub abre o
   repositório novo, que é só seu.
5. Traga o repositório para o computador. No repositório novo, clique
   no botão verde **Code**, copie o endereço e rode, no terminal:

   ```sh
   git clone ENDEREÇO-COPIADO
   ```

   Quem prefere não usar o terminal escolhe **Open with GitHub Desktop**
   no mesmo botão.
6. Abra o agente na pasta que o passo 5 criou e diga do que é o projeto.
   No Claude Code, entre na pasta pelo terminal e rode `claude`.

### Projeto novo, pelo terminal

Com o [GitHub CLI](https://cli.github.com) instalado, um comando cria o
repositório privado e baixa a pasta:

```sh
gh repo create NOME-DO-PROJETO --template brahm/deliverables-presentation-template --private --clone
cd NOME-DO-PROJETO
```

Depois abra o agente na pasta e diga do que é o projeto.

### Projeto novo, sem GitHub

Crie uma pasta vazia no computador, abra o agente nela e cole o prompt
da próxima seção. O projeto fica só na sua máquina, o que o harness
aceita.

### Projeto que já está em andamento

Cole no agente, dentro da pasta do projeto:

```text
Instale neste projeto o harness de entregáveis que está em
https://github.com/brahm/deliverables-presentation-template
seguindo a seção "Passos para o agente" do INSTALL.md desse repositório.
Não mova, renomeie nem apague nada do que existe, e me mostre a
simulação antes de instalar.
```

O prompt completo, o que o instalador muda e a instalação sem Python
estão em [INSTALL.md](INSTALL.md).

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

No dia a dia, salve as atas das reuniões em `entregaveis/_atas/`. O
agente lê cada uma, atualiza os registros com a reunião de origem e
mostra no resumo do dia o que mudou. Os avisos seguem o cronograma: um
item parado dentro do prazo, um prazo próximo e um prazo vencido, que
pede uma de três respostas: concluído, nova data ou não é mais
necessário. A data anterior fica guardada.

A lista do dia traz no topo até três itens: o vencido, o que trava
outros ou é ameaçado por um risco alto, o prazo com menos folga e o que
espera o cliente há mais tempo sem cobrança. O que depende de aprovação
do cliente só segue com a confirmação, que você informa ou o agente
pergunta pelo follow-up. O agente também sugere o nível de governança
pelo porte do projeto, enxuto, padrão ou completo, e você escolhe os
materiais que serão emitidos. O status, a pauta e o aceite saem dos
registros como rascunho, e você revisa e envia. Um envio abre o prazo de
resposta do aprovador, e um pedido fora do combinado espera a decisão.
Os pacotes de tipo de projeto trazem os controles de governança próprios
do tipo, que só fecham com evidência.

O que o projeto aprende vai para o segundo cérebro, em notas de Markdown
dentro de `entregaveis/_cerebro/`. O agente atualiza a nota do assunto a
cada ação do projeto, com o id do registro de onde vem cada afirmação, e
busca nas notas e nos registros antes de escrever. Não é preciso
instalar nenhum programa.

Quando o projeto muda de natureza, diga o que aconteceu: a proposta foi
vendida, uma extensão foi contratada. O agente abre uma fase nova, que
herda as decisões, as evidências e tudo o que foi produzido.

O [guia de uso](entregaveis/_harness/guia.md) apresenta todos os
recursos, o que dizer em cada momento e o que fazer quando algo trava.

Você não precisa citar skill nem comando. Os que ajudam a acompanhar:

```sh
python3 entregaveis/_harness/scripts/estado.py        # onde cada entregável está
python3 entregaveis/_harness/scripts/validar.py       # todas as checagens
python3 entregaveis/_harness/scripts/gerar.py ID      # PowerPoint, Word, PDF ou Excel sobre o seu modelo
python3 entregaveis/_harness/scripts/fase.py          # as fases do projeto: proposta, trabalho vendido, extensão
python3 entregaveis/_harness/scripts/dominio.py       # os casos de teste do domínio
python3 entregaveis/_harness/scripts/repositorio.py   # o remoto é local, privado ou público
python3 entregaveis/_harness/scripts/rotina.py        # o resumo do dia: atas novas, prazos e o que espera o seu sim
python3 entregaveis/_harness/scripts/rotina.py --lista  # a lista do dia, com o que pede atenção primeiro
python3 entregaveis/_harness/scripts/governanca.py    # o nível de governança e os materiais emitidos
python3 entregaveis/_harness/scripts/emitir.py status-semanal  # o rascunho do status, montado dos registros
python3 entregaveis/_harness/scripts/cerebro.py --buscar TERMO  # o que o projeto sabe sobre um assunto
python3 entregaveis/_harness/scripts/ambiente.py      # o que a máquina tem e como instalar o que falta
```

## Ver um exemplo

A pasta [exemplo/](exemplo/LEIA-ME.md) traz um projeto fictício inteiro,
do brief à entrega: o que a consultora disse em cada etapa, o que o
agente registrou e o [arquivo final](exemplo/resultado/leitura-executiva.pdf).
Para abrir o exemplo com o harness rodando:

```sh
python3 tools/abrir_exemplo.py ../exemplo-aberto
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
arquivo externo, ação sem dono ou com prazo vencido sem resposta e as
regras do domínio do projeto.

Em outros agentes que leem `AGENTS.md` e rodam comandos, valem as
regras, as skills e as checagens, sem os hooks.

No Claude desktop, no ChatGPT desktop e no Microsoft Copilot, o método
chega como um texto de instruções para colar e arquivos de conhecimento
para enviar, sem travas nem checagens automáticas. O passo a passo está
em [ambientes/LEIA-ME.md](entregaveis/_harness/ambientes/LEIA-ME.md).

## Onde ler mais

| Para saber | Leia |
| --- | --- |
| As regras e o momento de cada skill | [REGRAS.md](entregaveis/_harness/REGRAS.md) |
| Todos os recursos e como usar cada um | [guia.md](entregaveis/_harness/guia.md) |
| Um projeto fictício, do brief à entrega | [exemplo/LEIA-ME.md](exemplo/LEIA-ME.md) |
| O método, etapa por etapa | [metodo.md](entregaveis/_harness/metodo/metodo.md) |
| As práticas de texto | [texto.md](entregaveis/_harness/metodo/texto.md) |
| Formatos, veículos e idiomas | [formatos.md](entregaveis/_harness/metodo/formatos.md) |
| HTML interativo em arquivo único | [interativo.md](entregaveis/_harness/metodo/interativo.md) |
| O uso no Claude desktop, no ChatGPT e no Copilot | [ambientes/LEIA-ME.md](entregaveis/_harness/ambientes/LEIA-ME.md) |
| Os pacotes por tipo de projeto | [LEIA-ME.md](entregaveis/_harness/pacotes/LEIA-ME.md) |
| As peças do kit, as checagens e os créditos | [kit.md](entregaveis/_harness/kit.md) |
| O que mudou em cada versão | [HISTORY.md](HISTORY.md) |

## Testar o kit

```sh
python3 tools/testar_kit.py
```

## Licença

MIT. Veja [LICENSE](LICENSE). As fontes do método estão em
[kit.md](entregaveis/_harness/kit.md).
