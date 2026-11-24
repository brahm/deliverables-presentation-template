#!/usr/bin/env python3
"""Os materiais de governança, montados a partir dos registros do projeto.

Uso:
    emitir.py                                o que dá para emitir e a última emissão de cada material
    emitir.py status-semanal [--cor verde|amarelo|vermelho --motivo TXT]
    emitir.py status-executivo [--cor ... --motivo TXT]
    emitir.py pauta --reuniao NOME [--data AAAA-MM-DD]
    emitir.py nota-de-entrega ENTREGAVEL
    emitir.py aceite ENTREGAVEL              pedido de aceite ou, depois dele, a confirmação
    emitir.py ciclo-de-aprovacao             quem aprova cada entregável e como está cada envio
    emitir.py mudanca MU-nnn                 a solicitação de mudança, com o impacto e a decisão
    --gravar                                 grava o rascunho em _projeto/emitidos/ e registra a emissão
    --hoje AAAA-MM-DD                        calcula como se fosse este dia

Tudo sai dos registros de _projeto/. O que os registros não trazem fica
marcado com PREENCHER, para o consultor completar. O resultado é um
rascunho: quem revisa e envia é o consultor.
"""
from __future__ import annotations

import argparse
import datetime
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import afazeres  # noqa: E402
import comum  # noqa: E402
import governanca  # noqa: E402
import rotina  # noqa: E402

EMITIDOS = comum.PROJETO / "emitidos"
REGISTRO = comum.PROJETO / "emitidos.tsv"
CORES = ("verde", "amarelo", "vermelho")
MATERIAIS = {
    "status-semanal": "Status semanal de uma página",
    "status-executivo": "Status executivo para o comitê",
    "pauta": "Pauta e pré-leitura",
    "nota-de-entrega": "Nota de entrega",
    "aceite": "Confirmação ou termo de aceite",
    "ciclo-de-aprovacao": "Ciclo de aprovação com prazos",
    "mudanca": "Solicitação de mudança",
}
# Blocos da reunião operacional, com os minutos de cada um.
BLOCOS = [("Situação e objetivos da semana", 5), ("Entregas e marcos", 10), ("Riscos, issues e dependências", 15), ("Decisões e mudanças", 10), ("Ações e responsáveis", 5)]


# --- O que os registros dizem ----------------------------------------------


def projeto() -> tuple[str, str]:
    meta, _ = comum.cabecalho(comum.ler(comum.PROJETO / "brief.md"))
    limpo = lambda v: "" if comum.MARCA in v else v.strip()  # noqa: E731
    return limpo(meta.get("projeto", "")) or "Projeto", limpo(meta.get("cliente", ""))


def emissoes(codigo: str = "") -> list[dict]:
    return [l for l in comum.ler_tsv(REGISTRO) if not codigo or l.get("codigo", "") == codigo]


def desde_quando(codigo: str, hoje: datetime.date, dias: int) -> datetime.date:
    """O início do período do material: a última emissão antes de hoje ou, sem ela, `dias` atrás."""
    antes = [d for l in emissoes(codigo) if (d := rotina.data(l.get("data", ""))) and d < hoje]
    return max(antes) if antes else hoje - datetime.timedelta(days=dias)


def emite(codigo: str) -> bool:
    """O projeto mantém este material na lista do nível?"""
    mantidos = {l.get("codigo", "") for l in governanca.mantidos()}
    if codigo == "aceite":
        return bool(mantidos & {"aceite", "termo-de-aceite"})
    return codigo in mantidos


def papel(ident: str) -> dict:
    return next((l for l in comum.ler_tsv(comum.PROJETO / "papeis.tsv") if l.get("item", "") == ident), {})


def versoes_de(ident: str) -> list[dict]:
    return [l for l in comum.ler_tsv(comum.PROJETO / "versoes.tsv") if l.get("entregavel", "") == ident]


def acoes(tipo: str = "", estado: str = "aberta") -> list[dict]:
    return [l for l in comum.ler_tsv(comum.PROJETO / "acoes.tsv")
            if comum.normalizar(l.get("estado", "")) == estado and (not tipo or comum.normalizar(l.get("tipo", "")) == tipo)]


