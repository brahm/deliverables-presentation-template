#!/usr/bin/env python3
"""Hook de depois da gravação: roda as checagens rápidas no arquivo gravado.

É o que aplica as práticas de texto de forma automática: o agente recebe
os achados logo depois de escrever e corrige antes de seguir. Erros voltam
pela saída de erro com código 2. Avisos voltam como contexto, sem barrar.

É também um dos gatilhos do segundo cérebro: quando a gravação de um
registro, de um material ou de um entregável cria algo que nenhuma nota
guarda, o agente recebe o lembrete. Uma nota gravada é conferida na hora.
"""
from __future__ import annotations

import json
import sys

import _base
import cerebro
import comum
import dominio
import validar


def contexto(linhas: list[str]) -> None:
    if linhas:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "\n".join(linhas)}}))


def do_cerebro(dados: dict, arquivo) -> list[str]:
    """O que a gravação pede ao segundo cérebro: conferir a nota gravada, ou absorver o que o registro ganhou."""
    if not cerebro.PASTA.is_dir():
        return []
    if cerebro.PASTA.resolve() in arquivo.parents:
        if arquivo.suffix != ".md" or arquivo.parent.resolve() == cerebro.PASTA.resolve():
            return []
        achados = cerebro.conferir(arquivo)
        return ["Segundo cérebro, nesta nota (corrija antes de absorver):"] + [a.formatar() for a in achados[:8]] if achados else []
    if not _base.area_de_projeto(arquivo):
        return []
    sessao = _base.ler_sessao(dados.get("session_id") or "sem-sessao")
    vistos = set(sessao.get("cerebro_avisados", []))
    novos = [(f, s, n) for f, s, n in cerebro.pendentes() if f"{f.ident}:{f.marca}" not in vistos]
    if not novos:
        return []
    if dados.get("session_id"):
        sessao["cerebro_avisados"] = sorted(vistos | {f"{f.ident}:{f.marca}" for f, _, _ in novos})
        _base.gravar_sessao(dados["session_id"], sessao)
    nomes = ", ".join(f.ident for f, _, _ in novos[:6]) + ("..." if len(novos) > 6 else "")
    return [f"Segundo cérebro: {len(novos)} item(ns) a absorver ({nomes}). Antes de encerrar o turno, aplique a skill manter-cerebro (scripts/cerebro.py --pendentes)."]


def principal() -> int:
    dados = _base.entrada()
    arquivo = _base.arquivo_da_ferramenta(dados)
    if arquivo is None:
        return 0
    lembrete = do_cerebro(dados, arquivo)
    if arquivo.parent == comum.BASE / "_dominio" and arquivo.suffix in (".tsv", ".py"):
        defeitos = dominio.testar()
        if defeitos:
            linhas = [a.formatar() for a in defeitos[:15]]
            print("Regras do domínio do projeto. Corrija a regra ou o caso antes de seguir:\n" + "\n".join(linhas), file=sys.stderr)
            return 2
        contexto(lembrete)
        return 0
    pasta = _base.entregavel_do_arquivo(arquivo)
    if arquivo.suffix not in (".md", ".html") or pasta is None:
        contexto(lembrete)
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
        lembrete = ["Avisos do harness neste arquivo (corrija os que fizerem sentido):"] + [a.formatar() for a in avisos[:10]] + lembrete
    contexto(lembrete)
    return 0


if __name__ == "__main__":
    _base.protegido(principal, ao_falhar="avisar")
