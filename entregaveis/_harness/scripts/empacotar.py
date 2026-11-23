#!/usr/bin/env python3
"""Monta o pacote de instruções e de conhecimento para ambientes sem hooks nem scripts.

Uso:
    empacotar.py                  refaz os arquivos de conhecimento do kit, em _harness/ambientes/
    empacotar.py --conferir       diz se esses arquivos estão em dia com o método e as skills
    empacotar.py --projeto        monta o pacote deste projeto em entregaveis/_ambiente/
    empacotar.py --projeto --saida PASTA

O Claude desktop, o ChatGPT desktop e o Microsoft Copilot não rodam os
hooks nem os scripts do harness. Neles o método chega como um texto de
instruções, para colar, e poucos arquivos de conhecimento, para enviar.
Os arquivos saem em .txt porque é o formato que os três aceitam.

O pacote do projeto leva também o brief, a marca, o glossário, as
decisões, as evidências e o domínio. Isso é material do projeto saindo
para outro ambiente: quem decide é o consultor, pelas regras de material.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import comum  # noqa: E402

AMBIENTES = comum.HARNESS / "ambientes"
CONHECIMENTO = AMBIENTES / "conhecimento"
INSTRUCOES = AMBIENTES / "instrucoes.md"
LIMITE_DAS_INSTRUCOES = 8000  # o menor limite entre os três ambientes
MARCA_DE_SKILL = "origem: harness-de-entregaveis"
# Skills que só fazem sentido onde o harness está instalado em uma pasta.
SO_COM_ARQUIVOS = {"adotar-projeto", "atualizar-harness", "usar-outro-ambiente"}


def versao() -> str:
    return comum.ler(comum.HARNESS / "VERSAO").strip() or "?"


def topo(titulo: str, nota: str = "") -> str:
    linhas = [f"# {titulo}", "", f"Arquivo de conhecimento do harness de entregáveis, versão {versao()}. Gerado por empacotar.py: não edite à mão."]
    if nota:
        linhas += ["", nota]
    return "\n".join(linhas) + "\n"


def rebaixar(texto: str, niveis: int = 1) -> str:
    """Desce os títulos Markdown de nível, fora dos blocos de código."""
    saida, em_bloco = [], False
    for linha in texto.splitlines():
        if linha.lstrip().startswith(("```", "~~~")):
            em_bloco = not em_bloco
        if not em_bloco and re.match(r"^#{1,5} ", linha):
            linha = "#" * niveis + linha
        saida.append(linha)
    return "\n".join(saida).strip("\n") + "\n"


def cercado(texto: str) -> str:
    return "~~~text\n" + texto.strip("\n") + "\n~~~\n"


def ordem_das_skills() -> list[str]:
    """A ordem em que as skills aparecem na tabela das regras, que é a ordem do trabalho."""
    return re.findall(r"\| `([a-z0-9-]+)` \|", comum.ler(comum.HARNESS / "REGRAS.md"))


def skills(do_projeto: bool) -> list[Path]:
    pasta = comum.RAIZ / ".claude" / "skills"
    achadas = {}
    for arquivo in sorted(pasta.glob("*/SKILL.md")):
        nome = arquivo.parent.name
        if nome in SO_COM_ARQUIVOS or nome.startswith("pacote-"):
            continue
        if not do_projeto and MARCA_DE_SKILL not in comum.ler(arquivo):
            continue  # o pacote do kit leva só as skills do kit
        achadas[nome] = arquivo
    ordem = ordem_das_skills()
    return sorted(achadas.values(), key=lambda a: (ordem.index(a.parent.name) if a.parent.name in ordem else len(ordem), a.parent.name))


def procedimento(arquivo: Path, nome: str | None = None) -> str:
    meta, corpo = comum.cabecalho(comum.ler(arquivo))
    nome = nome or meta.get("name", arquivo.parent.name)
    quando = re.sub(r"^Use ", "", meta.get("description", "")).strip()
    corpo = re.sub(r"^# .*\n", "", corpo.strip("\n"), count=1)
    return f"## {nome}\n\nQuando: {quando}\n\n" + rebaixar(corpo.strip("\n"), 1)


def procedimentos(do_projeto: bool) -> str:
    nota = (
        "Estes procedimentos foram escritos para um agente que lê e grava arquivos e roda comandos. Neste ambiente, "
        "onde o texto manda rodar um script, faça a conferência à mão pelas regras de 2-metodo-e-texto. Onde manda "
        "gravar em um arquivo de `entregaveis/_projeto/` ou na pasta de um entregável, atualize a seção correspondente "
        "do registro do projeto. As skills citadas pelo nome são os procedimentos deste arquivo."
    )
    return topo("Procedimentos", nota) + "\n" + "\n".join(procedimento(a) for a in skills(do_projeto))


def lista_de_vicios(arquivo: Path) -> str:
    linhas = []
    for linha in comum.ler(arquivo).splitlines():
        partes = linha.split("\t")
        if not linha.strip() or linha.startswith("#") or len(partes) < 3:
            continue
        linhas.append(f"- {partes[2].strip()} Padrão: `{partes[1].strip()}`")
    return "\n".join(linhas) + "\n"


def metodo_e_texto() -> str:
    metodo = comum.HARNESS / "metodo"
    partes = [topo("Método, texto e revisão")]
    for nome in ("metodo.md", "texto.md", "rubrica.md"):
        partes.append(rebaixar(comum.ler(metodo / nome)))
    partes.append("## Vícios de texto a tirar\n\nCada linha diz o que corrigir e traz o padrão que denuncia o vício. Confira o texto contra a lista do idioma dele e contra a lista geral.\n")
    for titulo, nome in (("Em qualquer idioma", "texto-geral.tsv"), ("Português", "texto-pt.tsv"), ("Espanhol", "texto-es.tsv"), ("Inglês", "texto-en.tsv")):
        partes.append(f"### {titulo}\n\n" + lista_de_vicios(comum.LISTAS / nome))
    rotulos = [l.strip() for l in comum.ler(comum.LISTAS / "rotulos.txt").splitlines() if l.strip() and not l.startswith("#")]
    partes.append("### Títulos que são rótulo\n\nUm título de página diz a mensagem. Estes são rótulos de assunto e não servem de título: " + ", ".join(rotulos) + ".\n")
    return "\n".join(partes)


def formatos_e_visual() -> str:
    metodo = comum.HARNESS / "metodo"
    partes = [topo("Formatos, visual e HTML interativo")]
    for nome in ("formatos.md", "visual.md", "interativo.md"):
        partes.append(rebaixar(comum.ler(metodo / nome)))
    return "\n".join(partes)


def modelos() -> str:
    nota = "Cada modelo é a forma de uma seção do registro do projeto ou de uma parte de um entregável. PREENCHER marca o que ainda precisa ser escrito."
    partes = [topo("Modelos", nota)]
    grupos = (
        ("Entregável", comum.MODELOS / "entregavel", ("briefing.md", "storyline.md", "storyboard.md", "conteudo.md", "documento.md", "planilha.md", "revisao.md")),
        ("Projeto", comum.MODELOS / "projeto", ("brief.md", "fases.md", "audiencia.md", "marca.md", "regras-de-material.md", "decisoes.md", "licoes.md", "evidencias.tsv", "glossario.tsv", "adiados.tsv", "limites.tsv")),
        ("Fase", comum.MODELOS / "fase", ("passagem.md",)),
        ("Materiais", comum.MODELOS / "intake", ("registro.tsv",)),
        ("Domínio", comum.MODELOS / "dominio", ("dominio.md", "checagens.tsv", "casos.tsv")),
    )
    for titulo, pasta, nomes in grupos:
        partes.append(f"## {titulo}\n")
        for nome in nomes:
            if (pasta / nome).is_file():
                partes.append(f"### {nome}\n\n" + cercado(comum.ler(pasta / nome)))
    return "\n".join(partes)


def pacotes_do_kit() -> list[str]:
    pasta = comum.HARNESS / "pacotes"
    return sorted(p.name for p in pasta.iterdir() if (p / "PACOTE.md").is_file()) if pasta.is_dir() else []


def pacote(nome: str) -> str:
    pasta = comum.HARNESS / "pacotes" / nome
    partes = [topo(f"Pacote {nome}", "Ponto de partida genérico para este tipo de projeto. O domínio do projeto vence o pacote onde os dois se contradizem.")]
    partes.append(rebaixar(comum.ler(pasta / "PACOTE.md")))
    if (pasta / "entrevistas.md").is_file():
        partes.append(rebaixar(comum.ler(pasta / "entrevistas.md")))
    if (pasta / "skill" / "SKILL.md").is_file():
        partes.append(procedimento(pasta / "skill" / "SKILL.md", f"Procedimento do pacote {nome}"))
    for titulo, arquivo in (("Termos do pacote", "glossario.tsv"), ("Pedido de dados", "pedido-de-dados.tsv")):
        if (pasta / arquivo).is_file():
            partes.append(f"## {titulo}\n\n" + cercado(comum.ler(pasta / arquivo)))
    return "\n".join(partes)


def arquivos_do_kit(do_projeto: bool = False) -> dict[str, str]:
    arquivos = {
        "1-procedimentos.txt": procedimentos(do_projeto),
        "2-metodo-e-texto.txt": metodo_e_texto(),
        "3-formatos-e-visual.txt": formatos_e_visual(),
        "4-modelos.txt": modelos(),
    }
    for nome in pacotes_do_kit():
        arquivos[f"pacote-{nome}.txt"] = pacote(nome)
    return arquivos


# --- o pacote de um projeto -------------------------------------------------

REGISTROS = ("brief.md", "fases.md", "audiencia.md", "marca.md", "regras-de-material.md", "decisoes.md", "licoes.md", "glossario.tsv", "evidencias.tsv", "adiados.tsv", "limites.tsv")


def pacotes_do_projeto() -> list[str]:
    """Os pacotes de todas as fases do projeto, com os da fase atual primeiro."""
    meta, _ = comum.cabecalho(comum.ler(comum.PROJETO / "brief.md"))
    nomes = [p.strip() for p in meta.get("pacotes", "").split(",") if p.strip()]
    for linha in comum.tabela(comum.ler(comum.PROJETO / "fases.md")):
        nomes += [p.strip() for p in linha.get("pacotes", "").split(",") if p.strip()]
    vistos: list[str] = []
    for nome in nomes:
        if nome in pacotes_do_kit() and nome not in vistos:
            vistos.append(nome)
    return vistos


def projeto() -> str:
    nota = (
        "O registro deste projeto no dia em que o pacote foi montado. Ele vence os pacotes onde os dois se contradizem. "
        "A lista de nomes confidenciais não vem aqui: pergunte ao consultor que nomes não podem aparecer."
    )
    partes = [topo("Projeto", nota)]
    partes.append("## Registros do projeto\n")
    for nome in REGISTROS:
        texto = comum.ler(comum.PROJETO / nome)
        if texto.strip():
            partes.append(f"### {nome}\n\n" + cercado(texto))
    for pasta in sorted((comum.PROJETO / "fases").glob("fase-*")):
        if (pasta / "passagem.md").is_file():
            partes.append(f"### Passagem da {pasta.name}\n\n" + cercado(comum.ler(pasta / "passagem.md")))
    intake = comum.ler(comum.INTAKE / "registro.tsv")
    if intake.strip():
        partes.append("## Materiais pedidos e recebidos\n\n" + cercado(intake))
    dominio = comum.BASE / "_dominio"
    if comum.ler(dominio / "dominio.md").strip():
        partes.append("## Domínio do projeto\n\n" + cercado(comum.ler(dominio / "dominio.md")))
        if comum.ler(dominio / "checagens.tsv").strip():
            partes.append("### Regras de checagem do domínio\n\nConfira cada entregável contra estas regras, à mão.\n\n" + cercado(comum.ler(dominio / "checagens.tsv")))
    entregaveis = comum.entregaveis()
    if entregaveis:
        partes.append("## Entregáveis\n")
    for pasta in entregaveis:
        partes.append(f"### {pasta.name}\n")
        for nome in ("briefing.md", "storyline.md", "storyboard.md"):
            texto = comum.ler(pasta / nome)
            if texto.strip():
                partes.append(f"#### {nome}\n\n" + cercado(texto))
    return "\n".join(partes)


def arquivos_do_projeto() -> dict[str, str]:
    todos = arquivos_do_kit(do_projeto=True)
    ativos = pacotes_do_projeto()
    arquivos = {nome: texto for nome, texto in todos.items() if not nome.startswith("pacote-") or nome[len("pacote-"):-len(".txt")] in ativos}
    arquivos["5-projeto.txt"] = projeto()
    arquivos["instrucoes.txt"] = comum.ler(INSTRUCOES)
    return arquivos


# --- gravação ---------------------------------------------------------------

def gravar(destino: Path, arquivos: dict[str, str], limpar: bool = False) -> list[str]:
    """Grava os arquivos. 'limpar' tira os .txt que saíram do pacote, e só vale na pasta do próprio kit."""
    destino.mkdir(parents=True, exist_ok=True)
    mudados = []
    for nome, texto in arquivos.items():
        if comum.ler(destino / nome) != texto:
            (destino / nome).write_text(texto, encoding="utf-8")
            mudados.append(nome)
    for sobra in sorted(destino.glob("*.txt")) if limpar else []:
        if sobra.name not in arquivos:
            sobra.unlink()
            mudados.append(f"{sobra.name} (retirado)")
    return mudados


def diferencas(destino: Path, arquivos: dict[str, str]) -> list[str]:
    fora = [nome for nome, texto in arquivos.items() if comum.ler(destino / nome) != texto]
    fora += [a.name for a in sorted(destino.glob("*.txt")) if a.name not in arquivos]
    return fora


def main() -> int:
    analisador = argparse.ArgumentParser(description="Monta o pacote para Claude desktop, ChatGPT desktop e Microsoft Copilot.")
    analisador.add_argument("--conferir", action="store_true", help="diz se os arquivos de conhecimento do kit estão em dia")
    analisador.add_argument("--projeto", action="store_true", help="monta o pacote deste projeto, com os registros e o domínio")
    analisador.add_argument("--saida", default="", help="a pasta do pacote do projeto (padrão: entregaveis/_ambiente)")
    args = analisador.parse_args()

    tamanho = len(comum.ler(INSTRUCOES))
    if tamanho > LIMITE_DAS_INSTRUCOES:
        raise SystemExit(f"{comum.relativo(INSTRUCOES)} tem {tamanho} caracteres. O limite é {LIMITE_DAS_INSTRUCOES}, o menor entre os ambientes.")
    if args.conferir:
        fora = diferencas(CONHECIMENTO, arquivos_do_kit())
        if fora:
            print("Arquivos de conhecimento fora de dia: " + ", ".join(fora) + ". Rode empacotar.py e grave o resultado.")
            return 1
        print("Os arquivos de conhecimento estão em dia.")
        return 0
    if not args.projeto:
        mudados = gravar(CONHECIMENTO, arquivos_do_kit(), limpar=True)
        print(f"{comum.relativo(CONHECIMENTO)}: " + (", ".join(mudados) if mudados else "nada mudou") + ".")
        return 0
    meta, _ = comum.cabecalho(comum.ler(comum.PROJETO / "brief.md"))
    if not meta or comum.normalizar(meta.get("iniciado", "nao")) != "sim":
        raise SystemExit("O projeto ainda não foi iniciado. Sem projeto, use os arquivos prontos de " + comum.relativo(AMBIENTES) + ".")
    destino = Path(args.saida).expanduser() if args.saida else comum.BASE / "_ambiente"
    if not destino.is_absolute():
        destino = comum.RAIZ / destino
    arquivos = arquivos_do_projeto()
    gravar(destino, arquivos)
    print(f"Pacote do projeto em {comum.relativo(destino)}:")
    for nome, texto in arquivos.items():
        print(f"  {nome} ({len(texto) // 1000 + 1} mil caracteres)")
    print(
        "Atenção: 5-projeto.txt leva o brief, as decisões, as evidências e o domínio deste projeto. Só envie a um ambiente "
        "que as regras de material do projeto permitem. Quem decide é o consultor."
    )
    print("Cole o conteúdo de instrucoes.txt no campo de instruções e envie os outros arquivos como conhecimento. O passo a passo de cada ambiente está em " + comum.relativo(AMBIENTES / "LEIA-ME.md") + ".")
    return 0


if __name__ == "__main__":
    sys.exit(main())
