#!/bin/sh
# Instala o harness de entregáveis em um projeto. Veja INSTALL.md.
# Uso: sh install.sh --destino /caminho/do/projeto [--pasta NOME] [--simular] [--atualizar] [--ci]
set -e
AQUI="$(cd "$(dirname "$0")" && pwd)"
if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  echo "O instalador precisa do Python 3.9 ou mais novo, e não achou python3 nem python nesta máquina." >&2
  echo "Instale o Python: no Windows, pela Microsoft Store; no macOS, com 'brew install python' ou pelo instalador de python.org; no Linux, com 'sudo apt install python3'." >&2
  echo "Se nada pode ser instalado aqui, siga a seção 'Sem Python' do INSTALL.md." >&2
  exit 2
fi
exec "$PY" "$AQUI/entregaveis/_harness/scripts/instalar.py" "$@"
