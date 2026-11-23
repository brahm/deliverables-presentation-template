#!/usr/bin/env python3
"""Apoio comum aos hooks do Claude Code.

Cada hook recebe um JSON pela entrada padrão e responde pelo código de
saída: 0 deixa seguir, 2 bloqueia e mostra ao agente o que foi escrito na
saída de erro. Um hook que falha por defeito próprio sai com 0, para
nunca travar o trabalho do dono por causa do harness.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import comum  # noqa: E402

ESTADO = comum.HARNESS / ".estado"

ARQUIVOS_PROTEGIDOS = ("conteudo", "documento", "planilha")


def entrada() -> dict:
    try:
        return json.load(sys.stdin)
    except (ValueError, OSError):
        return {}


def arquivo_da_ferramenta(dados: dict) -> Path | None:
    """Caminho do arquivo que a ferramenta grava, quando há um."""
    parametros = dados.get("tool_input") or {}
    caminho = parametros.get("file_path") or parametros.get("notebook_path")
    if not caminho:
        return None
    caminho = Path(caminho)
    if not caminho.is_absolute():
        caminho = Path(dados.get("cwd") or ".") / caminho
    return caminho.resolve()


def entregavel_do_arquivo(arquivo: Path) -> Path | None:
    """Pasta do entregável a que o arquivo pertence, ou None."""
    try:
        partes = arquivo.relative_to(comum.BASE).parts
    except ValueError:
        return None
    if len(partes) < 2 or partes[0].startswith(("_", ".")):
        return None
    return comum.BASE / partes[0]


def e_conteudo(arquivo: Path, pasta: Path) -> bool:
    """Diz se o arquivo é o corpo do entregável ou um arquivo de saída."""
    relativo = arquivo.relative_to(pasta).parts
    if relativo[0] in ("saida", "paginas"):
        return True
    return len(relativo) == 1 and arquivo.name.startswith(ARQUIVOS_PROTEGIDOS) and arquivo.suffix == ".md"


def ler_sessao(sessao: str) -> dict:
    try:
        return json.loads((ESTADO / f"{sessao}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"alterados": [], "avisados": {}}


def gravar_sessao(sessao: str, dados: dict) -> None:
    try:
        ESTADO.mkdir(exist_ok=True)
        (ESTADO / f"{sessao}.json").write_text(json.dumps(dados), encoding="utf-8")
    except OSError:
        pass


def protegido(funcao):
    """Roda o hook e garante saída 0 se o próprio hook quebrar."""
    try:
        sys.exit(funcao() or 0)
    except SystemExit:
        raise
    except Exception as erro:  # noqa: BLE001 - o hook nunca deve travar o trabalho
        print(f"(hook do harness falhou e foi ignorado: {erro})", file=sys.stderr)
        sys.exit(0)
