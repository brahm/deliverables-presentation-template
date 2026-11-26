# O Deliverables Presentation Template fora do Claude Code

O Claude desktop, o ChatGPT desktop e o Microsoft Copilot não rodam os
hooks nem os scripts do harness. Neles o método chega de outro jeito: um
texto de instruções, que você cola uma vez, e poucos arquivos de
conhecimento, que você envia ao projeto ou ao agente.

## O que vale em cada ambiente

| | Claude Code | Claude desktop, ChatGPT desktop e Copilot |
| --- | --- | --- |
| Regras e método | Sim | Sim, pelas instruções e pelos arquivos |
| Procedimentos de cada momento | Skills, que se aplicam sozinhas | O arquivo `1-procedimentos`, que o agente abre |
| Travas | Bloqueiam a gravação e o envio | Viram regras que o agente segue, sem bloqueio |
| Checagens de texto, fonte e densidade | Automáticas, a cada gravação | Feitas à mão pelo agente, pela lista de `2-metodo-e-texto` |
| Registros do projeto | Arquivos em `entregaveis/_projeto/` | Um registro único, que o agente atualiza e você guarda |
| Arquivo final sobre o modelo | `gerar.py` | Depende do ambiente: ele gera o arquivo ou entrega a fonte página por página |
| Domínio do projeto | Regras com casos de teste | Texto no arquivo `5-projeto`, conferido à mão |
| Atas, prazos e rotina diária | `rotina.py` lê a pasta de atas e calcula os avisos | Você anexa a ata, e o agente atualiza o registro e confere os prazos à mão a cada conversa |
| Requisitos da máquina | Python 3.9 ou mais novo, conferido por `ambiente.py` | Nenhum: nada é instalado |

O que se perde é a garantia. Sem trava e sem checagem automática, o
resultado depende de o agente seguir as instruções. Para material que vai
ao cliente, a revisão final no Claude Code continua valendo a pena.

## Conferir o ambiente

O harness confere o ambiente no início de um projeto novo e na
instalação em um projeto em andamento. O que ele confere depende de onde
você trabalha.

| Onde você trabalha | O que é conferido | Quem confere |
| --- | --- | --- |
| Um agente que roda comandos na pasta do projeto, como o Claude Code e os que leem `AGENTS.md` | Python 3.9 ou mais novo, o comando `python3`, o Git e os pacotes e programas do gerador de arquivos | O script `ambiente.py`. Ele lista o que falta com o comando de cada item, e o agente se oferece para instalar ou passa o passo a passo |
| Um aplicativo de conversa com projeto, como o Claude desktop e o ChatGPT desktop | Se o agente lê os arquivos anexados, roda código e cria PowerPoint, Word e Excel | O próprio agente, na primeira conversa, pelas instruções coladas |
| Só o navegador, como o Copilot web | O mesmo. Nada pode ser instalado | O próprio agente, na primeira conversa |

Na pasta do projeto, o comando é
`python3 entregaveis/_harness/scripts/ambiente.py`. Em uma máquina em
que você não pode instalar nada, use um dos caminhos sem instalação
desta página: o método vale inteiro, sem as checagens automáticas.

## Os arquivos

- [instrucoes.md](instrucoes.md): o texto para colar no campo de
  instruções. Tem menos de 8.000 caracteres, o menor limite entre os
  três ambientes.
- `conhecimento/`: os arquivos para enviar, em `.txt`, que é o formato
  que os três aceitam.

| Arquivo | O que traz |
| --- | --- |
| `1-procedimentos.txt` | O passo a passo de cada momento do trabalho |
| `2-metodo-e-texto.txt` | O método, as práticas de texto, os vícios a tirar e a rubrica de revisão |
| `3-formatos-e-visual.txt` | Limites por veículo, gráficos, diagramas e HTML interativo |
| `4-modelos.txt` | Os modelos de briefing, storyline, storyboard, página e registros |
| `pacote-NOME.txt` | Um por tipo de projeto. Envie só os que o projeto usa |

Os quatro primeiros e um pacote somam cinco arquivos, o que cabe no
plano gratuito do ChatGPT.

## Com o projeto dentro

Em um projeto que já usa o harness no Claude Code, monte o pacote do
projeto:

```sh
python3 entregaveis/_harness/scripts/empacotar.py --projeto
```

