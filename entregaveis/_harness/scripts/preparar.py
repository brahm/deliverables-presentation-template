#!/usr/bin/env python3
"""Cria os registros do projeto e as pastas de entregável a partir dos modelos.

Uso:
    preparar.py                          cria _projeto/ e _intake/ se faltarem
    preparar.py --entregavel ID [opções] cria a pasta de um entregável

Nunca sobrescreve um arquivo que já existe.
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import comum  # noqa: E402


def copiar_modelos(origem: Path, destino: Path) -> list[str]:
    """Copia os arquivos do modelo que ainda não existem no destino."""
    criados = []
    for arquivo in sorted(origem.rglob("*")):
        if arquivo.is_dir():
            continue
        alvo = destino / arquivo.relative_to(origem)
        if alvo.exists():
            continue
        alvo.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(arquivo, alvo)
        criados.append(comum.relativo(alvo))
    return criados


def preparar_projeto() -> list[str]:
    criados = copiar_modelos(comum.MODELOS / "projeto", comum.PROJETO)
    criados += copiar_modelos(comum.MODELOS / "intake", comum.INTAKE)
    materiais = comum.INTAKE / "materiais"
    if not materiais.exists():
        materiais.mkdir(parents=True)
        (materiais / ".gitkeep").write_text("", encoding="utf-8")
    return criados


def preparar_entregavel(ident: str, campos: dict) -> list[str]:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,48}", ident):
        raise SystemExit("O id do entregável usa letras minúsculas, números e hífen, e não começa por '_'.")
    pasta = comum.BASE / ident
    criados = copiar_modelos(comum.MODELOS / "entregavel", pasta)
    briefing = pasta / "briefing.md"
    texto = briefing.read_text(encoding="utf-8")
    campos = {"id": ident, **{k: v for k, v in campos.items() if v}}
    for chave, valor in campos.items():
        texto = re.sub(rf"^{chave}:.*$", f"{chave}: {valor}", texto, count=1, flags=re.MULTILINE)
    briefing.write_text(texto, encoding="utf-8")
    tipo = comum.normalizar(campos.get("tipo", ""))
    veiculo = comum.normalizar(campos.get("veiculo", ""))
    # O modelo traz os dois corpos possíveis. Fica só o que serve ao tipo.
    if tipo == "planilha" or veiculo == "planilha":
        sobram = ["conteudo.md", "documento.md"]
    elif veiculo == "documento":
        sobram = ["conteudo.md", "planilha.md"]
    elif veiculo:
        sobram = ["documento.md", "planilha.md"]
    else:
        sobram = []
    for nome in sobram:
        arquivo = pasta / nome
        if arquivo.is_file() and comum.relativo(arquivo) in criados:
            arquivo.unlink()
            criados.remove(comum.relativo(arquivo))
    return criados


def main() -> int:
    analisador = argparse.ArgumentParser(description="Cria registros e pastas a partir dos modelos.")
    analisador.add_argument("--entregavel", metavar="ID")
    analisador.add_argument("--titulo", default="")
    analisador.add_argument("--tipo", default="", help="apresentacao, documento, proposta, planilha ou treinamento")
    analisador.add_argument("--veiculo", default="", help="projetado, leitura, documento, planilha ou workshop")
    analisador.add_argument("--formato", default="", help="pptx, docx, pdf ou xlsx")
    analisador.add_argument("--idiomas", default="", help="por exemplo: pt-BR, es")
    args = analisador.parse_args()

    criados = preparar_projeto()
    if args.entregavel:
        criados += preparar_entregavel(args.entregavel, {
            "titulo": args.titulo, "tipo": args.tipo, "veiculo": args.veiculo,
            "formato": args.formato, "idiomas": args.idiomas,
        })
    if criados:
        print("Criados:")
        for nome in criados:
            print(f"  {nome}")
    else:
        print("Nada a criar: os arquivos já existem.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
