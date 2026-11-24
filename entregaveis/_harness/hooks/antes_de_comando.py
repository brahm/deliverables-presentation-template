#!/usr/bin/env python3
"""Hook de antes de um comando: material de cliente não vai para repositório público.

Olha só os comandos que tiram o projeto da máquina ou mudam quem pode
lê-lo: `git push` e a criação ou edição de repositório como público ou
interno. Com conteúdo de projeto na pasta, o envio só passa quando todo
destino é privado: os remotos configurados, o endereço de envio de cada
um e o endereço escrito no próprio comando. É a terceira trava do
harness, ao lado das duas da ordem de trabalho.

A trava ouve os comandos de terminal. O envio por outra ferramenta, como
um conector de GitHub, não passa por aqui.
"""
from __future__ import annotations

import re
import sys

import _base
import repositorio

ENVIO = re.compile(r"\bgit\b[^|;&\n]*\bpush\b")
ABRIR = re.compile(
    r"\bgh\s+repo\s+(?:create|edit)\b[^|;&\n]*(?:--(public|internal)\b|--visibility[= ]+(public|internal)\b)"
    r"|\bgh\s+api\b[^|;&\n]*\b(?:private=(false)|visibility=(public|internal))\b"
)


def principal() -> int:
    dados = _base.entrada()
    comando = str((dados.get("tool_input") or {}).get("command", ""))
    envio = ENVIO.search(comando)
    abrir = ABRIR.search(comando)
    if not (envio or abrir) or not repositorio.tem_projeto():
        return 0
    if abrir:
        interno = "internal" in abrir.groups()
        print(
            "Bloqueado pelo harness: este projeto tem material de cliente e o comando cria ou torna um repositório "
            + ("interno, que toda a organização lê. " if interno else "público. ")
            + "Um projeto de cliente só fica em git local ou em repositório privado. Use --private.",
            file=sys.stderr,
        )
        return 2
    geral, linhas = repositorio.situacao(usar_memoria=False, outros=repositorio.destinos_do_comando(comando))
    if repositorio.aceita(geral):
        return 0
    print("Bloqueado pelo harness: " + repositorio.explicar(geral, linhas), file=sys.stderr)
    return 2


if __name__ == "__main__":
    _base.protegido(principal, ao_falhar="bloquear")
