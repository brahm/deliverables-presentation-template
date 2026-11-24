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
endereço do próprio remoto, seguindo os redirecionamentos do servidor.
Quando não há rede, ou o servidor não responde, a situação fica "não
verificado" e vale a confirmação do consultor, registrada em
_projeto/repositorio.tsv. Um remoto verificado como público não aceita
confirmação: torne-o privado ou remova-o.

O endereço de envio de um remoto (pushurl) é conferido como um remoto à
parte. Usuário e senha escritos no endereço nunca são mostrados nem
gravados.

Sai com 0 quando o projeto pode ficar onde está e com 1 quando não pode.
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import shlex
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import comum  # noqa: E402

REGISTRO = comum.PROJETO / "repositorio.tsv"
MEMORIA = comum.HARNESS / ".estado" / "repositorio.json"
ESTE = comum.relativo(Path(__file__).resolve()).replace("\\", "/")  # o caminho deste script no projeto, para as mensagens
VALIDADE = {"privado": 24 * 3600, "publico": 120, "nao-verificado": 900}
ESPERA = 4
SALTOS = 5  # quantos redirecionamentos seguir antes de desistir
REGRA = 2  # muda quando a classificação muda, para a memória antiga não valer

LOCAL = "local"
PRIVADO = "privado"
PUBLICO = "publico"
NAO_VERIFICADO = "nao-verificado"


def remotos(raiz: Path | None = None) -> dict[str, str]:
    """Os remotos do git do projeto, por nome. Vazio quando não há git ou não há remoto."""
    raiz = raiz or comum.RAIZ
    try:
        saida = subprocess.run(
            ["git", "-C", str(raiz), "config", "--get-regexp", r"^remote\..*\.(url|pushurl)$"],
            capture_output=True, text=True, timeout=10,
        )
        if saida.returncode in (0, 1):
            achados = {}
            for linha in saida.stdout.splitlines():
                chave, _, url = linha.partition(" ")
                nome, _, campo = chave[len("remote."):].rpartition(".")
                _guardar(achados, nome, campo, url.strip())
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
        elif nome and (m := re.match(r"\s*(url|pushurl)\s*=", linha, flags=re.IGNORECASE)):
            _guardar(achados, nome, m.group(1).lower(), linha.split("=", 1)[1].strip())
    return achados


def _guardar(achados: dict[str, str], nome: str, campo: str, url: str) -> None:
    """Guarda o endereço de um remoto. O de envio entra com nome próprio, e um remoto pode ter mais de um."""
    if campo == "url":
        achados.setdefault(nome, url)
        return
    chave, n = f"{nome} (envio)", 2
    while chave in achados:
        chave, n = f"{nome} (envio {n})", n + 1
    achados[chave] = url


