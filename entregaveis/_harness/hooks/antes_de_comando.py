#!/usr/bin/env python3
"""Hook de antes de um comando: material de cliente não vai para repositório público.

Olha só os comandos que tiram o projeto da máquina ou mudam quem pode
lê-lo: `git push` e a criação ou edição de repositório como público.
Com conteúdo de projeto na pasta, o envio só passa para um remoto
privado. É a terceira trava do harness, ao lado das duas da ordem de
trabalho.
"""
from __future__ import annotations

import re
import sys

import _base
import repositorio

ENVIO = re.compile(r"\bgit\b[^|;&\n]*\bpush\b")
TORNAR_PUBLICO = re.compile(r"\bgh\s+repo\s+(?:create|edit)\b[^|;&\n]*(?:--public\b|--visibility[= ]+public\b)")


def principal() -> int:
    dados = _base.entrada()
    comando = str((dados.get("tool_input") or {}).get("command", ""))
    envio = ENVIO.search(comando)
    publico = TORNAR_PUBLICO.search(comando)
    if not (envio or publico) or not repositorio.tem_projeto():
        return 0
    if publico:
        print(
            "Bloqueado pelo harness: este projeto tem material de cliente e o comando cria ou torna um repositório público. "
            "Um projeto de cliente só fica em git local ou em repositório privado. Use --private.",
            file=sys.stderr,
        )
        return 2
    geral, linhas = repositorio.situacao(usar_memoria=False)
    if repositorio.aceita(geral):
        return 0
    print("Bloqueado pelo harness: " + repositorio.explicar(geral, linhas), file=sys.stderr)
    return 2


if __name__ == "__main__":
    _base.protegido(principal)
