#!/usr/bin/env python3
"""A lista do dia do consultor, em seis listas, e o follow-up do que espera o cliente.

Quem chama é o rotina.py:
    rotina.py --lista                  a lista do dia, sem gravar nada
    rotina.py --lista --abrir          grava a lista em _projeto/afazeres.md e registra os avisos
    rotina.py --cobrado ID [--resposta aprovou|cobrei|nao-cobrei|dispensada] [--nota TXT]
    rotina.py --respondida PERGUNTA    a pergunta da lista foi respondida hoje

As listas: caixa de entrada, próximas ações, aguardando o cliente, agenda
do dia, confirmar e algum dia. No topo sobem no máximo três itens, nesta
ordem: vencido sem data nova, item que trava outros ou é ameaçado por um
risco de exposição alta, prazo de entrega com menos folga e item que
espera o cliente há mais tempo sem cobrança.
"""
from __future__ import annotations

import datetime
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import comum  # noqa: E402
import rotina  # noqa: E402

GRAU = {"alta": 3, "media": 2, "baixa": 1}
EXPOSICAO_ALTA = 6  # uma alta e a outra pelo menos média
RESPOSTAS = ("aprovou", "cobrei", "nao-cobrei", "dispensada")


@dataclass
class Aberto:
    """Um item aberto do projeto, de qualquer registro."""

    ident: str
    tipo: str
    texto: str
    dono: str = ""
    lado: str = "consultoria"
    inicio: datetime.date | None = None
    prazo: datetime.date | None = None
    espera: list[str] = field(default_factory=list)  # só anda depois destes
    serve: list[str] = field(default_factory=list)   # contribui para estes, sem travar
    trava: list[str] = field(default_factory=list)   # estes só andam depois dele
    passo: str = ""


def ids(texto: str) -> list[str]:
    return [parte.strip() for parte in (texto or "").replace(";", ",").split(",") if parte.strip()]


def itens_abertos() -> dict[str, Aberto]:
    """Tudo o que está aberto: ações, pedidos de material, dependências e entregáveis, com o que cada um espera."""
    import estado

    itens: dict[str, Aberto] = {}
    tipos = {"marco": "marco", "decisao": "decisão pedida", "aprovacao": "aprovação"}
    for l in comum.ler_tsv(comum.PROJETO / "acoes.tsv"):
        if comum.normalizar(l.get("estado", "")) == "aberta":
            lado = comum.normalizar(l.get("lado", "")) or "consultoria"
            itens[l.get("id", "?")] = Aberto(l.get("id", "?"), tipos.get(comum.normalizar(l.get("tipo", "")), "ação"), l.get("item", ""), l.get("dono", ""), lado,
                                             rotina.data(l.get("inicio", "")), rotina.data(l.get("prazo", "")), ids(l.get("depende_de", "")), ids(l.get("entregavel", "")))
    for l in comum.ler_tsv(comum.INTAKE / "registro.tsv"):
        if comum.normalizar(l.get("estado", "")) in ("pedido", "em falta"):
            itens[l.get("id", "?")] = Aberto(l.get("id", "?"), "pedido de material", l.get("material", ""), l.get("pedido_a", ""), "cliente",
                                             rotina.data(l.get("pedido_em", "")), rotina.data(l.get("prazo", "")))
    for l in comum.ler_tsv(comum.PROJETO / "dependencias.tsv"):
        if comum.normalizar(l.get("estado", "")) == "aberta":
            itens[l.get("id", "?")] = Aberto(l.get("id", "?"), "dependência", l.get("item", ""), l.get("de_quem", ""), comum.normalizar(l.get("lado", "")) or "cliente",
                                             rotina.data(l.get("pedido_em", "")), rotina.data(l.get("prazo", "")), trava=ids(l.get("afeta", "")))
    for pasta in comum.entregaveis():
        meta, _ = comum.cabecalho(comum.ler(pasta / "briefing.md"))
        if comum.ETAPAS[comum.etapa(meta)] != "entregue":
            itens[pasta.name] = Aberto(pasta.name, "entregável", meta.get("titulo", pasta.name), prazo=rotina.data(meta.get("prazo", "")),
                                       espera=ids(meta.get("depende_de", "")), passo=estado.proximo_passo(pasta))
    # O que a dependência declara que afeta passa a esperar por ela.
    for item in list(itens.values()):
        for alvo in item.trava:
            if alvo in itens and item.ident not in itens[alvo].espera:
                itens[alvo].espera.append(item.ident)
        item.trava = []
    for item in itens.values():
        item.espera = [e for e in item.espera if e in itens and e != item.ident]
        item.serve = [s for s in item.serve if s in itens and s != item.ident]
    for item in itens.values():
        for e in item.espera:
            itens[e].trava.append(item.ident)
    return itens


