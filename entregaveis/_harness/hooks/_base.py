#!/usr/bin/env python3
"""Apoio comum aos hooks do Claude Code.

Cada hook recebe um JSON pela entrada padrão e responde pelo código de
saída: 0 deixa seguir, 2 bloqueia e mostra ao agente o que foi escrito na
saída de erro. Um hook que falha por defeito próprio avisa o agente. Só
as duas travas, a de comando e a de gravação, barram nesse caso: o que
elas não conseguiram conferir não passa.
"""
from __future__ import annotations

import json
import sys
import time
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


def area_de_projeto(arquivo: Path) -> bool:
    """Diz se o arquivo é registro, material, domínio ou entregável do projeto."""
    try:
        partes = arquivo.relative_to(comum.BASE).parts
    except ValueError:
        return False
    if not partes or partes[0] == "_harness" or partes[0].startswith("."):
        return False
    if partes[0] in ("_projeto", "_intake", "_dominio", "_atas", "_cerebro"):
        return True
    return arquivo.name == "briefing.md" or (comum.BASE / partes[0] / "briefing.md").is_file()


def e_conteudo(arquivo: Path, pasta: Path) -> bool:
    """Diz se o arquivo é o corpo do entregável ou um arquivo de saída."""
    relativo = arquivo.relative_to(pasta).parts
    if relativo[0] in ("saida", "paginas", "interativos"):
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


def limpar_sessoes(dias: int = 30) -> None:
    """Apaga os arquivos de sessão que ninguém toca há mais de um mês. A memória do repositório fica."""
    limite = time.time() - dias * 86400
    try:
        for arquivo in ESTADO.glob("*.json"):
            if arquivo.name != "repositorio.json" and arquivo.stat().st_mtime < limite:
                arquivo.unlink()
    except OSError:
        pass


def protegido(funcao, ao_falhar: str = "seguir"):
    """Roda o hook e decide o que fazer quando o próprio hook quebra.

    'seguir' deixa o trabalho correr: é o caso do hook de fim de turno, em
    que barrar prenderia o agente. 'contexto' também deixa correr e põe o
    aviso na saída padrão, que os hooks de sessão e de mensagem levam ao
    agente. 'avisar' devolve o defeito ao agente depois de uma gravação
    que já aconteceu. 'bloquear' é o das travas: o que a trava não
    conseguiu conferir não passa, porque liberar em silêncio é o mesmo que
    não ter a trava.
    """
    try:
        sys.exit(funcao() or 0)
    except SystemExit as saida:
        if saida.code is None or isinstance(saida.code, int):
            raise
        erro = str(saida.code)  # um script parou com uma mensagem
    except Exception as falha:  # noqa: BLE001 - o defeito do hook é tratado aqui
        erro = f"{type(falha).__name__}: {falha}"
    if ao_falhar == "bloquear":
        print(
            f"Bloqueado pelo harness: a trava não conseguiu conferir este passo ({erro}). "
            "O que não foi conferido não passa. Corrija o arquivo que a mensagem aponta, ou rode "
            f"'python3 {comum.relativo(comum.HARNESS / 'scripts' / 'ambiente.py')}' e conte ao consultor o que apareceu.",
            file=sys.stderr,
        )
        sys.exit(2)
    if ao_falhar == "avisar":
        print(
            f"O hook do harness falhou e as checagens desta gravação não rodaram ({erro}). "
            f"Rode 'python3 {comum.relativo(comum.HARNESS / 'scripts' / 'validar.py')}' e corrija o que a mensagem aponta.",
            file=sys.stderr,
        )
        sys.exit(2)
    aviso = f"Harness de entregáveis: um hook falhou e foi ignorado ({erro}). Rode 'python3 {comum.relativo(comum.HARNESS / 'scripts' / 'ambiente.py')}'."
    print(aviso, file=sys.stdout if ao_falhar == "contexto" else sys.stderr)
    sys.exit(0)
