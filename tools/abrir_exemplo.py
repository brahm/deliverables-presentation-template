#!/usr/bin/env python3
"""Abre o projeto de exemplo em uma pasta nova, com o harness instalado.

Uso: python3 tools/abrir_exemplo.py DESTINO

Instala o harness em DESTINO, copia os registros e o entregável de
`exemplo/` por cima dos modelos e ativa os pacotes do brief. A pasta
resultante é um projeto completo, em que `estado.py`, `validar.py` e
`gerar.py` rodam. DESTINO precisa estar vazia ou não existir, e fica
fora deste repositório.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
EXEMPLO = RAIZ / "exemplo" / "entregaveis"
SCRIPTS = Path("entregaveis") / "_harness" / "scripts"


def rodar(args: list, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *map(str, args)], cwd=cwd, capture_output=True, text=True, timeout=180)


def abrir(destino: Path) -> int:
    destino = destino.resolve()
    if destino == RAIZ or RAIZ in destino.parents:
        print("Escolha uma pasta fora deste repositório. O exemplo aberto é um projeto à parte.")
        return 2
    if destino.exists() and any(destino.iterdir()):
        print(f"{destino} já tem arquivos. Escolha uma pasta vazia ou que ainda não existe.")
        return 2
    destino.mkdir(parents=True, exist_ok=True)
    instalacao = rodar([RAIZ / SCRIPTS / "instalar.py", "--destino", destino], RAIZ)
    if instalacao.returncode != 0:
        print(instalacao.stdout + instalacao.stderr)
        return 1
    shutil.copytree(EXEMPLO, destino / "entregaveis", dirs_exist_ok=True)
    brief = (destino / "entregaveis" / "_projeto" / "brief.md").read_text(encoding="utf-8")
    campo = re.search(r"^pacotes:[ \t]*(.*)$", brief, flags=re.MULTILINE)
    for pacote in [p.strip() for p in (campo.group(1) if campo else "").split(",") if p.strip()]:
        ativacao = rodar([SCRIPTS / "preparar.py", "--pacote", pacote], destino)
        if ativacao.returncode != 0:
            print(ativacao.stdout + ativacao.stderr)
            return 1
    print(f"Exemplo aberto em {destino}\n")
    print(rodar([SCRIPTS / "estado.py"], destino).stdout.rstrip())
    print("\nPara ver o arquivo final, rode dentro da pasta:")
    print("  python3 entregaveis/_harness/scripts/gerar.py leitura-executiva --pdf --imagens")
    return 0


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1].startswith("-"):
        print(__doc__.strip())
        return 2
    return abrir(Path(sys.argv[1]))


if __name__ == "__main__":
    sys.exit(main())