def mudancas(*estados: str) -> list[dict]:
    return [l for l in comum.ler_tsv(comum.PROJETO / "mudancas.tsv") if comum.normalizar(l.get("estado", "")) in estados]


def issues_abertas() -> list[dict]:
    return [l for l in comum.ler_tsv(comum.PROJETO / "issues.tsv") if comum.normalizar(l.get("estado", "")) == "aberta"]


def vencidos(hoje: datetime.date) -> list[rotina.Item]:
    return [i for i in rotina.itens_com_prazo() if hoje > i.prazo]


def semaforo(hoje: datetime.date) -> tuple[str, list[str]]:
    """A cor pela regra e os motivos. A cor diz o prognóstico: o compromisso está ameaçado ou não."""
    p = rotina.parametros()
    desvios = governanca.desvios(hoje)
    vermelho = [texto for _, _, acima, texto in desvios if acima]
    vermelho += [f"{l.get('id', '?')}: issue escalada, {l.get('problema', '')}" for l in issues_abertas() if comum.normalizar(l.get("escalada", "")) == "sim"]
    if vermelho:
        return "vermelho", vermelho
    amarelo = [texto for _, dias, _, texto in desvios if dias > 0]
    fora = {texto.split(":", 1)[0] for texto in amarelo}
    amarelo += [f"{i.ident} ({i.tipo}): venceu em {i.prazo} e está sem data nova" for i in vencidos(hoje) if i.ident not in fora]
    amarelo += [f"{r.get('id', '?')}: risco de exposição alta, {r.get('risco', '')}" for r in afazeres.riscos_abertos() if afazeres.exposicao(r) >= afazeres.EXPOSICAO_ALTA]
    if amarelo:
        return "amarelo", amarelo
    _, base = governanca.ultima_base()
    return "verde", ["Nenhum desvio contra a linha de base, nenhum item vencido e nenhum risco de exposição alta." if base
                     else f"Nenhum item vencido e nenhum risco de exposição alta. O projeto ainda não tem linha de base, e por isso o desvio de prazo não foi medido (tolerância de {int(p['tolerancia_de_prazo'])} dias úteis)."]


def linhas_do_semaforo(hoje: datetime.date, cor: str, motivo: str) -> list[str]:
    pela_regra, motivos = semaforo(hoje)
    if cor and cor != pela_regra:
        return [f"**Semáforo: {cor}.** Definido pelo consultor: {motivo}", "", f"Pela regra, a cor seria {pela_regra}:"] + [f"- {m}" for m in motivos[:5]]
    return [f"**Semáforo: {pela_regra}.**"] + [f"- {m}" for m in motivos[:5]]


def feito(desde: datetime.date, hoje: datetime.date) -> list[str]:
    no_periodo = lambda d: bool(d) and desde < d <= hoje  # noqa: E731
    saida = [f"{l.get('id', '?')}: {l.get('item', '')}, concluído em {l.get('movida_em', '')}" for l in acoes(estado="concluida") if no_periodo(rotina.data(l.get("movida_em", "")))]
    for l in comum.ler_tsv(comum.PROJETO / "versoes.tsv"):
        if no_periodo(rotina.data(l.get("data", ""))):
            saida.append(f"{l.get('entregavel', '?')} {l.get('versao', '')}: {l.get('o_que_mudou', '')}" + (f", enviada a {l['enviada_a']}" if l.get("enviada_a", "") else "") + f", em {l.get('data', '')}")
        aceite = l.get("aceite", "")
        if aceite and no_periodo(data_do_aceite(aceite)):
            saida.append(f"{l.get('entregavel', '?')} {l.get('versao', '')}: aceite de {aceite}")
    saida += [f"Reunião de {l.get('data', '')}: {l.get('reuniao', '')}" + (f", {l['resultado']}" if l.get("resultado", "") else "")
              for l in comum.ler_tsv(comum.PROJETO / "reunioes.tsv") if no_periodo(rotina.data(l.get("data", ""))) and comum.normalizar(l.get("situacao", "")) in ("realizada", "ata processada")]
    return saida


def data_do_aceite(aceite: str) -> datetime.date | None:
    achado = re.search(r"\d{4}-\d{2}-\d{2}", aceite or "")
    return rotina.data(achado.group(0)) if achado else None