def dependentes(itens: dict[str, Aberto], ident: str) -> list[str]:
    """Tudo o que só anda, ou só termina bem, depois deste item, em cadeia."""
    vistos: list[str] = []
    fila = [ident]
    while fila:
        atual = itens[fila.pop(0)]
        for proximo in atual.trava + atual.serve:
            if proximo not in vistos and proximo != ident:
                vistos.append(proximo)
                fila.append(proximo)
    return vistos


def espera_do_cliente(ident: str) -> list[Aberto]:
    """Os itens do cliente ou de terceiro, ainda abertos, de que este item depende."""
    itens = itens_abertos()
    if ident not in itens:
        return []
    return [itens[e] for e in itens[ident].espera if itens[e].lado != "consultoria"]


def exposicao(risco: dict) -> int:
    return GRAU.get(comum.normalizar(risco.get("probabilidade", "")), 0) * GRAU.get(comum.normalizar(risco.get("impacto", "")), 0)


def riscos_abertos() -> list[dict]:
    riscos = [l for l in comum.ler_tsv(comum.PROJETO / "riscos.tsv") if comum.normalizar(l.get("estado", "")) == "aberto"]
    return sorted(riscos, key=lambda r: -exposicao(r))


def cobrancas() -> dict[str, list[datetime.date]]:
    por_item: dict[str, list[datetime.date]] = {}
    for l in comum.ler_tsv(comum.PROJETO / "cobrancas.tsv"):
        dia = rotina.data(l.get("cobrado_em", ""))
        if dia and comum.normalizar(l.get("resposta", "")) == "cobrado":
            por_item.setdefault(l.get("item", ""), []).append(dia)
    return por_item


def ocorre_hoje(rito: dict, hoje: datetime.date) -> bool:
    desde, ate = rotina.data(rito["desde"]), rotina.data(rito.get("ate", ""))
    if hoje < desde or (ate and hoje > ate):
        return False
    cadencia = comum.normalizar(rito.get("cadencia", ""))
    if cadencia in rotina.CICLOS:
        return (hoje - desde).days % rotina.CICLOS[cadencia] == 0
    if cadencia == "mensal":
        fim_do_mes = (hoje.replace(day=28) + datetime.timedelta(days=4)).replace(day=1) - datetime.timedelta(days=1)
        return hoje.day == min(desde.day, fim_do_mes.day)
    return hoje == desde


# --- Perguntas por frequência ----------------------------------------------


def vespera_do_status(hoje: datetime.date, dia_do_status: float) -> datetime.date:
    """O último dia, até hoje, que foi véspera útil do dia do status."""
    alvo = (int(dia_do_status) - 2) % 5  # a véspera da segunda é a sexta
    dia = hoje
    while dia.weekday() != alvo:
        dia -= datetime.timedelta(days=1)
    return dia


def ultimo_marco() -> datetime.date | None:
    """O dia do último marco concluído ou do último aceite registrado."""
    dias = [rotina.data(l.get("movida_em", "")) for l in comum.ler_tsv(comum.PROJETO / "acoes.tsv")
            if comum.normalizar(l.get("tipo", "")) == "marco" and comum.normalizar(l.get("estado", "")) == "concluida"]
    dias += [rotina.data(l.get("data", "")) for l in comum.ler_tsv(comum.PROJETO / "versoes.tsv") if l.get("aceite", "")]
    return max((d for d in dias if d), default=None)


