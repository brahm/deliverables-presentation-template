#!/bin/sh
# Instala o harness de entregáveis em um projeto. Veja INSTALL.md.
#
# Em uma linha, dentro da pasta do projeto (Linux, macOS e Windows com WSL):
#   curl -fsSL https://raw.githubusercontent.com/brahm/deliverables-presentation-template/main/install.sh | sh
# Com opções:
#   curl -fsSL https://raw.githubusercontent.com/brahm/deliverables-presentation-template/main/install.sh | sh -s -- --simular
# A partir de uma cópia do kit:
#   sh install.sh --destino /caminho/do/projeto [--pasta NOME] [--simular] [--atualizar] [--ci]
#
# Variáveis de ambiente, todas opcionais e só para a instalação em uma linha:
#   HARNESS_REF      o ramo, a etiqueta ou o commit do kit (padrão: main)
#   HARNESS_REPO     o repositório do kit no GitHub, como DONO/NOME
#   HARNESS_ARQUIVO  um .tar.gz do kit já baixado, para instalar sem internet
#
# O corpo fica dentro de uma função chamada na última linha. Se o download
# for cortado no meio, o shell acusa erro de sintaxe e nada roda.
set -eu

REPO_PADRAO="brahm/deliverables-presentation-template"

erro() {
  printf '%s\n' "$@" >&2
}

achar_python() {
  for candidato in python3 python; do
    if command -v "$candidato" >/dev/null 2>&1 \
      && "$candidato" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' >/dev/null 2>&1; then
      printf '%s\n' "$candidato"
      return 0
    fi
  done
  return 1
}

sem_python() {
  erro "O instalador precisa do Python 3.9 ou mais novo, e não achou python3 nem python com essa versão nesta máquina." \
    "Instale o Python: no Windows com WSL e no Linux, com 'sudo apt install python3'; no macOS, com 'brew install python' ou pelo instalador de python.org." \
    "Se nada pode ser instalado aqui, siga a seção 'Sem Python' do INSTALL.md."
}

# Diz se as opções trazem --destino. Sem ela, o destino é a pasta atual.
tem_destino() {
  for opcao in "$@"; do
    case "$opcao" in
      --destino | --destino=*) return 0 ;;
    esac
  done
  return 1
}

baixar() {
  # $1: endereço. $2: arquivo de saída. Só HTTPS, inclusive nos redirecionamentos.
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL --proto '=https' --proto-redir '=https' --retry 2 -o "$2" "$1"
  elif command -v wget >/dev/null 2>&1; then
    wget -q --https-only -O "$2" "$1"
  else
    erro "O instalador precisa do curl ou do wget para baixar o kit."
    return 1
  fi
}

instalar_da_internet() {
  PY="$(achar_python)" || { sem_python; exit 2; }
  command -v tar >/dev/null 2>&1 || { erro "O instalador precisa do comando tar para abrir o kit."; exit 2; }

  repo="${HARNESS_REPO:-$REPO_PADRAO}"
  ref="${HARNESS_REF:-main}"
  arquivo="${HARNESS_ARQUIVO:-}"
  # O repositório e a referência entram em um endereço: só os caracteres de um nome do GitHub passam.
  case "$repo" in
    */*/* | /* | */ | *[!A-Za-z0-9._/-]* | *..*) erro "HARNESS_REPO precisa ter a forma DONO/NOME: $repo"; exit 2 ;;
    */*) ;;
    *) erro "HARNESS_REPO precisa ter a forma DONO/NOME: $repo"; exit 2 ;;
  esac
  case "$ref" in
    "" | -* | /* | *[!A-Za-z0-9._/-]* | *..*) erro "HARNESS_REF precisa ser um ramo, uma etiqueta ou um commit: $ref"; exit 2 ;;
  esac

  if ! tem_destino "$@"; then
    aqui="$(pwd -P)"
    casa="$(cd "${HOME:-/}" 2>/dev/null && pwd -P || printf '%s' "${HOME:-/}")"
    if [ "$aqui" = "/" ] || [ "$aqui" = "$casa" ]; then
      erro "Você está em $aqui, que não é a pasta de um projeto." \
        "Entre na pasta do projeto antes de rodar o comando, ou crie uma: mkdir meu-projeto && cd meu-projeto" \
        "Para instalar em outra pasta sem sair daqui, acrescente: | sh -s -- --destino /caminho/do/projeto"
      exit 2
    fi
  fi

  TEMP="$(mktemp -d "${TMPDIR:-/tmp}/harness-de-entregaveis.XXXXXX")"
  trap 'rm -rf "$TEMP"' EXIT
  trap 'exit 130' INT
  trap 'exit 143' TERM HUP

  if [ -n "$arquivo" ]; then
    [ -f "$arquivo" ] || { erro "HARNESS_ARQUIVO não é um arquivo: $arquivo"; exit 2; }
    pacote="$arquivo"
    printf 'Abrindo o kit de %s\n' "$arquivo"
  else
    pacote="$TEMP/kit.tar.gz"
    endereco="https://codeload.github.com/$repo/tar.gz/$ref"
    printf 'Baixando o kit de https://github.com/%s (%s)\n' "$repo" "$ref"
    if ! baixar "$endereco" "$pacote"; then
      erro "Não deu para baixar o kit de $endereco" \
        "Confira a internet e se a referência '$ref' existe. O repositório do kit é público e não pede senha." \
        "Sem internet, baixe o ZIP do repositório, descompacte fora do projeto e rode: sh PASTA-DO-KIT/install.sh --destino ."
      exit 1
    fi
  fi

  mkdir "$TEMP/kit"
  if ! tar -xzf "$pacote" -C "$TEMP/kit" 2>/dev/null; then
    erro "O arquivo baixado não é um .tar.gz válido. Rode o comando de novo."
    exit 1
  fi
  # O pacote do GitHub traz uma pasta só, com o nome do repositório e da referência.
  raiz=""
  for pasta in "$TEMP/kit"/*/; do
    if [ -f "${pasta}entregaveis/_harness/scripts/instalar.py" ]; then
      raiz="${pasta%/}"
      break
    fi
  done
  if [ -z "$raiz" ]; then
    erro "O pacote baixado não traz o harness de entregáveis. Confira HARNESS_REPO e HARNESS_REF."
    exit 1
  fi
  printf 'Versão do kit: %s\n\n' "$(cat "$raiz/entregaveis/_harness/VERSAO" 2>/dev/null || printf '?')"

  # A entrada padrão é este script quando ele chega por um pipe. O instalador não lê dela.
  "$PY" "$raiz/entregaveis/_harness/scripts/instalar.py" "$@" </dev/null
}

principal() {
  # Rodando a partir de uma cópia do kit, o instalador é o que está ao lado deste arquivo.
  if [ -f "$0" ] && [ "$(basename "$0")" = "install.sh" ]; then
    AQUI="$(cd "$(dirname "$0")" && pwd)"
    if [ -f "$AQUI/entregaveis/_harness/scripts/instalar.py" ] && [ -f "$AQUI/entregaveis/_harness/VERSAO" ]; then
      PY="$(achar_python)" || { sem_python; exit 2; }
      exec "$PY" "$AQUI/entregaveis/_harness/scripts/instalar.py" "$@"
    fi
  fi
  instalar_da_internet "$@"
}

principal "$@"