def a_fazer(hoje: datetime.date, dias: int = 7) -> list[str]:
    ate = hoje + datetime.timedelta(days=dias)
    itens = sorted((i for i in afazeres.itens_abertos().values() if i.lado == "consultoria" and (i.tipo == "entregável" or (i.prazo and i.prazo <= ate))),
                   key=lambda i: (i.prazo or datetime.date.max, i.ident))
    return [f"{i.ident} ({i.tipo}): {i.texto}" + (f". Próximo passo: {i.passo}" if i.passo else "") + (f". Prazo: {i.prazo}" if i.prazo else "") for i in itens]


def tabela_de_marcos(hoje: datetime.date) -> list[str]:
    versao, base = governanca.ultima_base()
    if not base:
        return ["O projeto ainda não tem linha de base. As datas abaixo são as de hoje."] + [
            f"- {i['item']} ({i['tipo']}): {i['descricao']}, {i['data']}" + ("" if i["aberto"] else ", concluído") for i in governanca.itens_da_base()]
    atuais = {i["item"]: i for i in governanca.itens_da_base()}
    desvio = {ident: dias for ident, dias, _, _ in governanca.desvios(hoje)}
    linhas = [f"Linha de base versão {versao}.", "", "| Item | Linha de base | Previsto hoje | Situação |", "| --- | --- | --- | --- |"]
    for l in base:
        atual = atuais.get(l["item"])
        if atual is None:
            linhas.append(f"| {l['item']}: {l.get('descricao', '')} | {l.get('data_base', '')} | fora do plano | saiu do plano |")
            continue
        dias = desvio.get(l["item"], 0)
        situacao = "concluído" if not atual["aberto"] else ("vencido sem data nova" if rotina.data(atual["data"]) < hoje else "no prazo")
        if dias:
            situacao += f", {abs(dias)} dia(s) útil(eis) {'depois' if dias > 0 else 'antes'}"
        linhas.append(f"| {l['item']}: {l.get('descricao', '')} | {l.get('data_base', '')} | {atual['data']} | {situacao} |")
    return linhas


def riscos_e_issues(limite: int) -> list[str]:
    saida = [f"{l.get('id', '?')} (issue{', escalada' if comum.normalizar(l.get('escalada', '')) == 'sim' else ''}): {l.get('problema', '')}. Ação: {l.get('acao', '') or comum.MARCA}"
             + (f". Dono: {l['dono']}" if l.get("dono", "") else "") + (f". Prazo: {l['prazo']}" if l.get("prazo", "") else "") for l in issues_abertas()]
    saida += [f"{r.get('id', '?')} (risco, {r.get('probabilidade', '?') or '?'}/{r.get('impacto', '?') or '?'}): {r.get('risco', '')}. Resposta: {r.get('resposta', '') or comum.MARCA}"
              + (f". Dono: {r['dono']}" if r.get("dono", "") else "") for r in afazeres.riscos_abertos()]
    return saida[:limite]


def decisoes_pedidas() -> list[str]:
    saida = [f"{l.get('id', '?')}: {l.get('item', '')}. Quem decide: {l.get('dono', '') or comum.MARCA}. Até: {l.get('prazo', '') or comum.MARCA}" for l in acoes("decisao")]
    saida += [f"{l.get('id', '?')}: mudança pedida por {l.get('solicitante', '') or '?'}, {l.get('pedido', '')}. Impacto: {impacto(l)}" for l in mudancas("em analise")]
    return saida


def impacto(l: dict) -> str:
    partes = [f"{nome} {l[campo]}" for campo, nome in (("impacto_prazo", "prazo"), ("impacto_esforco", "esforço"), ("impacto_escopo", "escopo")) if l.get(campo, "")]
    return "; ".join(partes) if partes else "ainda não analisado"


