#!/usr/bin/env python3
"""Levanta o que já existe em um projeto em andamento.

A skill adotar-projeto roda este script antes de perguntar qualquer coisa
ao consultor. Ele não supõe nada sobre o projeto: pode ser um repositório de
código, uma pasta só com apresentações ou um projeto que já usa outro
conjunto de regras para agentes.

Uso:
    levantar.py                    resumo do que existe no projeto
    levantar.py --titulos ARQ.pptx títulos e volume de texto de cada slide
"""
from __future__ import annotations

import argparse
import html
import os
import re
import subprocess
import sys
import zipfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import comum  # noqa: E402

IGNORAR = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".idea", ".vscode", "target"}

GRUPOS = {
    "Apresentações": {".pptx", ".ppt", ".key", ".odp"},
    "Documentos": {".docx", ".doc", ".pdf", ".odt"},
    "Planilhas e dados": {".xlsx", ".xls", ".csv", ".tsv", ".parquet", ".json"},
    "Modelos de arquivo": {".potx", ".dotx", ".xltx", ".thmx"},
    "Imagens": {".png", ".jpg", ".jpeg", ".svg", ".ai", ".psd"},
    "Texto e Markdown": {".md", ".txt"},
}

PISTAS = {
    "Possíveis modelos": r"template|modelo|plantilla|master|\.potx$|\.dotx$|\.xltx$",
    "Possíveis guias de marca": r"brand|marca|guideline|identidade|style.?guide|manual.?de|logo",
    "Possíveis escopos e propostas": r"sow|escopo|proposta|propuesta|proposal|contrato|statement.?of.?work",
    "Possíveis regras de confidencialidade": r"confidenc|nda|sigilo|classifica|data.?handling|lgpd|gdpr",
    "Possíveis pedidos de dados": r"data.?request|pedido.?de.?dados|solicitud.?de.?datos|drl",
    "Possíveis bases de conhecimento": r"wiki|second.?brain|segundo.?c[ée]rebro|zettel|knowledge|conhecimento|(?<![a-z])notas?(?![a-z])|(?<![a-z])notes?(?![a-z])|mem[oó]ria|memory",
    "Possíveis materiais de governança": r"status|(?<![a-z])atas?(?![a-z])|acta|minuta|cronograma|schedule|raci|riscos?(?![a-z])|risk|kick.?off|abertura|charter|steering|comit|plano.?d[eo].?projeto|aceite|change.?request|mudanca|mudança",
}

ARQUIVOS_DE_AGENTE = [
    "AGENTS.md", "CLAUDE.md", "GEMINI.md", ".github/copilot-instructions.md",
    ".cursor/rules", ".cursorrules", ".claude/settings.json", ".claude/skills",
    ".agents", ".codex", ".windsurfrules",
]


def arquivos(raiz: Path):
    for pasta, subpastas, nomes in os.walk(raiz):
        subpastas[:] = [s for s in subpastas if s not in IGNORAR and Path(pasta, s).resolve() != comum.HARNESS]
        for nome in nomes:
            yield Path(pasta, nome)


def alterado_em(arquivo: Path) -> float:
    """A data de alteração do arquivo. Um atalho quebrado ou um arquivo sem permissão fica por último."""
    try:
        return arquivo.stat().st_mtime
    except OSError:
        return 0.0


def resumo() -> None:
    raiz = comum.RAIZ
    todos = list(arquivos(raiz))
    print(f"Raiz do projeto: {raiz}")
    print(f"Arquivos: {len(todos)} | pastas de primeiro nível: {', '.join(sorted(p.name for p in raiz.iterdir() if p.is_dir() and p.name not in IGNORAR)) or 'nenhuma'}")

    try:
        git = subprocess.run(["git", "-C", str(raiz), "log", "-1", "--format=%ad | %s", "--date=short"], capture_output=True, text=True, timeout=20)
        print("Git: " + (git.stdout.strip() if git.returncode == 0 and git.stdout.strip() else "sem histórico ou sem repositório"))
    except (OSError, subprocess.SubprocessError):
        print("Git: não disponível")

    presentes = [a for a in ARQUIVOS_DE_AGENTE if (raiz / a).exists()]
    print("Instruções para agentes já existentes: " + (", ".join(presentes) if presentes else "nenhuma"))

    extensoes = Counter(a.suffix.lower() for a in todos)
    for grupo, exts in GRUPOS.items():
        do_grupo = sorted((a for a in todos if a.suffix.lower() in exts), key=alterado_em, reverse=True)
        if not do_grupo:
            continue
        print(f"\n{grupo}: {len(do_grupo)}")
        for a in do_grupo[:12]:
            print(f"  {a.relative_to(raiz)}")
        if len(do_grupo) > 12:
            print(f"  ... e mais {len(do_grupo) - 12}")

    for titulo, padrao in PISTAS.items():
        achados = [a for a in todos if re.search(padrao, a.name, flags=re.IGNORECASE)]
        if achados:
            print(f"\n{titulo}:")
            for a in achados[:10]:
                print(f"  {a.relative_to(raiz)}")

    outras = [(e, n) for e, n in extensoes.most_common(8) if e and not any(e in exts for exts in GRUPOS.values())]
    if outras:
        print("\nOutros tipos mais frequentes: " + ", ".join(f"{e} ({n})" for e, n in outras))
    print("\nOs nomes acima são pistas. Abra cada arquivo antes de registrar o que ele é.")


def titulos_de_pptx(caminho: Path) -> None:
    """Lê os títulos dos slides direto do arquivo, sem depender de pacotes."""
    with zipfile.ZipFile(caminho) as pacote:
        slides = sorted(
            (n for n in pacote.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)),
            key=lambda n: int(re.search(r"(\d+)\.xml$", n).group(1)),
        )
        print(f"{caminho.name}: {len(slides)} slides")
        for i, nome in enumerate(slides, start=1):
            xml = pacote.read(nome).decode("utf-8", errors="replace")
            titulo = ""
            for forma in re.findall(r"<p:sp>.*?</p:sp>", xml, flags=re.DOTALL):
                if re.search(r'<p:ph[^>]*type="(title|ctrTitle)"', forma):
                    titulo = " ".join(re.findall(r"<a:t>([^<]*)</a:t>", forma))
                    break
            palavras = len(re.findall(r"\w+", " ".join(re.findall(r"<a:t>([^<]*)</a:t>", xml))))
            print(f"{i:3}. [{palavras:3} palavras] {html.unescape(titulo) or '(sem título)'}")


def main() -> int:
    analisador = argparse.ArgumentParser(description="Levanta o que já existe no projeto.")
    analisador.add_argument("--titulos", metavar="ARQUIVO.pptx", help="lista os títulos de uma apresentação existente")
    args = analisador.parse_args()
    if args.titulos:
        titulos_de_pptx(Path(args.titulos))
    else:
        resumo()
    return 0


if __name__ == "__main__":
    sys.exit(main())