def perguntas_do_dia(hoje: datetime.date, p: dict) -> list[tuple[str, str]]:
    """As perguntas de calendário que vencem hoje: (chave, texto). As de item saem dos registros, em outra função."""
    import governanca

    vespera = vespera_do_status(hoje, p["dia_do_status"])
    piso = rotina.inicio_da_fase() or datetime.date.min
    marco = ultimo_marco()
    riscos = riscos_abertos()[:3]
    enviados = [l for l in comum.ler_tsv(comum.PROJETO / "versoes.tsv") if l.get("enviada_a", "") and not l.get("aceite", "")]
    premissas = sorted((l for l in comum.ler_tsv(comum.PROJETO / "premissas.tsv") if comum.normalizar(l.get("estado", "")) == "a confirmar"), key=lambda l: l.get("validar_ate", "") or "9999")
    adiados = [l for l in comum.ler_tsv(comum.PROJETO / "adiados.tsv") if comum.normalizar(l.get("estado", "")) == "aberto"]
    complemento = {
        "riscos": " " + "; ".join(f"{r.get('id', '?')} ({r.get('probabilidade', '?') or '?'}/{r.get('impacto', '?') or '?'}): {r.get('risco', '')}" for r in riscos) if riscos else " Nenhum risco aberto: apareceu algum?",
        "retorno": " " + "; ".join(f"{l.get('entregavel', '?')} {l.get('versao', '')}, enviada a {l.get('enviada_a', '')} em {l.get('data', '')}" for l in enviados) if enviados else None,
        "premissas": " " + "; ".join(f"{l.get('id', '?')}: {l.get('premissa', '')}" + (f" (validar até {l['validar_ate']})" if l.get("validar_ate", "") else "") for l in premissas[:3]) if premissas else None,
        "algum_dia": " " + "; ".join(f"{l.get('id', '?')}: {l.get('item', '')}" for l in adiados[:5]) if adiados else None,
        "nivel": " " + governanca.revisao(hoje) if governanca.revisao(hoje) else None,
        "materiais": "" if governanca.nivel_atual() else None,
    }
    saida = []
    caminho = comum.PROJETO / "perguntas.tsv"
    for l in comum.ler_tsv(caminho if caminho.is_file() else comum.MODELOS / "projeto" / "perguntas.tsv"):
        chave, frequencia = l.get("pergunta", ""), comum.normalizar(l.get("frequencia", ""))
        respondida = rotina.data(l.get("respondida_em", ""))
        if frequencia == "diaria":
            vence = respondida != hoje
        elif frequencia == "semanal":
            vence = (respondida or piso) < vespera
        elif frequencia == "marco":
            vence = bool(marco) and (respondida or datetime.date.min) < marco
        else:
            vence = False
        mais = complemento.get(chave, "")
        if vence and mais is not None:
            saida.append((chave, f"{l.get('texto', '')}{mais} [{chave}]"))
    return saida


def responder_pergunta(chaves: str, hoje: datetime.date) -> int:
    caminho = rotina.garantir("perguntas.tsv")
    comentarios, colunas, linhas = rotina.abrir_tsv(caminho)
    feitas = []
    for chave in ids(chaves):
        linha = next((l for l in linhas if l.get("pergunta", "") == chave), None)
        if linha is None:
            print(f"Não existe a pergunta '{chave}'. As perguntas: {', '.join(l.get('pergunta', '') for l in linhas)}.")
            return 1
        linha["respondida_em"] = str(hoje)
        feitas.append(chave)
    rotina.gravar_tsv(caminho, comentarios, colunas, linhas)
    print(f"Respondida(s) em {hoje}: {', '.join(feitas)}.")
    return 0


