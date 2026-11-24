#!/usr/bin/env python3
"""Confere se esta máquina tem o que o harness precisa e diz como resolver o que falta.

Uso:
    ambiente.py              lista o que está pronto e o que falta, com o comando de cada falta
    ambiente.py --instalar   instala os pacotes Python do gerador de arquivos (pip)

Sai com código 1 quando falta algo essencial: Python 3.9 ou mais novo e o
comando python3, que os hooks e as regras chamam. O resto é pedido só
por um formato de arquivo e não impede o trabalho.

Este arquivo roda em versões antigas do Python, para conseguir dizer que
a versão é antiga. Só usa a biblioteca padrão.
"""
import importlib.util
import os
import platform
import shutil
import subprocess
import sys

MINIMO = (3, 9)
HARNESS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def no_projeto(*partes):
    """O caminho de um arquivo do harness a partir da raiz do projeto, com o nome que a pasta tem aqui."""
    raiz = os.path.dirname(os.path.dirname(HARNESS))
    return os.path.relpath(os.path.join(HARNESS, *partes), raiz).replace(os.sep, "/")


PACOTES = [("pptx", "python-pptx", "gerar PowerPoint"), ("docx", "python-docx", "gerar Word"), ("openpyxl", "openpyxl", "gerar Excel")]

# Como instalar cada programa, por sistema. O agente roda o comando com o sim do consultor, ou repassa o passo a passo.
COMO = {
    "python": {
        "Windows": "instale o Python 3 pela Microsoft Store (procure por Python 3.12), que cria o comando python3. Depois feche e abra o terminal",
        "Darwin": "brew install python   (sem o Homebrew: baixe o instalador em https://www.python.org/downloads/)",
        "Linux": "sudo apt install python3 python3-pip   (em Fedora: sudo dnf install python3 python3-pip)",
    },
    "git": {
        "Windows": "winget install Git.Git",
        "Darwin": "xcode-select --install   (ou: brew install git)",
        "Linux": "sudo apt install git   (em Fedora: sudo dnf install git)",
    },
    "soffice": {
        "Windows": "winget install TheDocumentFoundation.LibreOffice",
        "Darwin": "brew install --cask libreoffice",
        "Linux": "sudo apt install libreoffice   (em Fedora: sudo dnf install libreoffice)",
    },
    "pdftoppm": {
        "Windows": "baixe o Poppler para Windows e ponha a pasta bin no PATH. Sem ele, confira as páginas abrindo o PDF",
        "Darwin": "brew install poppler",
        "Linux": "sudo apt install poppler-utils   (em Fedora: sudo dnf install poppler-utils)",
    },
}


def sistema():
    nome = platform.system()
    return nome if nome in ("Windows", "Darwin", "Linux") else "Linux"


