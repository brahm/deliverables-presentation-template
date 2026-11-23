#!/usr/bin/env python3
"""Hook de depois da gravação: roda as checagens rápidas no arquivo gravado.

É o que aplica as práticas de texto de forma automática: o agente recebe
os achados logo depois de escrever e corrige antes de seguir. Erros voltam
pela saída de erro com código 2. Avisos voltam como contexto, sem barrar.
"""
from __future__ import annotations

import json
import sys

import _base
import comum
import dominio
import validar


def principal() -> int:
    dados = _base.entrada()
    arquivo = _base.arquivo_da_ferramenta(dados)
    if arquivo is None:
        return 0
    if arquivo.parent == comum.BASE / "_dominio" and arquivo.suffix in (".tsv", ".py"):
        defeitos = dominio.testar()
        if defeitos:
            linhas = [a.formatar() for a in defeitos[:15]]
            print("Regras do domínio do projeto. Corrija a regra ou o caso antes de seguir:\n" + "\n".join(linhas), file=sys.stderr)
            return 2
        return 0
    if arquivo.suffix not in (".md", ".html"):
        return 0
    pasta = _base.entregavel_do_arquivo(arquivo)
    if pasta is None:
        return 0
    if _base.e_conteudo(arquivo, pasta) and dados.get("session_id"):
        sessao = _base.ler_sessao(dados["session_id"])
        if pasta.name not in sessao["alterados"]:
            sessao["alterados"].append(pasta.name)
            _base.gravar_sessao(dados["session_id"], sessao)
    achados = validar.validar_arquivo(arquivo)
    erros = [a for a in achados if a.nivel == "erro"]
    avisos = [a for a in achados if a.nivel != "erro"]
    if erros:
        linhas = [a.formatar() for a in erros[:15]]
        if len(erros) > 15:
            linhas.append(f"... e mais {len(erros) - 15} erro(s).")
        print("Checagens do harness neste arquivo. Corrija antes de seguir:\n" + "\n".join(linhas), file=sys.stderr)
        return 2
    if avisos:
        texto = "Avisos do harness neste arquivo (corrija os que fizerem sentido):\n" + "\n".join(a.formatar() for a in avisos[:10])
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": texto}}))
    return 0


if __name__ == "__main__":
    _base.protegido(principal)