def pendencias_do_cliente(hoje: datetime.date) -> list[str]:
    itens = afazeres.itens_abertos()
    feitas = afazeres.cobrancas()
    saida = []
    for i in sorted((i for i in itens.values() if i.lado != "consultoria"), key=lambda i: (i.prazo or datetime.date.max, i.ident)):
        texto = f"{i.ident} ({i.tipo}): {i.texto}. Com: {i.dono or 'a definir'}"
        if i.prazo:
            texto += f". Prazo: {i.prazo}" + (f", vencido há {rotina.uteis(i.prazo, hoje)} dia(s) útil(eis)" if hoje > i.prazo else "")
        dias = feitas.get(i.ident, [])
        texto += f". Cobranças: {len(dias)}, a última em {max(dias)}" if dias else ". Nenhuma cobrança registrada"
        presos = afazeres.dependentes(itens, i.ident)
        if presos:
            texto += f". Trava: {', '.join(presos)}"
        saida.append(texto)
    for pasta in comum.entregaveis():
        versoes = versoes_de(pasta.name)
        v = versoes[-1] if versoes else {}
        if v.get("enviada_a", "") and not v.get("aceite", "") and not governanca.aprovacao_aberta(pasta.name):
            limite = governanca.somar_uteis(rotina.data(v.get("data", "")) or hoje, governanca.prazo_de_resposta(pasta.name))
            saida.append(f"{pasta.name} {v.get('versao', '')}: enviada a {v['enviada_a']} em {v.get('data', '')}, sem aceite registrado. Resposta esperada até {limite}")
    return saida


def secao(titulo: str, linhas: list[str], vazio: str = "", marcador: str = "- ") -> list[str]:
    """Uma seção do material. Sem linhas e sem texto para o vazio, a seção não sai."""
    if not linhas and not vazio:
        return []
    corpo = [linha if linha.startswith(("|", "**")) or not linha or not marcador else f"{marcador}{linha}" for linha in linhas] if linhas else [vazio]
    return ["", f"## {titulo}", ""] + corpo


def cabecalho(titulo: str, hoje: datetime.date, extra: str = "") -> list[str]:
    nome, cliente = projeto()
    return [f"# {titulo}", "", f"{nome}" + (f", {cliente}" if cliente else "") + f". {extra or 'Emitido em ' + str(hoje)}.",
            "", "Rascunho montado a partir dos registros do projeto. Quem revisa e envia é o consultor."]


# --- Os materiais -----------------------------------------------------------


def status_semanal(hoje: datetime.date, cor: str, motivo: str) -> list[str]:
    desde = desde_quando("status-semanal", hoje, 7)
    texto = cabecalho("Status semanal", hoje, f"Período de {desde + datetime.timedelta(days=1)} a {hoje}")
    texto += [""] + linhas_do_semaforo(hoje, cor, motivo)
    texto += secao("Feito no período", feito(desde, hoje), "Nenhuma conclusão, envio ou reunião registrada no período.")
    texto += secao("A fazer na próxima semana", a_fazer(hoje), "Nenhum item da consultoria com prazo nos próximos sete dias.")
    texto += secao("Marcos", tabela_de_marcos(hoje), "Nenhum entregável com prazo e nenhum marco registrado.", marcador="")
    texto += secao("Riscos e issues", riscos_e_issues(3), "Nenhum risco e nenhuma issue em aberto.")
    texto += secao("Decisões pedidas", decisoes_pedidas(), "Nenhuma decisão pendente.")
    texto += secao("Pendências do cliente", pendencias_do_cliente(hoje), "Nada depende do cliente hoje.")
    texto += secao("Datas deslocadas", [linha.lstrip("- ").strip() for linha in rotina.datas_deslocadas()])
    return texto


def status_executivo(hoje: datetime.date, cor: str, motivo: str) -> list[str]:
    desde = desde_quando("status-executivo", hoje, 30)
    texto = cabecalho("Status executivo", hoje, f"Período de {desde + datetime.timedelta(days=1)} a {hoje}")
    texto += secao("1. O projeto está no compromisso?", linhas_do_semaforo(hoje, cor, motivo) + [""] + tabela_de_marcos(hoje), marcador="")
    entregue = [linha for linha in feito(desde, hoje) if not linha.startswith("Reunião")]
    texto += secao("2. O que foi entregue", entregue, "Nenhuma conclusão e nenhum envio registrado no período.")
    proximos = sorted((i for i in governanca.itens_da_base() if i["aberto"]), key=lambda i: i["data"])
    texto += secao("3. Qual é o prognóstico", [f"{i['item']} ({i['tipo']}): {i['descricao']}, previsto para {i['data']}" for i in proximos]
                   + [f"Leitura do consultor sobre a data final e o que a sustenta: {comum.MARCA}"])
    texto += secao("4. Que riscos ameaçam", riscos_e_issues(5), "Nenhum risco e nenhuma issue em aberto.")
    pedidas = decisoes_pedidas()
    texto += secao("5. O que precisa ser decidido", [f"{linha}. Opções e recomendação: {comum.MARCA}" for linha in pedidas], "Nenhuma decisão pendente.")
    decididas = [f"{l.get('id', '?')} ({l.get('estado', '')} em {l.get('decidido_em', '') or '?'}): {l.get('pedido', '')}. Impacto: {impacto(l)}" for l in mudancas("aprovada", "rejeitada")]
    texto += secao("Mudanças", decididas)
    return texto