def versao_de(comando):
    """A primeira linha que o programa responde a --version, ou vazio quando ele não roda."""
    caminho = shutil.which(comando)
    if not caminho:
        return ""
    try:
        saida = subprocess.run([caminho, "--version"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return ""
    texto = saida.stdout.decode("utf-8", "replace").strip().splitlines()
    return texto[0] if saida.returncode == 0 and texto else ""


def conferir():
    """Cada item: (nível, pronto, o que é, como resolver). Nível: essencial, recomendado ou formato."""
    onde = sistema()
    itens = []
    atual = sys.version_info[:3]
    itens.append(("essencial", atual >= MINIMO, "Python %d.%d.%d (o harness pede 3.9 ou mais novo)" % atual, COMO["python"][onde]))
    tres = versao_de("python3")
    numeros = tuple(int(n) for n in tres.replace("Python", "").strip().split(".")[:2] if n.isdigit()) if tres else ()
    itens.append(("essencial", bool(numeros) and numeros >= MINIMO, "Comando python3, que os hooks e as regras chamam" + (" (%s)" % tres if tres else ""), COMO["python"][onde]))
    git = versao_de("git")
    itens.append(("recomendado", bool(git), "Git, para guardar o histórico do projeto" + (" (%s)" % git if git else ""), COMO["git"][onde]))
    for modulo, pacote, uso in PACOTES:
        pronto = importlib.util.find_spec(modulo) is not None
        itens.append(("formato", pronto, "%s, para %s" % (pacote, uso), "%s -m pip install %s" % ("python3" if tres else "python", pacote)))
    escritorio = shutil.which("soffice") or shutil.which("libreoffice")
    itens.append(("formato", bool(escritorio), "LibreOffice, para gerar PDF e as imagens de conferência", COMO["soffice"][onde]))
    itens.append(("formato", bool(shutil.which("pdftoppm")), "pdftoppm, para as imagens de conferência das páginas", COMO["pdftoppm"][onde]))
    return itens


def relatorio(itens):
    nomes = {"Windows": "Windows", "Darwin": "macOS", "Linux": "Linux"}
    linhas = ["Ambiente desta máquina (%s)" % nomes[sistema()]]
    for nivel, pronto, texto, _ in itens:
        linhas.append("%-6s %s" % ("OK" if pronto else "FALTA", texto) + ("" if pronto or nivel != "essencial" else "  [essencial]"))
    faltas = [i for i in itens if not i[1]]
    if not faltas:
        linhas.append("\nTudo pronto: nada a instalar.")
        return "\n".join(linhas)
    linhas.append("\nComo resolver o que falta:")
    for n, (nivel, _, texto, como) in enumerate(faltas, start=1):
        linhas.append("%d. %s\n   %s" % (n, texto.split(",")[0].split(" (")[0], como))
    if any(nivel == "formato" and "pip install" in como for nivel, _, _, como in faltas):
        linhas.append("\nOs pacotes Python do gerador entram de uma vez com: ambiente.py --instalar")
    if any(nivel == "essencial" for nivel, _, _, _ in faltas):
        linhas.append("\nFalta o essencial. Sem ele, as checagens e os hooks não rodam: resolva antes de iniciar o projeto.")
    else:
        linhas.append("\nO essencial está pronto. O que falta só é pedido na hora de gerar o arquivo daquele formato.")
    linhas.append("O agente pode rodar estes comandos com o seu sim, ou você roda um a um no terminal.")
    linhas.append("Se nada pode ser instalado nesta máquina, o método vale sem instalação: veja %s." % no_projeto("ambientes", "LEIA-ME.md"))
    return "\n".join(linhas)


def faltas_em_uma_linha():
    """Para o relatório do instalador: vazio quando nada falta."""
    faltas = [i for i in conferir() if not i[1]]
    if not faltas:
        return ""
    nomes = ", ".join(texto.split(",")[0].split(" (")[0] for _, _, texto, _ in faltas)
    essencial = " Falta o essencial." if any(nivel == "essencial" for nivel, _, _, _ in faltas) else ""
    return "Nesta máquina falta: %s.%s O script ambiente.py diz como resolver cada item." % (nomes, essencial)


def instalar():
    faltam = [pacote for modulo, pacote, _ in PACOTES if importlib.util.find_spec(modulo) is None]
    if not faltam:
        print("Os pacotes do gerador já estão instalados.")
        return 0
    for extra in ([], ["--user"]):
        comando = [sys.executable, "-m", "pip", "install"] + extra + faltam
        print("Rodando: " + " ".join(comando))
        try:
            saida = subprocess.run(comando, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=900)
        except (OSError, subprocess.SubprocessError) as erro:
            print("Não consegui rodar o pip: %s" % erro)
            break
        if saida.returncode == 0:
            print("Instalado: " + ", ".join(faltam) + ".")
            return 0
        print("\n".join(saida.stdout.decode("utf-8", "replace").strip().splitlines()[-4:]))
    print(
        "\nO pip recusou a instalação nesta máquina. O caminho seguro é um ambiente próprio do projeto:\n"
        "  python3 -m venv .venv\n"
        "  .venv/bin/python -m pip install " + " ".join(faltam) + "      (no Windows: .venv\\Scripts\\python)\n"
        "Depois gere os arquivos com esse Python: .venv/bin/python %s ID" % no_projeto("scripts", "gerar.py")
    )
    return 1


def main():
    if "--instalar" in sys.argv[1:]:
        return instalar()
    if any(a in ("-h", "--help") for a in sys.argv[1:]):
        print(__doc__.strip())
        return 0
    itens = conferir()
    print(relatorio(itens))
    return 1 if any(nivel == "essencial" and not pronto for nivel, pronto, _, _ in itens) else 0


if __name__ == "__main__":
    sys.exit(main())