# --- A lista ----------------------------------------------------------------


def montar(hoje: datetime.date) -> dict:
    """As seis listas e os destaques do dia. Cada entrada é (id ou chave, texto)."""
    p = rotina.parametros()
    resumo = rotina.resumo(hoje)
    lista: dict = {"pausa": [t for _, t in resumo["pausa"]], "destaques": [], "entrada": list(resumo["chegou"]), "proximas": [], "aguardando": [], "agenda": [],
                   "confirmar": [], "algum_dia": []}
    lista["confirmar"] += [(chave, texto + ". Vale como está? Sim, corrige ou não.") for chave, texto in resumo["sim"]]
    if lista["pausa"]:
        return lista
    import cerebro
    fora = cerebro.pendentes() if cerebro.PASTA.is_dir() else []
    if fora:
        nomes = ", ".join(f.ident for f, _, _ in fora[:5]) + ("..." if len(fora) > 5 else "")
        lista["entrada"].append(("cerebro", f"Segundo cérebro: {len(fora)} item(ns) do projeto ainda fora das notas ({nomes}). Absorva com a skill manter-cerebro"))
    itens = itens_abertos()
    fases = {i.ident: rotina.fase_do_item(i, hoje, p) for i in rotina.itens_com_prazo()}
    etapas = {i.ident: i.etapas for i in rotina.itens_com_prazo()}
    feitas = cobrancas()
    riscos = [r for r in riscos_abertos() if exposicao(r) >= EXPOSICAO_ALTA]
    ameacas: dict[str, list[dict]] = {}
    for r in riscos:
        for alvo in ids(r.get("ameaca", "")):
            ameacas.setdefault(alvo, []).append(r)

    def sem_cobranca(item: Aberto) -> int:
        desde = max(feitas.get(item.ident, []), default=None) or item.inicio
        return rotina.uteis(desde, hoje) if desde and desde <= hoje else 0

    def linha(item: Aberto) -> str:
        fase, detalhe = fases.get(item.ident, ("", ""))
        texto = f"{item.ident} ({item.tipo}): {item.texto}"
        if item.passo:
            texto += f". Próximo passo: {item.passo}"
        if item.dono:
            texto += f". Dono: {item.dono}"
        if detalhe:
            texto += f". {detalhe[0].upper()}{detalhe[1:]}"
        elif item.prazo:
            texto += f". Prazo: {item.prazo}"
        if item.lado != "consultoria":
            dias = feitas.get(item.ident, [])
            texto += f". Última cobrança: {max(dias)}, {len(dias)} feita(s)" if dias else ". Nenhuma cobrança registrada"
        presos = dependentes(itens, item.ident)
        if presos:
            texto += f". Trava: {', '.join(presos)}"
        if item.ident in ameacas:
            texto += ". Risco de exposição alta: " + ", ".join(r.get("id", "?") for r in ameacas[item.ident])
        return texto

    # Destaques, na ordem combinada. No máximo três sobem.
    def peso(item: Aberto) -> int:
        return len(dependentes(itens, item.ident)) + max((exposicao(r) // 3 for r in ameacas.get(item.ident, [])), default=0)

    def folga(item: Aberto) -> int:
        return rotina.uteis(hoje, item.prazo) - etapas.get(item.ident, 0)

    candidatos: list[tuple[str, str]] = []
    longe = datetime.date.max
    for item in sorted((i for i in itens.values() if fases.get(i.ident, ("",))[0] == "vencido"), key=lambda i: (-peso(i), i.prazo or longe)):
        candidatos.append((item.ident, "está vencido e sem data nova"))
    for item in sorted((i for i in itens.values() if peso(i) > 0), key=lambda i: (-peso(i), i.prazo or longe)):
        motivos = []
        if dependentes(itens, item.ident):
            motivos.append(f"trava {len(dependentes(itens, item.ident))} item(ns)")
        if item.ident in ameacas:
            motivos.append("é ameaçado por um risco de exposição alta")
        candidatos.append((item.ident, " e ".join(motivos)))
    for item in sorted((i for i in itens.values() if fases.get(i.ident, ("",))[0] == "proximo"), key=lambda i: (folga(i), i.tipo != "entregável")):
        candidatos.append((item.ident, f"o prazo está próximo, com folga de {folga(item)} dia(s) útil(eis)"))
    for item in sorted((i for i in itens.values() if i.lado != "consultoria" and sem_cobranca(i) > p["cobrar_depois_de"]), key=lambda i: -sem_cobranca(i)):
        candidatos.append((item.ident, f"espera o cliente há {sem_cobranca(item)} dia(s) útil(eis) sem cobrança"))
    for ident, motivo in candidatos:
        if ident not in [d[0] for d in lista["destaques"]] and len(lista["destaques"]) < 3:
            lista["destaques"].append((ident, f"{linha(itens[ident])}. Sobe porque {motivo}"))

    for item in sorted(itens.values(), key=lambda i: (i.prazo or longe, i.ident)):
        if item.lado != "consultoria":
            lista["aguardando"].append((item.ident, linha(item)))
        elif not item.espera:
            lista["proximas"].append((item.ident, linha(item)))
        if item.prazo == hoje:
            lista["agenda"].append((item.ident, f"Vence hoje: {item.ident} ({item.tipo}), {item.texto}"))
    lista["agenda"] = [(r["rito"], f"Reunião: {r['rito']}" + (f", com {r['participantes']}" if r.get("participantes", "") else "")) for r in rotina.ritos() if ocorre_hoje(r, hoje)] + lista["agenda"]

    lista["confirmar"] += [(chave, texto + ". Concluído, nova data ou não é mais necessário?") for chave, texto in resumo["vencido"]]
    for item in itens.values():
        if item.lado != "consultoria" and sem_cobranca(item) > p["cobrar_depois_de"]:
            lista["confirmar"].append((f"cobranca:{item.ident}", f"{item.ident} ({item.tipo}, {item.dono or 'sem dono'}): você já fez o follow-up com o cliente? "
                                       f"Aprovou, cobrei hoje, ainda não cobrei ou não depende mais de aprovação. Sem cobrança há {sem_cobranca(item)} dia(s) útil(eis)"))
    cobrados = {chave.split(":", 1)[1] for chave, _ in lista["confirmar"] if chave.startswith("cobranca:")}  # a pergunta do follow-up já cobre o item parado
    lista["confirmar"] += [(chave, texto + ". Está andando, travou ou não é mais necessário?") for chave, texto in resumo["parado"] if chave not in cobrados]
    lista["confirmar"] += list(resumo["cadencia"])
    lista["confirmar"] += [(f"pergunta:{chave}", texto) for chave, texto in perguntas_do_dia(hoje, p)]
    lista["algum_dia"] = [(l.get("id", "?"), l.get("item", "")) for l in comum.ler_tsv(comum.PROJETO / "adiados.tsv") if comum.normalizar(l.get("estado", "")) == "aberto"]
    return lista


TITULOS = [("entrada", "Caixa de entrada"), ("proximas", "Próximas ações"), ("aguardando", "Aguardando o cliente"), ("agenda", "Agenda do dia"), ("confirmar", "Confirmar")]


def texto_da_lista(hoje: datetime.date, lista: dict, marcador: str = "- ") -> str:
    linhas = [f"Lista do dia, {hoje} ({rotina.DIAS[hoje.weekday()]})"]
    linhas += lista["pausa"]
    if lista["destaques"]:
        linhas += ["", "Atenção primeiro:"] + [f"{n}. {texto}" for n, (_, texto) in enumerate(lista["destaques"], start=1)]
    for chave, titulo in TITULOS:
        if lista[chave]:
            linhas += ["", f"{titulo} ({len(lista[chave])}):"] + [f"{marcador}{texto}" for _, texto in lista[chave]]
    if lista["algum_dia"]:
        linhas += ["", f"Algum dia: {len(lista['algum_dia'])} item(ns) adiado(s), fora da vista até a revisão semanal."]
    if len(linhas) == 1:
        linhas.append("Nada chegou, nada vence e nada espera resposta hoje.")
    return "\n".join(linhas)


def gravar(hoje: datetime.date, lista: dict) -> Path:
    caminho = comum.PROJETO / "afazeres.md"
    corpo = texto_da_lista(hoje, lista, marcador="- [ ] ").split("\n", 1)
    caminho.write_text(f"# {corpo[0]}\n\nQuem grava é o `rotina.py --lista --abrir`, a cada dia. Responda na conversa: o agente leva cada resposta ao registro.\n"
                       + (f"\n{corpo[1].lstrip()}\n" if len(corpo) > 1 else ""), encoding="utf-8")
    return caminho


# --- Follow-up do que espera o cliente -------------------------------------


def cobrado(ident: str, resposta: str, nota: str, motivo: str, quem: str, hoje: datetime.date) -> int:
    resposta = resposta or "cobrei"
    if resposta not in RESPOSTAS:
        print(f"A resposta é uma de: {', '.join(RESPOSTAS)}.")
        return 2
    itens = itens_abertos()
    item = itens.get(ident)
    if item is None or item.lado == "consultoria":
        print(f"{ident} não é um item aberto que espera o cliente. Valem as ações com lado cliente (T-nnn), os pedidos de material (M-nnn) e as dependências (DP-nnn).")
        return 1
    feitas = cobrancas().get(ident, [])
    if resposta == "nao-cobrei":
        print(f"Redija a mensagem de cobrança de {ident}, para o consultor enviar. Os fatos:")
        print(f"- O que se espera: {item.texto}. De quem: {item.dono or 'a definir'}.")
        print(f"- Pedido em {item.inicio or 'data não registrada'}, com prazo em {item.prazo or 'data não registrada'}.")
        print(f"- Cobranças já feitas: {len(feitas)}" + (f", a última em {max(feitas)}." if feitas else "."))
        presos = dependentes(itens, ident)
        print(f"- O que está parado por causa disto: {', '.join(presos)}." if presos else "- Nada registrado como parado por causa disto.")
        print(f"Quem envia é o consultor. Depois do envio, rode rotina.py --cobrado {ident}.")
        return 0
    if resposta == "dispensada":
        if not motivo:
            print("Diga em uma linha por que não depende mais do cliente (--motivo).")
            return 2
        retorno = rotina.responder(ident, "dispensar", motivo, hoje)
        if retorno:
            return retorno
    if resposta == "aprovou" and item.tipo == "pedido de material":
        print(f"{ident} é um pedido de material: quando o arquivo chegar, siga a skill receber-materiais, que muda o estado para recebido.")
        return 0
    caminho = rotina.garantir("cobrancas.tsv")
    comentarios, colunas, linhas = rotina.abrir_tsv(caminho)
    linhas.append({"item": ident, "cobrado_em": str(hoje), "quem": quem, "resposta": {"cobrei": "cobrado"}.get(resposta, resposta), "nota": nota or motivo})
    rotina.gravar_tsv(caminho, comentarios, colunas, linhas)
    _, registro = rotina.localizar(ident)
    if resposta == "cobrei":
        rotina.mudar_linha(registro, ident, {"movida_em": str(hoje)})
        print(f"Cobrança de {ident} registrada em {hoje}. É a de número {len(feitas) + 1}.")
        return 0
    if resposta == "aprovou":
        rotina.mudar_linha(registro, ident, {"estado": "atendida" if item.tipo == "dependência" else "concluida", "movida_em": str(hoje)})
        print(f"{ident}: o cliente respondeu em {hoje}. O item está fechado.")
    depois = itens_abertos()
    livres = [i for i in item.trava if i in depois and not depois[i].espera]
    if livres:
        print(f"Voltam às próximas ações: {', '.join(livres)}.")
    return 0
