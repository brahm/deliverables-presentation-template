#!/usr/bin/env python3
"""Cria os registros do projeto e as pastas de entregável a partir dos modelos.

Uso:
    preparar.py                          cria _projeto/, _intake/, _dominio/, _atas/ e _cerebro/ se faltarem
    preparar.py --entregavel ID [opções] cria a pasta de um entregável
    preparar.py --pacote NOME            ativa um pacote de tipo de projeto

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


# Registros de configuração: uma linha por sinal ou pergunta. Uma versão nova do kit pode trazer linhas novas.
CHAVES = {"cadencias.tsv": "sinal", "perguntas.tsv": "pergunta"}


def completar_registros() -> list[str]:
    """Leva a um registro que já existe as colunas e as linhas de configuração que uma versão nova do kit trouxe.

    As colunas novas entram no fim do cabeçalho. Nenhuma linha do projeto é alterada.
    """
    feitos = []
    for modelo in sorted((comum.MODELOS / "projeto").glob("*.tsv")):
        alvo = comum.PROJETO / modelo.name
        do_modelo = [l for l in comum.ler(modelo).splitlines() if l.strip() and not l.startswith("#")]
        linhas = comum.ler(alvo).splitlines()
        posicao = next((i for i, l in enumerate(linhas) if l.strip() and not l.startswith("#")), None)
        if posicao is None or not do_modelo:
            continue
        colunas_do_modelo = [c.strip() for c in do_modelo[0].split("\t")]
        colunas = [c.strip() for c in linhas[posicao].split("\t")]
        novas = [c for c in colunas_do_modelo if c not in colunas]
        if novas:
            linhas[posicao] = "\t".join(colunas + novas)
            colunas += novas
            feitos.append(f"{comum.relativo(alvo)} (colunas novas: {', '.join(novas)})")
        chave = CHAVES.get(modelo.name)
        if chave in colunas:
            presentes = {(l.split("\t") + [""] * len(colunas))[colunas.index(chave)].strip() for l in linhas[posicao + 1:] if l.strip() and not l.startswith("#")}
            acrescidas = []
            for linha in do_modelo[1:]:
                valores = dict(zip(colunas_do_modelo, linha.split("\t")))
                if valores.get(chave, "") not in presentes:
                    acrescidas.append("\t".join(valores.get(c, "") for c in colunas))
            if acrescidas:
                linhas += acrescidas
                feitos.append(f"{comum.relativo(alvo)} ({len(acrescidas)} linha(s) nova(s))")
        if any(f.startswith(comum.relativo(alvo) + " ") for f in feitos):
            alvo.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return feitos


def preparar_projeto() -> list[str]:
    criados = copiar_modelos(comum.MODELOS / "projeto", comum.PROJETO)
    criados += completar_registros()
    criados += copiar_modelos(comum.MODELOS / "intake", comum.INTAKE)
    criados += copiar_modelos(comum.MODELOS / "dominio", comum.BASE / "_dominio")
    materiais = comum.INTAKE / "materiais"
    if not materiais.exists():
        materiais.mkdir(parents=True)
        (materiais / ".gitkeep").write_text("", encoding="utf-8")
    # As atas e a pasta de entrada ficam fora do git, como o material recebido.
    criados += copiar_modelos(comum.MODELOS / "atas", comum.BASE / "_atas")
    entrada = comum.INTAKE / "entrada"
    if not entrada.exists():
        entrada.mkdir(parents=True)
        (entrada / ".gitkeep").write_text("", encoding="utf-8")
    # O segundo cérebro nasce vazio, com as quatro pastas e o índice.
    import cerebro
    criados += copiar_modelos(comum.MODELOS / "cerebro", cerebro.PASTA)
    if cerebro.refazer_indice():
        criados.append(comum.relativo(cerebro.INDICE))
    return criados


def preparar_entregavel(ident: str, campos: dict) -> list[str]:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,48}", ident):
        raise SystemExit("O id do entregável usa letras minúsculas, números e hífen, e não começa por '_'.")
    pasta = comum.BASE / ident
    criados = copiar_modelos(comum.MODELOS / "entregavel", pasta)
    briefing = pasta / "briefing.md"
    texto = briefing.read_text(encoding="utf-8")
    campos = {"id": ident, **{k: v for k, v in campos.items() if v}}
    if comum.relativo(briefing) in criados:
        campos["fase"] = str(comum.fase_atual())  # a fase em que o entregável nasce, e que não muda sozinha
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


def bases_de_interativo() -> list[str]:
    return sorted(a.stem for a in (comum.MODELOS / "interativos").glob("*.html"))


def preparar_interativo(ident: str, nome: str, base: str) -> list[str]:
    """Copia um modelo de HTML interativo para a pasta do entregável."""
    pasta = comum.BASE / ident
    if not (pasta / "briefing.md").is_file():
        raise SystemExit(f"O entregável '{ident}' não existe. Crie-o antes com --entregavel.")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,48}", nome):
        raise SystemExit("O nome da peça usa letras minúsculas, números e hífen.")
    if base not in bases_de_interativo():
        raise SystemExit(f"Modelo '{base}' não existe. Modelos: {', '.join(bases_de_interativo())}.")
    faltas = comum.briefing_completo(pasta)
    if faltas:
        raise SystemExit("A peça espera o briefing completo. Falta: " + ", ".join(faltas) + ".")
    if not comum.storyline_aprovada(pasta):
        raise SystemExit("A peça espera a storyline aprovada pelo consultor (aprovada: sim em storyline.md).")
    destino = pasta / "interativos" / f"{nome}.html"
    if destino.exists():
        return []
    texto = (comum.MODELOS / "interativos" / f"{base}.html").read_text(encoding="utf-8")
    meta, _ = comum.cabecalho(comum.ler(pasta / "briefing.md"))
    idiomas = [i.strip() for i in meta.get("idiomas", "").split(",") if i.strip() and comum.MARCA not in i]
    if idiomas:
        texto = texto.replace("idioma: pt-BR", f"idioma: {idiomas[0]}", 1)
        texto = texto.replace('<html lang="pt-BR">', f'<html lang="{idiomas[0]}">', 1)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(texto, encoding="utf-8")
    return [comum.relativo(destino)]


def pacotes_disponiveis() -> list[str]:
    pasta = comum.HARNESS / "pacotes"
    return sorted(p.name for p in pasta.iterdir() if (p / "PACOTE.md").is_file()) if pasta.is_dir() else []


def ativar_pacote(nome: str) -> list[str]:
    """Liga um pacote ao projeto: a skill, os termos e o campo do brief."""
    pasta = comum.HARNESS / "pacotes" / nome
    if not (pasta / "PACOTE.md").is_file():
        disponiveis = ", ".join(pacotes_disponiveis()) or "nenhum"
        raise SystemExit(f"Não existe o pacote '{nome}'. Disponíveis: {disponiveis}.")
    feitos = []
    origem = pasta / "skill" / "SKILL.md"
    alvo = comum.RAIZ / ".claude" / "skills" / f"pacote-{nome}" / "SKILL.md"
    if origem.is_file() and not alvo.exists():
        alvo.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(origem, alvo)
        feitos.append(comum.relativo(alvo))
    # Os termos do pacote entram no glossário do projeto, sem repetir os que já estão lá.
    glossario = comum.PROJETO / "glossario.tsv"
    presentes = {(l.get("termo", "").lower(), l.get("idioma", "")) for l in comum.ler_tsv(glossario)}
    novos = []
    for linha in comum.ler(pasta / "glossario.tsv").splitlines():
        partes = linha.split("\t")
        if not linha.strip() or linha.startswith("#") or partes[0] == "termo":
            continue
        if (partes[0].lower(), partes[3] if len(partes) > 3 else "") not in presentes:
            novos.append(linha)
    if novos and glossario.is_file():
        texto = glossario.read_text(encoding="utf-8")
        glossario.write_text(texto + ("" if texto.endswith("\n") else "\n") + "\n".join(novos) + "\n", encoding="utf-8")
        feitos.append(f"{comum.relativo(glossario)} ({len(novos)} termos do pacote)")
    brief = comum.PROJETO / "brief.md"
    texto = comum.ler(brief)
    campo = re.search(r"^pacotes:[ \t]*(.*)$", texto, flags=re.MULTILINE)
    if campo is not None:
        ativos = [a.strip() for a in campo.group(1).split(",") if a.strip()]
        if nome not in ativos:
            ativos.append(nome)
            brief.write_text(texto[:campo.start()] + "pacotes: " + ", ".join(ativos) + texto[campo.end():], encoding="utf-8")
            feitos.append(f"{comum.relativo(brief)} (campo pacotes)")
    return feitos


def main() -> int:
    analisador = argparse.ArgumentParser(description="Cria registros e pastas a partir dos modelos.")
    analisador.add_argument("--entregavel", metavar="ID")
    analisador.add_argument("--titulo", default="")
    analisador.add_argument("--tipo", default="", help="apresentacao, documento, proposta, planilha ou treinamento")
    analisador.add_argument("--veiculo", default="", help="projetado, leitura, documento, planilha ou workshop")
    analisador.add_argument("--formato", default="", help="pptx, docx, pdf, xlsx ou html")
    analisador.add_argument("--idiomas", default="", help="por exemplo: pt-BR, es")
    analisador.add_argument("--pacote", metavar="NOME", help="ativa um pacote de tipo de projeto")
    analisador.add_argument("--interativo", metavar="NOME", help="cria um HTML interativo no entregável indicado")
    analisador.add_argument("--base", default="fluxo", help="modelo do HTML interativo: fluxo, camadas-3d ou simulador")
    args = analisador.parse_args()

    criados = preparar_projeto()
    if args.interativo and not args.entregavel:
        raise SystemExit("Diga em que entregável a peça entra: --entregavel ID --interativo NOME.")
    if args.entregavel and not (args.interativo and (comum.BASE / args.entregavel / "briefing.md").is_file()):
        criados += preparar_entregavel(args.entregavel, {
            "titulo": args.titulo, "tipo": args.tipo, "veiculo": args.veiculo,
            "formato": args.formato, "idiomas": args.idiomas,
        })
    if args.interativo:
        criados += preparar_interativo(args.entregavel, args.interativo, args.base)
    if args.pacote:
        criados += ativar_pacote(args.pacote)
        print(f"Pacote '{args.pacote}' ativo. Leia {comum.relativo(comum.HARNESS / 'pacotes' / args.pacote / 'PACOTE.md')}.")
    if criados:
        print("Criados ou alterados:")
        for nome in criados:
            print(f"  {nome}")
    else:
        print("Nada a criar: os arquivos já existem.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