Ele grava em `entregaveis/_ambiente/` as instruções, os quatro arquivos
do método, os pacotes das fases do projeto e o arquivo `5-projeto.txt`,
com o brief, as fases, a marca, o glossário, as decisões, as evidências,
o domínio e o briefing e a storyline de cada entregável. A lista de
nomes confidenciais fica de fora.

Esse arquivo é material do projeto saindo para outro ambiente. Só envie
a um ambiente que as regras da sua organização e do cliente permitem. A
pasta `entregaveis/_ambiente/` fica fora do git.

## Passo a passo

Os nomes dos menus mudam com a versão e com o idioma do aplicativo. Os
limites e os formatos abaixo foram conferidos na documentação de cada
produto em novembro de 2026.

### Claude desktop

1. Abra Projects e crie um projeto novo.
2. Em "Set project instructions", cole o conteúdo de `instrucoes.md`.
3. Na base de conhecimento do projeto, envie os arquivos de
   `conhecimento/`.
4. Abra uma conversa no projeto e diga do que é o trabalho.

### ChatGPT desktop

1. Crie um projeto.
2. Em "Add project instructions", cole o conteúdo de `instrucoes.md`.
3. Envie os arquivos de `conhecimento/`. O limite por projeto é de 5
   arquivos no plano gratuito, 25 nos planos Go e Plus e 40 nos planos
   Pro, Business, Enterprise e Edu, com 10 arquivos por envio.
4. Abra uma conversa no projeto e diga do que é o trabalho.

### Microsoft Copilot

1. No Microsoft 365 Copilot, escolha "New agent" e depois "Skip to
   configure".
2. No campo de instruções, cole o conteúdo de `instrucoes.md`. O limite
   é de 8.000 caracteres.
3. Em conhecimento, envie os arquivos de `conhecimento/`. O limite é de
   20 arquivos, e Markdown não é aceito: por isso os arquivos são
   `.txt`. O envio de arquivos depende da licença da sua organização.
4. Abra o agente e diga do que é o trabalho.

### Só o Copilot web, sem instalar nada

Para quem só pode usar o Copilot no navegador, em
`m365.cloud.microsoft/chat`. Há três caminhos. Use o primeiro que a sua
conta oferecer.

1. Um caderno do Copilot (Copilot Notebooks) para o projeto. Em "More
   options" e depois "Instructions", cole o conteúdo de `instrucoes.md`.
   Acrescente os arquivos de `conhecimento/` como arquivos de
   referência. O registro do projeto fica no caderno, como mais um
   arquivo de referência, que você troca quando ele muda.
2. Um agente, como descrito acima, quando a sua conta mostra "New
   agent".
3. A conversa comum. Anexe os arquivos de `conhecimento/` e o registro
   do projeto, e cole o conteúdo de `instrucoes.md` como primeira
   mensagem. Se o Copilot recusar o texto pelo tamanho, anexe
   `instrucoes.md` salvo como `.txt` e escreva: "Siga as instruções do
   arquivo anexado em toda esta conversa". Repita em cada conversa nova.

O Copilot no navegador aceita anexos em `.txt`, `.md`, `.docx` e `.pdf`,
entre outros formatos. A documentação da Microsoft não diz quantos
arquivos cabem por conversa nem o tamanho máximo da mensagem. Se o
limite não comportar todos os arquivos, envie nesta ordem: `5-projeto`,
`1-procedimentos`, `2-metodo-e-texto`, o pacote do tipo de projeto,
`4-modelos` e `3-formatos-e-visual`.

Sem instalação não há Python: as checagens, as contas de prazo e a
revisão são feitas pelo agente, à mão, e ele diz isso no relatório. As
atas entram como anexo da conversa. No fim de cada conversa, peça o
registro atualizado e salve no OneDrive ou no caderno.

## Trazer o trabalho de volta

No fim de cada conversa, o agente entrega o registro do projeto
atualizado. Guarde-o nos arquivos do projeto naquele ambiente, no lugar
da versão anterior. Para voltar ao Claude Code, entregue o registro ao
agente: a skill `usar-outro-ambiente` leva cada parte ao arquivo certo,
sem apagar o que já estava registrado.

## Para quem mantém o kit

Os arquivos de `conhecimento/` são gerados a partir do método, das
skills, das listas e dos pacotes. Depois de mudar qualquer um deles,
rode `python3 entregaveis/_harness/scripts/empacotar.py` e grave o
resultado. O teste do kit acusa o arquivo fora de dia.