def pauta(hoje: datetime.date, reuniao: str, dia: datetime.date | None) -> list[str]:
    rito = next((r for r in rotina.ritos() if comum.normalizar(r["rito"]) == comum.normalizar(reuniao)), {})
    texto = cabecalho(f"Pauta: {rito.get('rito', reuniao)}", hoje, f"Reunião de {dia or comum.MARCA}")
    texto += ["", f"Participantes: {rito.get('participantes', '') or comum.MARCA}.", f"Objetivo: {comum.MARCA}"]
    pedidas = decisoes_pedidas()
    texto += secao("Decisões esperadas", pedidas, "Nenhuma decisão pendente nos registros. Se a reunião não decide nada, uma mensagem com o status pode bastar.")
    cor, motivos = semaforo(hoje)
    marcos = [f"{i['item']}: {i['descricao']}, {i['data']}" for i in sorted(governanca.itens_da_base(), key=lambda i: i["data"]) if i["aberto"]]
    abertas = [f"{l.get('id', '?')}: {l.get('item', '')}. Dono: {l.get('dono', '') or 'a definir'}. Prazo: {l.get('prazo', '') or 'a definir'}" for l in acoes()]
    conteudo = [[f"Semáforo {cor}: {motivos[0]}"], marcos, riscos_e_issues(5) + [l for l in pendencias_do_cliente(hoje) if "(dependência)" in l], pedidas, abertas]
    for (titulo, minutos), itens in zip(BLOCOS, conteudo):
        texto += secao(f"{titulo} ({minutos} min)", itens, "Nada nos registros para este bloco.")
    ultimo = max(emissoes("status-semanal") + emissoes("status-executivo"), key=lambda l: l.get("data", ""), default=None)
    enviados = [f"{l.get('entregavel', '?')} {l.get('versao', '')}, enviada em {l.get('data', '')}" for l in comum.ler_tsv(comum.PROJETO / "versoes.tsv") if l.get("enviada_a", "") and not l.get("aceite", "")]
    texto += secao("Material de leitura", ([f"Último status: {ultimo.get('arquivo', '')}"] if ultimo else []) + enviados, "Nenhum material de leitura nos registros.")
    return texto


def ultima_versao(ident: str) -> dict:
    governanca.pasta_do_entregavel(ident)
    versoes = versoes_de(ident)
    if not versoes:
        raise SystemExit(f"{ident} ainda não tem versão registrada. Registre o envio com governanca.py --versao {ident} --mudou \"...\" --enviada-a \"...\".")
    return versoes[-1]


def titulo_do(ident: str) -> str:
    meta, _ = comum.cabecalho(comum.ler(comum.BASE / ident / "briefing.md"))
    return meta.get("titulo", "").strip() or ident