def sem_credencial(url: str) -> str:
    """O endereço sem o usuário e a senha, para mostrar e para gravar.

    Em http e https, tudo o que vem antes do '@' sai, porque um token
    costuma ser escrito no lugar do usuário. Em ssh, o usuário fica e só a
    senha sai.
    """
    url = url.strip()
    m = re.match(r"^(https?://)[^@/]*@(.*)$", url, flags=re.IGNORECASE)
    if m:
        return m.group(1) + m.group(2)
    m = re.match(r"^([a-z][a-z0-9+.-]*://[^:@/]+):[^@/]*@(.*)$", url, flags=re.IGNORECASE)
    if m:
        return m.group(1) + "@" + m.group(2)
    return url


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
    """Código e tipo da resposta final a um pedido anônimo, seguindo os redirecionamentos.

    Um redirecionamento não diz se o repositório é aberto ou fechado: o
    GitHub responde 301 a um endereço http e ao nome antigo de um
    repositório público. Por isso vale a resposta do fim do caminho. Um
    caminho com mais de SALTOS redirecionamentos, ou que não diz para
    onde vai, fica sem resposta.
    """

    class SemRedirecionar(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None

    for _ in range(SALTOS + 1):
        partes = urllib.parse.urlsplit(url)
        if partes.scheme not in ("http", "https") or not partes.hostname:
            return None, ""
        manipuladores = [SemRedirecionar()]
        if partes.hostname in ("127.0.0.1", "localhost"):
            manipuladores.append(urllib.request.ProxyHandler({}))
        abridor = urllib.request.build_opener(*manipuladores)
        pedido = urllib.request.Request(url, headers={"User-Agent": "git/2.40 harness-de-entregaveis"})
        try:
            with abridor.open(pedido, timeout=ESPERA) as resposta:
                return resposta.status, resposta.headers.get("Content-Type", "")
        except urllib.error.HTTPError as erro:
            destino = erro.headers.get("Location", "") if erro.headers else ""
            if erro.code not in (301, 302, 303, 307, 308):
                return erro.code, ""
            if not destino:
                return None, ""
            url = urllib.parse.urljoin(url, destino)
        except (urllib.error.URLError, OSError, ValueError):
            return None, ""
    return None, ""


def verificar(url: str) -> str:
    """Pergunta ao servidor do remoto se o repositório pode ser clonado por quem não se identifica.

    É o mesmo pedido que o git faz ao clonar por HTTPS, sem credencial. Se o
    servidor entrega a lista de referências, o repositório é público. Se pede
    identificação ou diz que não existe, é privado. Qualquer outra resposta,
    como a página de entrada para onde alguns servidores redirecionam, fica
    como não verificada.
    """
    partes = endereco(url)
    if partes is None:
        return LOCAL
    protocolo, servidor, caminho = partes
    codigo, tipo = _pedir(f"{protocolo}://{servidor}/{caminho}.git/info/refs?service=git-upload-pack")
    if codigo == 200 and "git-upload-pack" in tipo:
        return PUBLICO
    if codigo in (401, 403, 404):
        return PRIVADO
    return NAO_VERIFICADO


def _memoria() -> dict:
    try:
        return json.loads(MEMORIA.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _lembrar(url: str, situacao: str) -> None:
    dados = {k: v for k, v in _memoria().items() if isinstance(v, dict) and v.get("regra") == REGRA}
    dados[sem_credencial(url)] = {"situacao": situacao, "quando": time.time(), "regra": REGRA}
    try:
        MEMORIA.parent.mkdir(exist_ok=True)
        MEMORIA.write_text(json.dumps(dados), encoding="utf-8")
    except OSError:
        pass


def confirmados() -> dict[str, dict]:
    """Remotos que o consultor confirmou como privados, pelo endereço."""
    return {sem_credencial(l.get("remoto", "")): l for l in comum.ler_tsv(REGISTRO) if comum.normalizar(l.get("situacao", "")) == PRIVADO}


def situacao_do_remoto(url: str, usar_memoria: bool = True) -> str:
    guardado = _memoria().get(sem_credencial(url)) if usar_memoria else None
    if isinstance(guardado, dict) and guardado.get("regra") == REGRA and time.time() - guardado.get("quando", 0) < VALIDADE.get(guardado.get("situacao"), 0):
        situacao = guardado["situacao"]
    else:
        situacao = verificar(url)
        _lembrar(url, situacao)
    if situacao == NAO_VERIFICADO and sem_credencial(url) in confirmados():
        return PRIVADO
    return situacao


def situacao(usar_memoria: bool = True, outros: dict[str, str] | None = None) -> tuple[str, list[tuple[str, str, str]]]:
    """A pior situação entre os remotos, e a lista (nome, endereço sem credencial, situação).

    'outros' são destinos que não estão na configuração do git, como o
    endereço escrito em um comando de envio.
    """
    todos = {**remotos(), **(outros or {})}
    linhas = [(nome, sem_credencial(url), situacao_do_remoto(url, usar_memoria)) for nome, url in sorted(todos.items())]
    for pior in (PUBLICO, NAO_VERIFICADO, PRIVADO):
        if any(s == pior for _, _, s in linhas):
            return pior, linhas
    return LOCAL, linhas


_OPCOES_COM_VALOR = {"-C", "-c", "-o", "--push-option", "--receive-pack", "--exec", "--repo", "--git-dir", "--work-tree", "--namespace"}


def _segmentos(comando: str) -> list[list[str]]:
    """As palavras do comando, separadas a cada '&&', ';', '|' ou quebra de linha."""
    segmentos: list[list[str]] = []
    for linha in comando.splitlines():
        try:
            leitor = shlex.shlex(linha, posix=True, punctuation_chars=True)
            leitor.whitespace_split = True
            palavras = list(leitor)
        except ValueError:  # aspas sem par: fica com a divisão simples
            palavras = re.split(r"\s+|(?<=[;&|])|(?=[;&|])", linha)
        atual: list[str] = []
        for palavra in palavras:
            if palavra and set(palavra) <= set(";&|()<>"):
                segmentos.append(atual)
                atual = []
            elif palavra:
                atual.append(palavra)
        segmentos.append(atual)
    return [s for s in segmentos if s]


def destinos_do_comando(comando: str) -> dict[str, str]:
    """Os endereços de repositório que um comando de git escreve por extenso.

    Olha o `git push ENDEREÇO`, o `--repo`, e o `git remote add` e o
    `git remote set-url`, que mudam o destino do envio seguinte. Um
    endereço em disco não entra, porque é local.
    """
    achados: dict[str, str] = {}

    def guardar(candidato: str) -> None:
        if endereco(candidato) is not None and candidato not in achados.values():
            achados[f"comando ({len(achados) + 1})"] = candidato

    for palavras in _segmentos(comando):
        # Um comando entre aspas, como o de `bash -c "git push ..."`, é lido por dentro.
        for palavra in palavras:
            if re.search(r"\s", palavra) and re.search(r"\bgit\b", palavra) and palavra != comando:
                for candidato in destinos_do_comando(palavra).values():
                    guardar(candidato)
        # O programa pode vir com o caminho, como /usr/bin/git.
        onde = next((i for i, palavra in enumerate(palavras) if re.split(r"[\\/]", palavra)[-1] in ("git", "git.exe")), None)
        if onde is None:
            continue
        depois = palavras[onde + 1:]
        if "push" in depois:
            candidatos = depois[depois.index("push") + 1:]
            primeiro = _primeiro_argumento(candidatos)
            candidatos = [c.split("=", 1)[1] for c in candidatos if c.startswith("--repo=")] + ([primeiro] if primeiro else [])
            candidatos += [depois[i + 1] for i, c in enumerate(depois[:-1]) if c == "--repo"]
        elif "remote" in depois and any(c in depois for c in ("add", "set-url")):
            candidatos = [c for c in depois[depois.index("remote") + 1:] if not c.startswith("-")]
        else:
            continue
        for candidato in candidatos:
            guardar(candidato)
    return achados


def _primeiro_argumento(palavras: list[str]) -> str:
    """O primeiro argumento de `git push` que não é opção: o nome do remoto ou o endereço."""
    pular = False
    for palavra in palavras:
        if pular:
            pular = False
        elif palavra in _OPCOES_COM_VALOR:
            pular = True
        elif not palavra.startswith("-"):
            return palavra
    return ""


def aceita(geral: str) -> bool:
    return geral in (LOCAL, PRIVADO)


def tem_projeto() -> bool:
    """Diz se já há conteúdo de projeto: brief iniciado, entregável, domínio, material recebido, ata ou nota do segundo cérebro."""
    meta, _ = comum.cabecalho(comum.ler(comum.PROJETO / "brief.md"))
    if comum.normalizar(meta.get("iniciado", "nao")) == "sim" or comum.entregaveis():
        return True
    dominio = comum.ler(comum.BASE / "_dominio" / "dominio.md")
    if dominio and comum.MARCA not in dominio:
        return True
    for pasta in (comum.INTAKE / "materiais", comum.INTAKE / "entrada", comum.BASE / "_atas"):
        if pasta.is_dir() and any(a.name not in (".gitkeep", "LEIA-ME.md") for a in pasta.iterdir()):
            return True
    cerebro = comum.BASE / "_cerebro"
    if any(a.suffix == ".md" for pasta in cerebro.glob("[1-4]-*") for a in pasta.rglob("*")):
        return True
    return False


def explicar(geral: str, linhas: list[tuple[str, str, str]]) -> str:
    """O que dizer ao agente quando o repositório não serve para um projeto de cliente."""
    if geral == PUBLICO:
        publicos = ", ".join(f"{nome} ({url})" for nome, url, s in linhas if s == PUBLICO)
        return (
            f"O repositório remoto {publicos} é público: qualquer pessoa lê o que for enviado. "
            "Um projeto de cliente só fica em git local ou em repositório privado. "
            "Peça ao consultor para tornar o repositório privado, ou para remover o remoto e seguir só com o git local, "
            f"e rode de novo 'python3 {ESTE}'. Não contorne esta trava."
        )
    pendentes = ", ".join(f"{nome} ({url})" for nome, url, s in linhas if s == NAO_VERIFICADO)
    return (
        f"Não foi possível verificar se o repositório remoto {pendentes} é privado (sem rede, o servidor não respondeu, ou respondeu com outra página). "
        "Um projeto de cliente só fica em git local ou em repositório privado. "
        "Pergunte ao consultor se o repositório é privado e, com o sim dele, registre com "
        f"'python3 {ESTE} --confirmar \"palavras do consultor\"'. "
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
    for url in dict.fromkeys(url for _, url in pendentes):
        atual = atual.rstrip("\n") + f"\n{url}\t{PRIVADO}\t{hoje}\t{limpo}\n"
    comum.gravar(REGISTRO, atual)
    print(f"Confirmação registrada em {comum.relativo(REGISTRO)} para: " + ", ".join(dict.fromkeys(url for _, url in pendentes)) + ".")
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
