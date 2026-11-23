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
  echo "O instalador precisa do Python 3.9 ou mais novo. Sem Python, siga a seção 'Sem Python' do INSTALL.md." >&2
  exit 2
fi
exec "$PY" "$AQUI/entregaveis/_harness/scripts/instalar.py" "$@"