def nota_de_entrega(hoje: datetime.date, ident: str) -> list[str]:
    v, quem = ultima_versao(ident), papel(ident)
    prazo = governanca.prazo_de_resposta(ident)
    texto = cabecalho(f"Nota de entrega: {titulo_do(ident)}", hoje)
    texto += secao("O que está sendo entregue", [f"{ident}, versão {v.get('versao', '')}, de {v.get('data', '')}.", f"O que mudou nesta versão: {v.get('o_que_mudou', '')}",
                                                 f"Enviada a: {v.get('enviada_a', '') or comum.MARCA}"])
    adiados = [f"{l.get('id', '?')}: {l.get('item', '')}. {l.get('motivo', '')}" for l in comum.ler_tsv(comum.PROJETO / "adiados.tsv") if comum.normalizar(l.get("estado", "")) == "aberto"]
    texto += secao("Pendências conhecidas", adiados, "Nenhuma pendência registrada.")
    limite = governanca.somar_uteis(rotina.data(v.get("data", "")) or hoje, prazo)
    texto += secao("O que se espera do cliente", [f"Quem aprova: {quem.get('aprova', '') or comum.MARCA}.", f"Resposta até {limite}, {prazo} dia(s) útil(eis) depois do envio: aceite, aceite com ressalvas ou pedido de ajuste.",
                                                  "O silêncio não vale como aceite. Sem resposta até a data, o item entra no status como pendência do cliente."])
    return texto


def marco_de_pagamento(ident: str) -> dict:
    """O marco de pagamento ligado ao entregável, quando o registro de ações traz um."""
    for l in comum.ler_tsv(comum.PROJETO / "acoes.tsv"):
        ligado = ident in afazeres.ids(l.get("entregavel", "")) + afazeres.ids(l.get("depende_de", ""))
        if comum.normalizar(l.get("tipo", "")) == "marco" and "pagamento" in comum.normalizar(l.get("item", "")) and ligado and comum.normalizar(l.get("estado", "")) != "cancelada":
            return l
    return {}


def aceite(hoje: datetime.date, ident: str) -> list[str]:
    v, quem = ultima_versao(ident), papel(ident)
    formal = "termo-de-aceite" in {l.get("codigo", "") for l in governanca.mantidos()}
    aprovador = quem.get("aprova", "") or comum.MARCA
    dados = [f"Entregável: {titulo_do(ident)} ({ident}).", f"Versão: {v.get('versao', '')}, de {v.get('data', '')}. {v.get('o_que_mudou', '')}", f"Aprovador: {aprovador}."]
    if not v.get("aceite", ""):
        prazo = governanca.prazo_de_resposta(ident)
        limite = governanca.somar_uteis(rotina.data(v.get("data", "")) or hoje, prazo)
        texto = cabecalho(f"{'Termo' if formal else 'Pedido'} de aceite: {titulo_do(ident)}", hoje) + [""] + dados
        if formal:
            texto += secao("Critérios de aceite", [f"Critérios combinados para este entregável e a situação de cada um: {comum.MARCA}"])
            texto += secao("Decisão do aprovador", ["( ) Aceito sem ressalvas", "( ) Aceito com ressalvas: ____", "( ) Não aceito. Ajustes pedidos: ____", "", f"Nome: {aprovador}", "Data: ____"], marcador="")
        else:
            texto += ["", f"Pedimos a confirmação até {limite}: aceito, aceito com ressalvas ou os ajustes que faltam. Uma resposta a esta mensagem basta."]
        texto += ["", f"O aceite ainda não foi registrado. A resposta é esperada até {limite}, e o silêncio não vale como aceite.",
                  f"Quando o cliente responder: governanca.py --aceite {ident} --quem \"NOME\" [--ressalvas \"...\"]."]
        return texto
    texto = cabecalho(f"{'Termo' if formal else 'Confirmação'} de aceite: {titulo_do(ident)}", hoje) + [""] + dados + [f"Aceite registrado: {v['aceite']}."]
    marco = marco_de_pagamento(ident)
    if marco:
        texto += secao("Aviso de faturamento", [f"O aceite cumpre a condição do marco {marco.get('id', '?')}: {marco.get('item', '')}.", "Evidência: a mensagem ou a ata em que o cliente aceitou. Guarde junto do registro.",
                                               "Quem emite a cobrança é a consultoria, fora do harness."])
    return texto


