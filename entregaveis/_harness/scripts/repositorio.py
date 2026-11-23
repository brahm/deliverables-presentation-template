#!/usr/bin/env python3
"""Diz se o repositório do projeto pode guardar material de cliente.

Um projeto iniciado só vive em três lugares: uma pasta sem git, um git
local sem remoto, ou um repositório privado. Um remoto que qualquer
pessoa lê sem se identificar é público, e o harness recusa.

Uso:
    repositorio.py                         mostra a situação de cada remoto
    repositorio.py --confirmar "palavras"  registra que o consultor confirmou que
                                           os remotos não verificados são privados

A verificação é o pedido que o git faz ao clonar, sem credencial, ao
endereço do próprio remoto. Quando não há rede, ou o servidor não
responde, a situação fica "não verificado" e vale a confirmação do consultor, registrada em
_projeto/repositorio.tsv. Um remoto verificado como público não aceita
confirmação: torne-o privado ou remova-o.

Sai com 0 quando o projeto pode ficar onde está e com 1 quando não pode.
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import comum  # noqa: E402

REGISTRO = comum.PROJETO / "repositorio.tsv"
MEMORIA = comum.HARNESS / ".estado" / "repositorio.json"
VALIDADE = {"privado": 24 * 3600, "publico": 120, "nao-verificado": 900}
ESPERA = 4

LOCAL = "local"
PRIVADO = "privado"
PUBLICO = "publico"
NAO_VERIFICADO = "nao-verificado"


def remotos(raiz: Path | None = None) -> dict[str, str]:
    """Os remotos do git do projeto, por nome. Vazio quando não há git ou não há remoto."""
    raiz = raiz or comum.RAIZ
    try:
        saida = subprocess.run(
            ["git", "-C", str(raiz), "config", "--get-regexp", r"^remote\..*\.url$"],
            capture_output=True, text=True, timeout=10,
        )
        if saida.returncode in (0, 1):
            achados = {}
            for linha in saida.stdout.splitlines():
                chave, _, url = linha.partition(" ")
                achados[chave[len("remote."):-len(".url")]] = url.strip()
            return achados
    except (OSError, subprocess.SubprocessError):
        pass
    # Sem o programa git, lê o arquivo de configuração.
    config = raiz / ".git" / "config"
    achados, nome = {}, None
    for linha in comum.ler(config).splitlines():
        m = re.match(r'\s*\[remote "(.+)"\]', linha)
        if m:
            nome = m.group(1)
        elif linha.strip().startswith("["):
            nome = None
        elif nome and re.match(r"\s*url\s*=", linha):
            achados[nome] = linha.split("=", 1)[1].strip()
    return achados


def endereco(url: str) -> tuple[str, str, str] | None:
    """(protocolo, servidor, caminho) de um remoto de rede. None para um remoto em disco."""
    url = url.strip()
    m = re.match(r"^(https?|ssh|git)://(?:[^@/]+@)?([^/]+)/(.+)$", url)
    if not m:
        m2 = re.match(r"^(?:[^@/:]+@)?([A-Za-z0-9.-]+\.[A-Za-z]{2,}):(?!/)(.+)$", url)
        if not m2:
            return None
        protocolo, servidor, caminho = "https", m2.group(1), m2.group(2)
    else:
        protocolo, servidor, caminho = m.group(1), m.group(2), m.group(3)
        if protocolo != "http":
            protocolo = "https"
            servidor = servidor.split(":")[0]
    caminho = re.sub(r"\.git/?$", "", caminho.strip("/"))
    return protocolo, servidor.lower(), caminho


def _pedir(url: str) -> tuple[int | None, str]:
    """Código e tipo da resposta a um pedido anônimo, sem seguir redirecionamento."""

    class SemRedirecionar(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None

    servidor = url.split("/")[2].split(":")[0]
    manipuladores = [SemRedirecionar()]
    if servidor in ("127.0.0.1", "localhost"):
        manipuladores.append(urllib.request.ProxyHandler({}))
    abridor = urllib.request.build_opener(*manipuladores)
    pedido = urllib.request.Request(url, headers={"User-Agent": "git/2.40 harness-de-entregaveis"})
    try:
        with abridor.open(pedido, timeout=ESPERA) as resposta:
            return resposta.status, resposta.headers.get("Content-Type", "")
    except urllib.error.HTTPError as erro:
        return erro.code, ""
    except (urllib.error.URLError, OSError, ValueError):
        return None, ""


def verificar(url: str) -> str:
    """Pergunta ao servidor do remoto se o repositório pode ser clonado por quem não se identifica.

    É o mesmo pedido que o git faz ao clonar por HTTPS, sem credencial. Se o
    servidor entrega a lista de referências, o repositório é público. Se pede
    identificação ou diz que não existe, é privado. Qualquer outra resposta
    fica como não verificada.
    """
    partes = endereco(url)
    if partes is None:
        return LOCAL
    protocolo, servidor, caminho = partes
    codigo, tipo = _pedir(f"{protocolo}://{servidor}/{caminho}.git/info/refs?service=git-upload-pack")
    if codigo == 200 and "git-upload-pack" in tipo:
        return PUBLICO
    if codigo in (301, 302, 303, 307, 308, 401, 403, 404):
        return PRIVADO
    return NAO_VERIFICADO


def _memoria() -> dict:
    try:
        return json.loads(MEMORIA.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _lembrar(url: str, situacao: str) -> None:
    dados = _memoria()
    dados[url] = {"situacao": situacao, "quando": time.time()}
    try:
        MEMORIA.parent.mkdir(exist_ok=True)
        MEMORIA.write_text(json.dumps(dados), encoding="utf-8")
    except OSError:
        pass


def confirmados() -> dict[str, dict]:
    """Remotos que o consultor confirmou como privados, pelo endereço."""
    return {l.get("remoto", ""): l for l in comum.ler_tsv(REGISTRO) if comum.normalizar(l.get("situacao", "")) == PRIVADO}


def situacao_do_remoto(url: str, usar_memoria: bool = True) -> str:
    guardado = _memoria().get(url) if usar_memoria else None
    if guardado and time.time() - guardado.get("quando", 0) < VALIDADE.get(guardado.get("situacao"), 0):
        situacao = guardado["situacao"]
    else:
        situacao = verificar(url)
        _lembrar(url, situacao)
    if situacao == NAO_VERIFICADO and url in confirmados():
        return PRIVADO
    return situacao


def situacao(usar_memoria: bool = True) -> tuple[str, list[tuple[str, str, str]]]:
    """A pior situação entre os remotos, e a lista (nome, endereço, situação)."""
    linhas = [(nome, url, situacao_do_remoto(url, usar_memoria)) for nome, url in sorted(remotos().items())]
    for pior in (PUBLICO, NAO_VERIFICADO, PRIVADO):
        if any(s == pior for _, _, s in linhas):
            return pior, linhas
    return LOCAL, linhas


def aceita(geral: str) -> bool:
    return geral in (LOCAL, PRIVADO)


def tem_projeto() -> bool:
    """Diz se já há conteúdo de projeto: brief iniciado, entregável, domínio ou material recebido."""
    meta, _ = comum.cabecalho(comum.ler(comum.PROJETO / "brief.md"))
    if comum.normalizar(meta.get("iniciado", "nao")) == "sim" or comum.entregaveis():
        return True
    dominio = comum.ler(comum.BASE / "_dominio" / "dominio.md")
    if dominio and comum.MARCA not in dominio:
        return True
    materiais = comum.INTAKE / "materiais"
    return materiais.is_dir() and any(a.name != ".gitkeep" for a in materiais.iterdir())


def explicar(geral: str, linhas: list[tuple[str, str, str]]) -> str:
    """O que dizer ao agente quando o repositório não serve para um projeto de cliente."""
    if geral == PUBLICO:
        publicos = ", ".join(f"{nome} ({url})" for nome, url, s in linhas if s == PUBLICO)
        return (
            f"O repositório remoto {publicos} é público: qualquer pessoa lê o que for enviado. "
            "Um projeto de cliente só fica em git local ou em repositório privado. "
            "Peça ao consultor para tornar o repositório privado, ou para remover o remoto e seguir só com o git local, "
            "e rode de novo 'python3 entregaveis/_harness/scripts/repositorio.py'. Não contorne esta trava."
        )
    pendentes = ", ".join(f"{nome} ({url})" for nome, url, s in linhas if s == NAO_VERIFICADO)
    return (
        f"Não foi possível verificar se o repositório remoto {pendentes} é privado (sem rede, ou o servidor não respondeu). "
        "Um projeto de cliente só fica em git local ou em repositório privado. "
        "Pergunte ao consultor se o repositório é privado e, com o sim dele, registre com "
        "'python3 entregaveis/_harness/scripts/repositorio.py --confirmar \"palavras do consultor\"'. "
        "Não registre a confirmação por conta própria."
    )


def confirmar(palavras: str) -> int:
    geral, linhas = situacao(usar_memoria=False)
    if geral == PUBLICO:
        print(explicar(geral, linhas))
        return 1
    pendentes = [(nome, url) for nome, url, s in linhas if s == NAO_VERIFICADO]
    if not pendentes:
        print("Nada a confirmar: não há remoto sem verificação.")
        return 0
    cabecalho = "remoto\tsituacao\tconfirmado_em\tpalavras_do_consultor\n"
    atual = comum.ler(REGISTRO)
    if not atual.strip():
        atual = "# Remotos que o consultor confirmou como privados. Uma linha por endereço.\n" + cabecalho
    hoje = datetime.date.today().isoformat()
    limpo = re.sub(r"[\t\r\n]+", " ", palavras).strip()
    for _, url in pendentes:
        atual = atual.rstrip("\n") + f"\n{url}\t{PRIVADO}\t{hoje}\t{limpo}\n"
    REGISTRO.parent.mkdir(parents=True, exist_ok=True)
    REGISTRO.write_text(atual, encoding="utf-8")
    print(f"Confirmação registrada em {comum.relativo(REGISTRO)} para: " + ", ".join(url for _, url in pendentes) + ".")
    return 0


NOMES = {LOCAL: "local", PRIVADO: "privado", PUBLICO: "PÚBLICO", NAO_VERIFICADO: "não verificado"}


def main() -> int:
    analisador = argparse.ArgumentParser(description="Situação do repositório do projeto.")
    analisador.add_argument("--confirmar", metavar="PALAVRAS", help="registra a confirmação do consultor para os remotos não verificados")
    args = analisador.parse_args()
    if args.confirmar:
        return confirmar(args.confirmar)
    geral, linhas = situacao(usar_memoria=False)
    if not linhas:
        print("Sem repositório remoto: o projeto fica só nesta máquina. Pode seguir.")
        return 0
    for nome, url, s in linhas:
        print(f"{nome}\t{NOMES[s]}\t{url}")
    if aceita(geral):
        print("Repositório privado. Pode seguir.")
        return 0
    print(explicar(geral, linhas))
    return 1


if __name__ == "__main__":
    sys.exit(main())
