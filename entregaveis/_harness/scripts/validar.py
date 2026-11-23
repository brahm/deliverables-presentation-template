#!/usr/bin/env python3
"""Roda as checagens do harness e diz o que reprova.

Uso:
    validar.py                    todas as checagens, em todos os entregáveis
    validar.py ID [ID...]         só os entregáveis citados
    validar.py --so texto,termos  só as checagens citadas
    validar.py --arquivo CAMINHO  só os achados daquele arquivo (usado pelo hook)
    validar.py --rigoroso         trata o material como pronto para revisão
    validar.py --carimbar ID      registra a revisão da versão atual do conteúdo

Sai com código 1 quando há algum erro. Avisos não reprovam.
"""
from __future__ import annotations

import argparse
import datetime
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import checagens  # noqa: E402
import comum  # noqa: E402
from comum import Achado  # noqa: E402


def validar(pastas: list[Path], so: set[str] | None = None, rigoroso: bool = False, gerais: bool = True) -> list[Achado]:
    achados: list[Achado] = []
    if gerais and (not so or "projeto" in so):
        achados.extend(checagens.projeto())
    if gerais and (not so or "intake" in so):
        achados.extend(checagens.intake())
    if gerais and (not so or "confidencialidade" in so):
        achados.extend(checagens.materiais_fora_do_git())
    if gerais and (not so or "repositorio" in so):
        achados.extend(checagens.repositorio_do_projeto())
    if gerais and (not so or "prazos" in so):
        achados.extend(checagens.prazos())
    if gerais and (not so or "governanca" in so):
        achados.extend(checagens.governanca_do_projeto())
    if gerais and (not so or "dominio" in so):
        achados.extend(checagens.dominio_do_projeto())
    for pasta in pastas:
        for nome, funcao in checagens.POR_ENTREGAVEL.items():
            if so and nome not in so:
                continue
            achados.extend(funcao(pasta, rigoroso))
    return achados


def validar_arquivo(arquivo: Path) -> list[Achado]:
    """Achados que dizem respeito a um arquivo de um entregável."""
    arquivo = arquivo.resolve()
    try:
        partes = arquivo.relative_to(comum.BASE).parts
    except ValueError:
        return []
    if len(partes) < 2 or partes[0].startswith(("_", ".")):
        return []
    pasta = comum.BASE / partes[0]
    if not (pasta / "briefing.md").is_file():
        return []
    alvo = comum.relativo(arquivo)
    return [a for a in validar([pasta], gerais=False) if a.arquivo == alvo]


def carimbar(pasta: Path) -> int:
    """Grava em revisao.md qual versão do conteúdo foi revisada."""
    erros = [a for a in validar([pasta], rigoroso=True, gerais=False) if a.nivel == "erro"]
    if erros:
        for a in erros:
            print(a.formatar())
        print(f"\nRevisão não registrada: {len(erros)} erro(s) nas checagens. Corrija e rode de novo.")
        return 1
    arquivo = pasta / "revisao.md"
    texto = comum.ler(arquivo)
    if not texto or comum.MARCA in texto:
        print(f"Revisão não registrada: {comum.relativo(arquivo)} não existe ou ainda tem {comum.MARCA}. Preencha a rubrica primeiro.")
        return 1
    meta, corpo = comum.cabecalho(texto)
    meta["conteudo_revisado"] = comum.carimbo(pasta)
    meta["revisado_em"] = datetime.date.today().isoformat()
    linhas = ["---"] + [f"{k}: {v}" for k, v in meta.items()] + ["---"]
    arquivo.write_text("\n".join(linhas) + "\n" + corpo.lstrip("\n") + ("" if corpo.endswith("\n") else "\n"), encoding="utf-8")
    print(f"Revisão registrada para {pasta.name} (conteúdo {meta['conteudo_revisado']}).")
    return 0


def revisao_em_dia(pasta: Path) -> bool:
    meta, _ = comum.cabecalho(comum.ler(pasta / "revisao.md"))
    return bool(meta.get("conteudo_revisado")) and meta.get("conteudo_revisado") == comum.carimbo(pasta)


def main() -> int:
    analisador = argparse.ArgumentParser(description="Checagens do harness de entregáveis.")
    analisador.add_argument("ids", nargs="*", help="entregáveis a validar (padrão: todos)")
    analisador.add_argument("--so", default="", help="checagens separadas por vírgula")
    analisador.add_argument("--arquivo", help="mostra só os achados deste arquivo")
    analisador.add_argument("--rigoroso", action="store_true", help="marcas esquecidas e faltas viram erro")
    analisador.add_argument("--carimbar", metavar="ID", help="registra a revisão da versão atual")
    analisador.add_argument("--sem-avisos", action="store_true", help="mostra só os erros")
    args = analisador.parse_args()

    if args.carimbar:
        pasta = comum.BASE / args.carimbar
        if not (pasta / "briefing.md").is_file():
            print(f"Não existe o entregável '{args.carimbar}'.")
            return 2
        return carimbar(pasta)

    if args.arquivo:
        achados = validar_arquivo(Path(args.arquivo))
    else:
        todas = comum.entregaveis()
        pastas = [p for p in todas if not args.ids or p.name in args.ids]
        desconhecidos = set(args.ids) - {p.name for p in todas}
        if desconhecidos:
            print(f"Entregável não encontrado: {', '.join(sorted(desconhecidos))}.")
            return 2
        so = {s.strip() for s in re.split(r"[,\s]+", args.so) if s.strip()} or None
        achados = validar(pastas, so, args.rigoroso, gerais=not args.ids)

    erros = [a for a in achados if a.nivel == "erro"]
    avisos = [a for a in achados if a.nivel != "erro"]
    for a in erros + ([] if args.sem_avisos else avisos):
        print(a.formatar())
    if erros:
        print(f"\n{len(erros)} erro(s) e {len(avisos)} aviso(s).")
        return 1
    print(f"Nenhum erro. {len(avisos)} aviso(s)." if avisos else "Nenhum erro e nenhum aviso.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