def ciclo_de_aprovacao(hoje: datetime.date) -> list[str]:
    texto = cabecalho("Ciclo de aprovação", hoje)
    feitas = afazeres.cobrancas()
    linhas = ["| Entregável | Aprovador | Prazo de resposta | Última versão | Situação |", "| --- | --- | --- | --- | --- |"]
    for pasta in comum.entregaveis():
        ident, quem = pasta.name, papel(pasta.name)
        prazo = governanca.prazo_de_resposta(ident)
        versoes = versoes_de(ident)
        v = versoes[-1] if versoes else {}
        if not v:
            situacao = "nenhuma versão enviada"
        elif v.get("aceite", ""):
            situacao = f"aceito: {v['aceite']}"
        elif not v.get("enviada_a", ""):
            situacao = "versão registrada, ainda não enviada"
        else:
            limite = governanca.somar_uteis(rotina.data(v.get("data", "")) or hoje, prazo)
            aberta = governanca.aprovacao_aberta(ident)
            cobrancas = len(feitas.get(aberta.get("id", ""), [])) if aberta else 0
            situacao = (f"sem resposta, vencido em {limite}, há {rotina.uteis(limite, hoje)} dia(s) útil(eis). O silêncio não vale como aceite" if hoje > limite else f"aguardando a resposta até {limite}")
            situacao += f". Cobranças: {cobrancas}" + (f" ({aberta['id']})" if aberta else "")
        linhas.append(f"| {ident} | {quem.get('aprova', '') or comum.MARCA} | {prazo} dia(s) útil(eis) | {(v.get('versao', '') + ', ' + v.get('data', '')) if v else ''} | {situacao} |")
    texto += secao("Quem aprova e como está cada envio", linhas if len(linhas) > 2 else [], "Nenhum entregável registrado.", marcador="")
    texto += ["", "Regra do silêncio: sem resposta no prazo, o envio não está aceito. O item é cobrado pelo follow-up e sobe ao status como pendência do cliente."]
    return texto


def mudanca(hoje: datetime.date, ident: str) -> list[str]:
    l = next((m for m in comum.ler_tsv(comum.PROJETO / "mudancas.tsv") if m.get("id", "") == ident), None)
    if l is None:
        raise SystemExit(f"Não achei a mudança '{ident}' em _projeto/mudancas.tsv.")
    estado = comum.normalizar(l.get("estado", ""))
    texto = cabecalho(f"Solicitação de mudança {ident}", hoje)
    texto += secao("Pedido", [f"{l.get('pedido', '')}", f"Solicitante: {l.get('solicitante', '') or comum.MARCA}. Pedido em {l.get('pedido_em', '') or comum.MARCA}."])
    versao, _ = governanca.ultima_base()
    falta = "Ainda não analisado. Rode governanca.py --analisar." if estado == "proposta" else comum.MARCA
    texto += secao("Impacto", [f"Prazo: {l.get('impacto_prazo', '') or falta}", f"Esforço: {l.get('impacto_esforco', '') or falta}", f"Escopo: {l.get('impacto_escopo', '') or falta}",
                               f"Referência: linha de base versão {versao}." if versao else "O projeto ainda não tem linha de base para medir o impacto."])
    if estado in ("aprovada", "rejeitada"):
        texto += secao("Decisão", [f"{estado.capitalize()} em {l.get('decidido_em', '') or '?'}. {l.get('decisao', '')}".strip()])
    else:
        texto += secao("Decisão", ["( ) Aprovada", "( ) Rejeitada", "", f"Quem decide: {papel('mudanca').get('aprova', '') or comum.MARCA}", "Data: ____"], marcador="")
        texto += ["", "Nenhum trabalho deste pedido começa antes da decisão."]
    return texto


# --- Emissão ----------------------------------------------------------------


def listar() -> int:
    nivel = governanca.nivel_atual()
    print("Materiais que o emitir.py monta a partir dos registros:")
    for codigo, nome in MATERIAIS.items():
        ultimas = [l.get("data", "") for l in emissoes(codigo)]
        situacao = "na lista do projeto" if emite(codigo) else ("fora da lista do projeto" if nivel else "nível não definido")
        print(f"  {codigo}: {nome}. {situacao.capitalize()}" + (f". Última emissão: {max(ultimas)}" if ultimas else "") + ".")
    print("Os outros materiais do catálogo são montados à mão, pela linha de cada um em _projeto/governanca.tsv.")
    return 0


def gravar(codigo: str, alvo: str, hoje: datetime.date, texto: str) -> Path:
    EMITIDOS.mkdir(parents=True, exist_ok=True)
    sufixo = "-" + re.sub(r"[^a-z0-9]+", "-", comum.normalizar(alvo)).strip("-") if alvo else ""
    caminho = EMITIDOS / f"{hoje}-{codigo}{sufixo}.md"
    caminho.write_text(texto, encoding="utf-8")
    registro = rotina.garantir("emitidos.tsv")
    comentarios, colunas, linhas = rotina.abrir_tsv(registro)
    arquivo = comum.relativo(caminho)
    linhas = [l for l in linhas if l.get("arquivo", "") != arquivo]
    linhas.append({"data": str(hoje), "codigo": codigo, "alvo": alvo, "arquivo": arquivo, "situacao": "rascunho"})
    rotina.gravar_tsv(registro, comentarios, colunas, linhas)
    return caminho


def status_do_dia(hoje: datetime.date) -> str:
    """A linha da agenda no dia do status, quando o status semanal ainda não saiu nesta semana."""
    if not emite("status-semanal") or hoje.weekday() + 1 != int(rotina.parametros()["dia_do_status"]):
        return ""
    if any(rotina.data(l.get("data", "")) == hoje for l in emissoes("status-semanal")):
        return ""
    return "Dia do status semanal: monte o rascunho com emitir.py status-semanal --gravar e leve ao consultor"


def main() -> int:
    analisador = argparse.ArgumentParser(description="Monta os materiais de governança a partir dos registros.")
    analisador.add_argument("material", nargs="?", choices=list(MATERIAIS) + ["termo-de-aceite"])
    analisador.add_argument("alvo", nargs="?", default="")
    analisador.add_argument("--cor", choices=CORES)
    analisador.add_argument("--motivo", default="")
    analisador.add_argument("--reuniao", default="")
    analisador.add_argument("--data", default="")
    analisador.add_argument("--gravar", action="store_true")
    analisador.add_argument("--hoje", default="")
    args = analisador.parse_args()
    hoje = rotina.data(args.hoje) or datetime.date.today()
    codigo = "aceite" if args.material == "termo-de-aceite" else args.material
    if not codigo:
        return listar()
    if args.cor and not args.motivo:
        print("A cor trocada pelo consultor pede a justificativa em uma linha (--motivo).")
        return 2
    if codigo in ("nota-de-entrega", "aceite", "mudanca") and not args.alvo:
        print(f"Diga de que item é o material: emitir.py {codigo} " + ("MU-nnn." if codigo == "mudanca" else "ENTREGAVEL."))
        return 2
    alvo = args.alvo
    if codigo == "status-semanal":
        linhas = status_semanal(hoje, args.cor, args.motivo)
    elif codigo == "status-executivo":
        linhas = status_executivo(hoje, args.cor, args.motivo)
    elif codigo == "pauta":
        if not args.reuniao:
            nomes = ", ".join(r["rito"] for r in rotina.ritos()) or "nenhuma no registro de ritos"
            print(f"Diga de que reunião é a pauta (--reuniao). Reuniões que se repetem: {nomes}.")
            return 2
        alvo = args.reuniao
        linhas = pauta(hoje, args.reuniao, rotina.data(args.data))
    elif codigo == "nota-de-entrega":
        linhas = nota_de_entrega(hoje, alvo)
    elif codigo == "aceite":
        linhas = aceite(hoje, alvo)
    elif codigo == "ciclo-de-aprovacao":
        linhas = ciclo_de_aprovacao(hoje)
    else:
        linhas = mudanca(hoje, alvo)
    texto = "\n".join(linhas) + "\n"
    print(texto, end="")
    faltam = texto.count(comum.MARCA)
    rodape = []
    if faltam:
        rodape.append(f"{faltam} ponto(s) marcado(s) com {comum.MARCA}: os registros não trazem o dado. Complete com o consultor antes do envio.")
    if governanca.nivel_atual() and not emite(codigo):
        rodape.append(f"O projeto não tem este material na lista do nível. Para passar a emitir: governanca.py --incluir {'termo-de-aceite' if args.material == 'termo-de-aceite' else codigo}.")
    if args.gravar:
        rodape.append(f"Rascunho gravado em {comum.relativo(gravar(codigo, alvo, hoje, texto))}. Passe o texto pela skill humanizar-texto e leve ao consultor, que é quem envia.")
    if rodape:
        print("\n---\n" + "\n".join(rodape), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
