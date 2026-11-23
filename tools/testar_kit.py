#!/usr/bin/env python3
"""Testes do próprio kit. Só serve ao repositório do template.

Instala o harness em pastas temporárias e confere o instalador, as
skills, as checagens e os hooks. Cada checagem é provada dos dois lados:
passa em um exemplo bom e reprova no erro que ela existe para pegar.

Uso: python3 tools/testar_kit.py
"""
from __future__ import annotations

import http.server
import json
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
HARNESS = RAIZ / "entregaveis" / "_harness"
PY = sys.executable

falhas: list[str] = []
total = 0


def confere(nome: str, condicao: bool, detalhe: str = "") -> None:
    global total
    total += 1
    if not condicao:
        falhas.append(nome + (f"\n      {detalhe.strip()[:600]}" if detalhe else ""))
        print(f"  FALHOU  {nome}")


def rodar(args: list, cwd: Path, entrada: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([str(a) for a in args], cwd=cwd, input=entrada, capture_output=True, text=True, timeout=120)


def instalar(destino: Path, *opcoes: str) -> subprocess.CompletedProcess:
    return rodar([PY, HARNESS / "scripts" / "instalar.py", "--destino", destino, *opcoes], RAIZ)


# --- Skills e documentos --------------------------------------------------


def testar_skills() -> None:
    print("Skills e regras")
    regras = (HARNESS / "REGRAS.md").read_text(encoding="utf-8")
    citadas = set(re.findall(r"\|\s*`([a-z-]+)`\s*\|", regras))
    pastas = {p.name for p in (RAIZ / ".claude" / "skills").iterdir() if p.is_dir()}
    confere("toda skill da tabela de momentos existe", citadas <= pastas, str(citadas - pastas))
    confere("toda skill do kit está na tabela de momentos", pastas <= citadas, str(pastas - citadas))
    for nome in sorted(pastas):
        texto = (RAIZ / ".claude" / "skills" / nome / "SKILL.md").read_text(encoding="utf-8")
        partes = texto.split("---\n")
        cabecalho = partes[1] if len(partes) > 2 and partes[0] == "" else ""
        campos = dict(re.findall(r"^(\w+): (.*)$", cabecalho, flags=re.MULTILINE))
        descricao = campos.get("description", "")
        confere(f"{nome}: o nome do cabeçalho é o da pasta", campos.get("name") == nome)
        confere(f"{nome}: a descrição começa por 'Use' e diz o momento", descricao.startswith("Use "))
        confere(f"{nome}: a descrição é um valor YAML simples", ": " not in descricao and " #" not in descricao and len(descricao) <= 1024, descricao)
        confere(f"{nome}: traz a marca de origem do kit", "origem: harness-de-entregaveis" in cabecalho)
        confere(f"{nome}: cabe em uma tela", len(texto.splitlines()) <= 90, f"{len(texto.splitlines())} linhas")


def testar_referencias() -> None:
    print("Referências entre arquivos")
    arquivos = [RAIZ / n for n in ("README.md", "INSTALL.md", "HISTORY.md", "AGENTS.md", "CLAUDE.md")]
    arquivos += sorted(HARNESS.rglob("*.md")) + sorted((RAIZ / ".claude" / "skills").rglob("*.md"))
    for arquivo in arquivos:
        if not arquivo.is_file():
            confere(f"{arquivo.relative_to(RAIZ)} existe", False)
            continue
        texto = arquivo.read_text(encoding="utf-8")
        for alvo in re.findall(r"\]\((?!https?:|#|mailto:)([^)#]+)(?:#[^)]*)?\)", texto):
            confere(f"{arquivo.relative_to(RAIZ)}: o link '{alvo}' existe", (arquivo.parent / alvo).exists())
        for alvo in re.findall(r"`(entregaveis/_harness/[\w./-]+|\.claude/skills/[a-z-]+/SKILL\.md|tools/[\w./-]+)`", texto):
            confere(f"{arquivo.relative_to(RAIZ)}: o caminho '{alvo}' existe", (RAIZ / alvo.rstrip("/")).exists())


def testar_texto_do_kit() -> None:
    """O kit segue as práticas de texto que cobra dos entregáveis."""
    print("Texto do próprio kit")
    sys.path.insert(0, str(HARNESS / "scripts"))
    import checagens  # noqa: PLC0415

    arquivos = [RAIZ / n for n in ("README.md", "INSTALL.md", "HISTORY.md")]
    arquivos += sorted(HARNESS.rglob("*.md")) + sorted((RAIZ / ".claude" / "skills").rglob("*.md"))
    for arquivo in arquivos:
        erros = [a for a in checagens.texto(arquivo, ["pt"]) if a.nivel == "erro"]
        confere(f"{arquivo.relative_to(RAIZ)}: sem vício de texto", not erros, "\n".join(a.formatar() for a in erros[:5]))


# --- Instalador -----------------------------------------------------------


def testar_instalador(tmp: Path) -> None:
    print("Instalador")
    vazio = tmp / "vazio"
    vazio.mkdir()
    (vazio / ".git").mkdir()
    simulacao = instalar(vazio, "--simular")
    confere("--simular não grava nada", simulacao.returncode == 0 and sorted(p.name for p in vazio.iterdir()) == [".git"], simulacao.stdout + simulacao.stderr)
    primeira = instalar(vazio, "--ci")
    confere("instala em pasta vazia", primeira.returncode == 0 and (vazio / "entregaveis/_harness/REGRAS.md").is_file(), primeira.stdout + primeira.stderr)
    confere("cria os registros do projeto", (vazio / "entregaveis/_projeto/brief.md").is_file() and (vazio / "entregaveis/_intake/materiais/.gitkeep").is_file())
    segunda = instalar(vazio, "--ci")
    confere("rodar de novo não muda nada", "Nada a fazer" in segunda.stdout, segunda.stdout)

    # A raiz do template é igual ao que o instalador põe em um projeto novo.
    for nome in ("AGENTS.md", "CLAUDE.md", ".claude/settings.json", ".gitignore", ".github/workflows/entregaveis.yml"):
        igual = (RAIZ / nome).is_file() and (RAIZ / nome).read_text(encoding="utf-8") == (vazio / nome).read_text(encoding="utf-8")
        confere(f"{nome} da raiz é igual ao de uma instalação nova", igual)
    json.loads((vazio / ".claude/settings.json").read_text(encoding="utf-8"))
    confere("a licença acompanha o harness", (HARNESS / "LICENCA.txt").read_text(encoding="utf-8") == (RAIZ / "LICENSE").read_text(encoding="utf-8"))

    # Projeto em andamento, com regras, hooks, skill e pasta de mesmo nome.
    andamento = tmp / "andamento"
    (andamento / ".claude/skills/humanizar-texto").mkdir(parents=True)
    (andamento / ".github").mkdir()
    (andamento / "entregaveis/final").mkdir(parents=True)
    (andamento / ".git").mkdir()
    (andamento / "AGENTS.md").write_text("# Meu projeto\n\nRegras minhas.\n", encoding="utf-8")
    (andamento / "CLAUDE.md").write_text("Regras do Claude daqui.\n", encoding="utf-8")
    (andamento / "GEMINI.md").write_text("# Gemini\n", encoding="utf-8")
    (andamento / ".github/copilot-instructions.md").write_text("Instruções do Copilot.\n", encoding="utf-8")
    (andamento / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
    (andamento / ".claude/skills/humanizar-texto/SKILL.md").write_text("minha skill\n", encoding="utf-8")
    (andamento / "entregaveis/final/deck.pptx").write_text("x", encoding="utf-8")
    (andamento / ".claude/settings.json").write_text(json.dumps({
        "permissions": {"allow": ["Bash(npm test)"], "deny": ["Read(.env)"]},
        "hooks": {"PostToolUse": [{"matcher": "Write", "hooks": [{"type": "command", "command": "npm run lint"}]}]},
        "model": "opus",
    }), encoding="utf-8")
    saida = instalar(andamento)
    confere("instala em projeto em andamento", saida.returncode == 0, saida.stdout + saida.stderr)
    confere("mantém o texto do AGENTS.md do projeto", (andamento / "AGENTS.md").read_text(encoding="utf-8").startswith("# Meu projeto\n\nRegras minhas.\n"))
    confere("mantém o texto do CLAUDE.md do projeto", (andamento / "CLAUDE.md").read_text(encoding="utf-8").startswith("Regras do Claude daqui.\n"))
    for nome in ("AGENTS.md", "CLAUDE.md", "GEMINI.md", ".github/copilot-instructions.md", ".gitignore"):
        confere(f"{nome} recebe um bloco só", (andamento / nome).read_text(encoding="utf-8").count("harness-de-entregaveis: inicio") == 1)
    confere("não cria arquivo de agente que o projeto não usa", not (andamento / ".cursorrules").exists())
    ajustes = json.loads((andamento / ".claude/settings.json").read_text(encoding="utf-8"))
    comandos = [h["command"] for g in ajustes["hooks"]["PostToolUse"] for h in g["hooks"]]
    confere("mantém os hooks e os ajustes do projeto", "npm run lint" in comandos and ajustes["model"] == "opus" and ajustes["permissions"]["deny"] == ["Read(.env)"] and "Bash(npm test)" in ajustes["permissions"]["allow"])
    confere("acrescenta os seis hooks", all(e in ajustes["hooks"] for e in ("SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse", "Stop")) and sum(len(g["hooks"]) for grupos in ajustes["hooks"].values() for g in grupos if "_harness/hooks/" in g["hooks"][0]["command"]) == 6)
    confere("mantém a skill do projeto que tem o mesmo nome", (andamento / ".claude/skills/humanizar-texto/SKILL.md").read_text(encoding="utf-8") == "minha skill\n" and "não veio do kit" in saida.stdout, saida.stdout)
    confere("não toca na pasta de entregáveis que já existia", (andamento / "entregaveis/final/deck.pptx").read_text(encoding="utf-8") == "x" and "já existia" in saida.stdout)
    de_novo = instalar(andamento)
    confere("segunda instalação em projeto em andamento não muda nada", "Nada a fazer" in de_novo.stdout and (andamento / "AGENTS.md").read_text(encoding="utf-8").count("harness-de-entregaveis: inicio") == 1, de_novo.stdout)
    (andamento / ".claude/skills/relatar-ao-dono").mkdir()
    (andamento / ".claude/skills/relatar-ao-dono/SKILL.md").write_text("skill do projeto\n", encoding="utf-8")
    forcada = instalar(andamento, "--atualizar")
    confere("--atualizar não retira a skill do projeto que tem o nome antigo de uma do kit", (andamento / ".claude/skills/relatar-ao-dono/SKILL.md").is_file(), forcada.stdout)
    confere("--atualizar não troca a skill do projeto", (andamento / ".claude/skills/humanizar-texto/SKILL.md").read_text(encoding="utf-8") == "minha skill\n", forcada.stdout)

    # Atualização: troca o que é do kit e preserva o que é do projeto.
    (vazio / "entregaveis/_harness/VERSAO").write_text("0.0.1\n", encoding="utf-8")
    (vazio / "entregaveis/_harness/REGRAS.md").write_text("regra velha\n", encoding="utf-8")
    skill = vazio / ".claude/skills/adiar-trabalho/SKILL.md"
    skill.write_text(skill.read_text(encoding="utf-8") + "\nlinha de versão antiga\n", encoding="utf-8")
    brief = vazio / "entregaveis/_projeto/brief.md"
    brief.write_text(brief.read_text(encoding="utf-8").replace("projeto: PREENCHER", "projeto: Meu projeto"), encoding="utf-8")
    antiga = vazio / ".claude/skills/relatar-ao-dono"
    antiga.mkdir()
    (antiga / "SKILL.md").write_text("---\nname: relatar-ao-dono\nmetadata:\n  origem: harness-de-entregaveis\n---\n", encoding="utf-8")
    sem_opcao = instalar(vazio)
    confere("sem --atualizar, avisa da versão diferente e não troca", "Use --atualizar" in sem_opcao.stdout and (vazio / "entregaveis/_harness/REGRAS.md").read_text(encoding="utf-8") == "regra velha\n", sem_opcao.stdout)
    atualizada = instalar(vazio, "--atualizar")
    confere("--atualizar troca o que é do kit", (vazio / "entregaveis/_harness/REGRAS.md").read_text(encoding="utf-8") == (HARNESS / "REGRAS.md").read_text(encoding="utf-8") and "linha de versão antiga" not in skill.read_text(encoding="utf-8"), atualizada.stdout + atualizada.stderr)
    confere("--atualizar retira a skill do kit que mudou de nome", not antiga.exists() and (vazio / ".claude/skills/relatar-ao-consultor/SKILL.md").is_file() and "relatar-ao-consultor" in atualizada.stdout, atualizada.stdout)
    confere("--atualizar preserva os registros do projeto", "projeto: Meu projeto" in brief.read_text(encoding="utf-8"))

    # Outro nome de pasta.
    outra = tmp / "outra"
    outra.mkdir()
    (outra / ".git").mkdir()
    saida = instalar(outra, "--pasta", "consultoria", "--ci")
    confere("instala com outro nome de pasta", saida.returncode == 0 and (outra / "consultoria/_harness/REGRAS.md").is_file() and not (outra / "entregaveis").exists(), saida.stdout + saida.stderr)
    sobras = []
    for arquivo in outra.rglob("*"):
        if arquivo.is_file() and arquivo.suffix in {".md", ".json", ".yml"} or arquivo.name == ".gitignore":
            if "entregaveis/" in arquivo.read_text(encoding="utf-8"):
                sobras.append(str(arquivo.relative_to(outra)))
    confere("nenhuma instrução aponta para o nome antigo da pasta", not sobras, ", ".join(sobras[:8]))
    estado = rodar([PY, "consultoria/_harness/scripts/estado.py"], outra)
    confere("o estado roda com outro nome de pasta", estado.returncode == 0 and "não foi iniciado" in estado.stdout, estado.stdout + estado.stderr)


# --- Checagens ------------------------------------------------------------

BRIEF = """---
projeto: Diagnóstico de martech
cliente: Varejista Exemplo
tipo: assessment de martech e adtech
pacotes:
consultor: Consultora responsável
idioma_dos_relatorios: pt-BR
idiomas_dos_entregaveis: pt-BR, es, en
classificacao: restrito
marcacao_obrigatoria:
iniciado: sim
---
# Brief do projeto

## O que é o projeto

Um diagnóstico das plataformas de marketing de um varejista.

## A decisão que o projeto precisa provocar

A diretoria escolhe quais plataformas ficam.
"""

BRIEFING = """---
id: diag
titulo: Diagnóstico de martech
tipo: apresentacao
veiculo: projetado
formato: pptx
idiomas: pt-BR
duracao_min: 30
prazo:
origem:
estado: redacao
---
# Briefing do entregável

## Audiência

A diretora de marketing decide. Ela conhece as plataformas pelo nome e teme parar campanhas.

## De e para

| De | Para |
| --- | --- |
| Cada área compra a sua ferramenta | Um conjunto único, com dono |

## Grande ideia

A empresa paga por plataformas que se repetem e perde lançamentos por causa disso.

## Chamada para ação

| Ação | Dono | Prazo | Papel |
| --- | --- | --- | --- |
| Aprovar o desligamento de duas plataformas | Diretora de marketing | 2026-12-15 | libera recursos |

## Resistências

| Tipo | Resistência esperada | Como o material responde |
| --- | --- | --- |
| prática | Medo de parar campanhas | Plano de migração por ondas |
"""

STORYLINE = """---
aprovada: sim
aprovada_por: Consultora responsável
aprovada_em: 2026-11-20
---
# Storyline

## Abertura

| Elemento | Texto |
| --- | --- |
| Situação | A empresa cresceu comprando ferramentas por área |
| Complicação | As ferramentas se repetem |
| Pergunta | Quais ficam |
| Resposta | Ficam as que têm dono e uso |

## Resumo executivo

Duas plataformas fazem o mesmo trabalho. Desligar uma libera verba para o que falta.

## Sequência

| N | Seção | Título de ação | Tipo | Evidência |
| --- | --- | --- | --- | --- |
| 1 | | Diagnóstico de martech | capa | |
| 2 | Achados | Duas plataformas de e-mail fazem o mesmo trabalho | dados | E-001 |
| 3 | Pedido | A diretoria aprova o desligamento até dezembro | pedido | |

## Recursos planejados

Nenhum.
"""

CONTEUDO = """# Conteúdo

## 1. Diagnóstico de martech
<!-- tipo: capa; secao: ; fonte: ; recurso: -->

Para a diretoria de marketing.

## 2. Duas plataformas de e-mail fazem o mesmo trabalho
<!-- tipo: dados; secao: Achados; fonte: E-001; recurso: -->

Das 14 plataformas contratadas, duas enviam e-mail para a mesma base.

Notas: conte o caso da campanha de aniversário.

## 3. A diretoria aprova o desligamento até dezembro
<!-- tipo: pedido; secao: Pedido; fonte: nao-se-aplica; recurso: -->

A diretora de marketing aprova o plano de migração.
"""

REVISAO = """---
conteudo_revisado:
revisado_em:
---
# Revisão

| Critério | Veredito | Onde | Correção feita |
| --- | --- | --- | --- |
| A grande ideia aparece no resumo | passa | | |

## O que ficou pendente

Nada ficou pendente.
"""


def montar_exemplo(projeto: Path) -> Path:
    """Um projeto pequeno e correto, sobre o qual cada erro é plantado."""
    base = projeto / "entregaveis"
    (base / "_projeto/brief.md").write_text(BRIEF, encoding="utf-8")
    with (base / "_projeto/evidencias.tsv").open("a", encoding="utf-8") as f:
        f.write("E-001\tPlataformas contratadas\t14\tInventário de contratos\t2026-10-01\tfato\talta\tdiag\n")
    with (base / "_projeto/glossario.tsv").open("a", encoding="utf-8") as f:
        f.write("plataforma de dados de clientes\tBase única de clientes\tcustomer data platform\tpt\n")
    with (base / "_projeto/confidencial.tsv").open("a", encoding="utf-8") as f:
        f.write("Projeto Girassol\tcodinome de outro cliente\n")
    criado = rodar([PY, "entregaveis/_harness/scripts/preparar.py", "--entregavel", "diag", "--tipo", "apresentacao", "--veiculo", "projetado", "--formato", "pptx", "--idiomas", "pt-BR"], projeto)
    confere("preparar.py cria o entregável", criado.returncode == 0 and (base / "diag/conteudo.md").is_file() and not (base / "diag/documento.md").exists(), criado.stdout + criado.stderr)
    pasta = base / "diag"
    (pasta / "briefing.md").write_text(BRIEFING, encoding="utf-8")
    (pasta / "storyline.md").write_text(STORYLINE, encoding="utf-8")
    (pasta / "conteudo.md").write_text(CONTEUDO, encoding="utf-8")
    return pasta


def validar(projeto: Path, *opcoes: str) -> subprocess.CompletedProcess:
    return rodar([PY, "entregaveis/_harness/scripts/validar.py", *opcoes], projeto)


def testar_checagens(tmp: Path) -> None:
    print("Checagens")
    projeto = tmp / "checagens"
    projeto.mkdir()
    instalar(projeto)
    pasta = montar_exemplo(projeto)
    bom = validar(projeto)
    confere("o exemplo bom passa sem erro", bom.returncode == 0 and "ERRO" not in bom.stdout, bom.stdout + bom.stderr)

    def com(arquivo: str, trocar: tuple[str, str] | None, espera: str, nome: str, acrescentar: str = "", opcoes: tuple = (), deve_reprovar: bool = True) -> None:
        """Planta um erro, roda as checagens, confere o achado e desfaz."""
        alvo = pasta / arquivo
        existia = alvo.is_file()
        original = alvo.read_text(encoding="utf-8") if existia else ""
        texto = original
        if trocar:
            assert trocar[0] in texto, f"trecho não encontrado em {arquivo}: {trocar[0]}"
            texto = texto.replace(trocar[0], trocar[1])
        alvo.write_text(texto + acrescentar, encoding="utf-8")
        try:
            saida = validar(projeto, *opcoes)
            if deve_reprovar:
                confere(nome, saida.returncode == 1 and espera in saida.stdout, saida.stdout + saida.stderr)
            else:
                confere(nome, espera not in saida.stdout, saida.stdout + saida.stderr)
        finally:
            if existia:
                alvo.write_text(original, encoding="utf-8")
            else:
                alvo.unlink()

    pagina = lambda n, corpo, campos="tipo: texto; secao: Achados; fonte: nao-se-aplica; recurso: ": f"\n## {n}. A equipe de mídia aprova o plano em uma tela\n<!-- {campos} -->\n\n{corpo}\n"  # noqa: E731

    # Briefing
    com("briefing.md", ("A empresa paga por plataformas que se repetem e perde lançamentos por causa disso.", "PREENCHER"), "ERRO  [briefing]", "briefing: reprova grande ideia sem preencher")
    com("briefing.md", ("A empresa paga por plataformas que se repetem e perde lançamentos por causa disso.", "Arquitetura de martech"), "ERRO  [briefing]", "briefing: reprova grande ideia que é só um assunto")
    com("briefing.md", ("| Diretora de marketing | 2026-12-15 |", "| | |"), "ERRO  [briefing]", "briefing: reprova pedido sem dono e sem prazo")
    # Storyline
    com("conteudo.md", ("## 2. Duas plataformas de e-mail fazem o mesmo trabalho", "## 2. Contexto"), "ERRO  [storyline]", "storyline: reprova título que é rótulo")
    com("conteudo.md", ("## 2. Duas plataformas de e-mail fazem o mesmo trabalho", "## 2. O que encontramos nas plataformas de e-mail:"), "ERRO  [storyline]", "storyline: reprova título que termina em dois-pontos")
    com("conteudo.md", ("## 2. Duas plataformas de e-mail fazem o mesmo trabalho", "## 2. " + "As duas plataformas de e-mail fazem o mesmo trabalho para a mesma base de clientes e de leads todos os meses"), "ERRO  [storyline]", "storyline: reprova título acima do limite do veículo")
    com("storyline.md", ("aprovada: sim", "aprovada: nao"), "ERRO  [storyline]", "storyline: reprova conteúdo escrito sem aprovação do consultor")
    com("conteudo.md", ("tipo: pedido", "tipo: texto"), "ERRO  [storyline]", "storyline: reprova material sem página de pedido", opcoes=("--rigoroso",))
    # Densidade
    com("conteudo.md", None, "ERRO  [densidade]", "densidade: reprova página projetada com texto demais", acrescentar=pagina(4, " ".join(["A equipe revisa o plano."] * 30)))
    # Evidência
    com("conteudo.md", ("fonte: E-001", "fonte: "), "ERRO  [evidencia]", "evidência: reprova página de dados sem fonte")
    com("conteudo.md", ("fonte: E-001", "fonte: E-999"), "ERRO  [evidencia]", "evidência: reprova fonte que não está no registro")
    com("conteudo.md", None, "ERRO  [evidencia]", "evidência: reprova número sem fonte", acrescentar=pagina(4, "O custo subiu 18% no período.", "tipo: texto; secao: Achados; fonte: ; recurso: "))
    com("conteudo.md", None, "ERRO  [evidencia]", "evidência: reprova marca de rascunho na revisão", acrescentar=pagina(4, "Valor TBD pela equipe."), opcoes=("--rigoroso",))
    # Texto
    com("conteudo.md", None, "ERRO  [texto]", "texto: reprova travessão", acrescentar=pagina(4, "A equipe aprova — e segue."))
    com("conteudo.md", None, "ERRO  [texto]", "texto: reprova contraste vazio", acrescentar=pagina(4, "Não é apenas uma plataforma, é uma nova forma de trabalhar."))
    com("conteudo.md", None, "ERRO  [texto]", "texto: aceita contraste planejado e declarado", acrescentar=pagina(4, "Não é apenas uma plataforma, é uma nova forma de trabalhar.", "tipo: texto; secao: Achados; fonte: nao-se-aplica; recurso: contraste"), deve_reprovar=False)
    com("conteudo.md", None, "ERRO  [texto]", "texto: reprova aviso de importância", acrescentar=pagina(4, "Vale ressaltar que a equipe aprova o plano."))
    com("conteudo.md", None, "ERRO  [texto]", "texto: reprova autoridade sem nome", acrescentar=pagina(4, "Especialistas apontam que a equipe aprova o plano."))
    com("conteudo.md", None, "ERRO  [texto]", "texto: não examina expressão citada entre aspas", acrescentar=pagina(4, 'A equipe cortou a frase "vale ressaltar" do material.'), deve_reprovar=False)
    com("conteudo.es.md", None, "ERRO  [texto]", "texto: reprova vício em espanhol", acrescentar=CONTEUDO + pagina(4, "Cabe destacar que el equipo aprueba el plan."))
    com("conteudo.en.md", None, "ERRO  [texto]", "texto: reprova vício em inglês", acrescentar=CONTEUDO + pagina(4, "It is worth noting that the team approves the plan."))
    com("conteudo.es.md", None, "ERRO  [texto]", "texto: não aplica a lista de um idioma a outro", acrescentar=CONTEUDO + pagina(4, "It is worth noting that the team approves the plan."), deve_reprovar=False)
    # Termos
    com("conteudo.md", None, "ERRO  [termos]", "termos: reprova variante que o glossário manda evitar", acrescentar=pagina(4, "A customer data platform junta as bases."))
    # Estrutura
    com("conteudo.md", ("## 3. A diretoria", "## 5. A diretoria"), "ERRO  [estrutura]", "estrutura: reprova numeração quebrada")
    com("conteudo.md", ("tipo: dados; ", ""), "ERRO  [estrutura]", "estrutura: reprova página sem tipo")
    com("conteudo.md", None, "ERRO  [estrutura]", "estrutura: reprova referência a página que não existe", acrescentar=pagina(4, "O detalhe está na página 40."))
    # Confidencialidade
    com("conteudo.md", None, "ERRO  [confidencialidade]", "confidencialidade: reprova termo proibido", acrescentar=pagina(4, "O mesmo foi feito no Projeto Girassol."))
    com("conteudo.md", None, "ERRO  [confidencialidade]", "confidencialidade: reprova credencial", acrescentar=pagina(4, "A senha: abc12345xyz fica com a equipe."))

    # Marcação obrigatória
    brief = projeto / "entregaveis/_projeto/brief.md"
    brief.write_text(BRIEF.replace("marcacao_obrigatoria:", "marcacao_obrigatoria: Uso restrito"), encoding="utf-8")
    saida = validar(projeto, "--rigoroso")
    confere("confidencialidade: reprova falta da marcação obrigatória", saida.returncode == 1 and "ERRO  [confidencialidade]" in saida.stdout, saida.stdout)
    brief.write_text(BRIEF, encoding="utf-8")

    # Intake e projeto
    with (projeto / "entregaveis/_intake/registro.tsv").open("a", encoding="utf-8") as f:
        f.write("M-001\tModelo de apresentação\tmodelo\tcliente\t2026-11-01\t2026-11-05\tpedido\t\t\n")
    saida = validar(projeto)
    confere("intake: avisa de material pedido e não recebido", "AVISO [intake]" in saida.stdout and "M-001" in saida.stdout, saida.stdout)
    estado = rodar([PY, "entregaveis/_harness/scripts/estado.py"], projeto)
    confere("estado: mostra o projeto, o entregável e o material pendente", estado.returncode == 0 and "diag" in estado.stdout and "Modelo de apresentação" in estado.stdout and "Decisões assumidas" not in estado.stdout, estado.stdout + estado.stderr)
    with (projeto / "entregaveis/_projeto/decisoes.md").open("a", encoding="utf-8") as f:
        f.write("| D-001 | 2026-11-20 | Deck de leitura em vez de projetado | O consultor não disse | Vigente (assumida) |\n")
    estado = rodar([PY, "entregaveis/_harness/scripts/estado.py"], projeto)
    confere("estado: conta as decisões assumidas à espera do consultor", "Decisões assumidas à espera do consultor: 1" in estado.stdout, estado.stdout)

    # Revisão
    sem_rubrica = validar(projeto, "--carimbar", "diag")
    confere("revisão: não registra sem a rubrica preenchida", sem_rubrica.returncode == 1, sem_rubrica.stdout)
    (pasta / "revisao.md").write_text(REVISAO, encoding="utf-8")
    com_rubrica = validar(projeto, "--carimbar", "diag")
    confere("revisão: registra a versão revisada", com_rubrica.returncode == 0 and re.search(r"conteudo_revisado: \w{16}", (pasta / "revisao.md").read_text(encoding="utf-8")) is not None, com_rubrica.stdout + com_rubrica.stderr)


# --- Hooks ----------------------------------------------------------------


def testar_hooks(tmp: Path) -> None:
    print("Hooks")
    projeto = tmp / "hooks"
    projeto.mkdir()
    instalar(projeto)
    hooks = projeto / "entregaveis/_harness/hooks"

    def hook(nome: str, dados: dict) -> subprocess.CompletedProcess:
        return rodar([PY, hooks / nome], projeto, json.dumps({"cwd": str(projeto), **dados}))

    def gravacao(caminho: str, sessao: str = "s1") -> dict:
        return {"session_id": sessao, "tool_name": "Write", "tool_input": {"file_path": caminho}}

    inicio = hook("sessao.py", {"hook_event_name": "SessionStart"})
    confere("sessão: diz que o projeto não foi iniciado", inicio.returncode == 0 and "iniciar-projeto" in inicio.stdout, inicio.stdout + inicio.stderr)
    lembrete = hook("mensagem.py", {"prompt": "monte a apresentação da diretoria"})
    confere("mensagem: lembra de iniciar o projeto quando o pedido é de material", lembrete.returncode == 0 and "iniciar-projeto" in lembrete.stdout, lembrete.stdout)
    calado = hook("mensagem.py", {"prompt": "corrija o teste da API"})
    confere("mensagem: fica calada em pedido de outro assunto", calado.returncode == 0 and not calado.stdout.strip(), calado.stdout)

    pasta = montar_exemplo(projeto)
    ponto = hook("mensagem.py", {"prompt": "siga"})
    confere("mensagem: mostra o ponto atual em até três linhas", "diag" in ponto.stdout and len(ponto.stdout.strip().splitlines()) <= 4, ponto.stdout)

    # Antes de gravar
    confere("antes de gravar: deixa gravar página com briefing e storyline prontos", hook("antes_de_gravar.py", gravacao("entregaveis/diag/conteudo.md")).returncode == 0)
    (pasta / "storyline.md").write_text(STORYLINE.replace("aprovada: sim", "aprovada: nao"), encoding="utf-8")
    barrado = hook("antes_de_gravar.py", gravacao("entregaveis/diag/conteudo.md"))
    confere("antes de gravar: bloqueia página sem storyline aprovada", barrado.returncode == 2 and "storyline" in barrado.stderr, barrado.stderr)
    confere("antes de gravar: bloqueia arquivo de saída sem storyline aprovada", hook("antes_de_gravar.py", gravacao(str(pasta / "saida/deck.pptx"))).returncode == 2)
    confere("antes de gravar: deixa gravar a storyline", hook("antes_de_gravar.py", gravacao("entregaveis/diag/storyline.md")).returncode == 0)
    (pasta / "storyline.md").write_text(STORYLINE, encoding="utf-8")
    (pasta / "briefing.md").write_text(BRIEFING.replace("A empresa paga por plataformas que se repetem e perde lançamentos por causa disso.", "PREENCHER"), encoding="utf-8")
    barrado = hook("antes_de_gravar.py", gravacao("entregaveis/diag/conteudo.md"))
    confere("antes de gravar: bloqueia página com briefing incompleto", barrado.returncode == 2 and "briefing" in barrado.stderr, barrado.stderr)
    (pasta / "briefing.md").write_text(BRIEFING, encoding="utf-8")
    confere("antes de gravar: ignora arquivo fora da pasta de entregáveis", hook("antes_de_gravar.py", gravacao("src/app.py")).returncode == 0)
    confere("antes de gravar: bloqueia página em pasta sem briefing", hook("antes_de_gravar.py", gravacao("entregaveis/novo/conteudo.md")).returncode == 2)
    confere("antes de gravar: não barra pasta antiga do projeto", hook("antes_de_gravar.py", gravacao("entregaveis/final/saida/deck.pptx")).returncode == 0)
    confere("antes de gravar: entrada inválida não trava o trabalho", rodar([PY, hooks / "antes_de_gravar.py"], projeto, "isto não é json").returncode == 0)

    # Depois de gravar
    limpo = hook("depois_de_gravar.py", gravacao("entregaveis/diag/conteudo.md"))
    confere("depois de gravar: arquivo limpo passa", limpo.returncode == 0, limpo.stdout + limpo.stderr)
    (pasta / "conteudo.md").write_text(CONTEUDO + "\nA equipe aprova — e segue.\n", encoding="utf-8")
    sujo = hook("depois_de_gravar.py", gravacao("entregaveis/diag/conteudo.md"))
    confere("depois de gravar: devolve o vício de texto ao agente", sujo.returncode == 2 and "[texto]" in sujo.stderr, sujo.stdout + sujo.stderr)
    (pasta / "conteudo.md").write_text(CONTEUDO + "\nVeja o fluxo -> aprovação.\n", encoding="utf-8")
    aviso = hook("depois_de_gravar.py", gravacao("entregaveis/diag/conteudo.md"))
    confere("depois de gravar: aviso volta como contexto e não barra", aviso.returncode == 0 and "additionalContext" in aviso.stdout, aviso.stdout + aviso.stderr)
    (pasta / "conteudo.md").write_text(CONTEUDO, encoding="utf-8")

    # Fim do turno
    outra_sessao = hook("fim_do_turno.py", {"session_id": "s2"})
    confere("fim do turno: não cobra sessão que não alterou conteúdo", outra_sessao.returncode == 0, outra_sessao.stderr)
    cobrado = hook("fim_do_turno.py", {"session_id": "s1"})
    confere("fim do turno: bloqueia conteúdo alterado e sem revisão", cobrado.returncode == 2 and "revisar-entregavel" in cobrado.stderr, cobrado.stdout + cobrado.stderr)
    confere("fim do turno: cobra uma vez por versão", hook("fim_do_turno.py", {"session_id": "s1"}).returncode == 0)
    (pasta / "revisao.md").write_text(REVISAO, encoding="utf-8")
    carimbo = validar(projeto, "--carimbar", "diag")
    hook("depois_de_gravar.py", gravacao("entregaveis/diag/conteudo.md", "s3"))
    confere("fim do turno: libera depois da revisão registrada", carimbo.returncode == 0 and hook("fim_do_turno.py", {"session_id": "s3"}).returncode == 0, carimbo.stdout)
    (pasta / "conteudo.md").write_text(CONTEUDO.replace("aprova o plano de migração", "aprova o plano de migração por ondas"), encoding="utf-8")
    confere("fim do turno: volta a cobrar quando o conteúdo muda depois da revisão", hook("fim_do_turno.py", {"session_id": "s3"}).returncode == 2)


def preencher_interativo(html: str) -> str:
    """Troca as marcas e os exemplos de um modelo de HTML interativo por conteúdo de projeto."""
    html = re.sub(
        r"<!-- interativo.*?-->",
        "<!-- interativo\ntitulo: Caminho de uma campanha\nmensagem: A aprovação consome metade do prazo de uma campanha.\n"
        "apoia: página 2\nfontes: E-001\nidioma: pt-BR\n-->",
        html, count=1, flags=re.S,
    )
    html = html.replace("<title>PREENCHER</title>", "<title>Caminho de uma campanha</title>")
    html = html.replace("Fonte: PREENCHER, com a data do dado.", "Fonte: inventário de plataformas, março de 2026.")
    html = re.sub(r"PREENCHER[^<\n]*", "A aprovação consome metade do prazo de uma campanha.", html)
    return html.replace('"Exemplo: ', '"').replace('"Exemplo. ', '"').replace("Exemplo: ", "")


def testar_interativos(tmp: Path) -> None:
    print("HTML interativo")
    projeto = tmp / "interativos"
    projeto.mkdir()
    instalar(projeto)
    pasta = montar_exemplo(projeto)
    preparar = projeto / "entregaveis/_harness/scripts/preparar.py"
    modelos = sorted((HARNESS / "modelos/interativos").glob("*.html"))
    confere("há três modelos de HTML interativo", [m.stem for m in modelos] == ["camadas-3d", "fluxo", "simulador"], str(modelos))

    # Criação pelo preparar.py
    (pasta / "storyline.md").write_text(STORYLINE.replace("aprovada: sim", "aprovada: nao"), encoding="utf-8")
    recusa = rodar([PY, preparar, "--entregavel", "diag", "--interativo", "caminho", "--base", "fluxo"], projeto)
    confere("preparar: recusa a peça sem storyline aprovada", recusa.returncode != 0 and not (pasta / "interativos/caminho.html").exists(), recusa.stdout + recusa.stderr)
    (pasta / "storyline.md").write_text(STORYLINE, encoding="utf-8")
    for modelo in modelos:
        feito = rodar([PY, preparar, "--entregavel", "diag", "--interativo", f"peca-{modelo.stem}", "--base", modelo.stem], projeto)
        confere(f"preparar: cria a peça a partir de '{modelo.stem}'", feito.returncode == 0 and (pasta / f"interativos/peca-{modelo.stem}.html").is_file(), feito.stdout + feito.stderr)
    confere("preparar: recusa modelo que não existe", rodar([PY, preparar, "--entregavel", "diag", "--interativo", "x1", "--base", "nada"], projeto).returncode != 0)
    confere("preparar: não mexe no briefing ao criar a peça", (pasta / "briefing.md").read_text(encoding="utf-8") == BRIEFING)
    cru = validar(projeto, "--so", "interativo")
    confere("modelo recém-criado: só avisos enquanto está em redação", cru.returncode == 0 and "PREENCHER" in cru.stdout, cru.stdout[-600:])
    rigor = validar(projeto, "--so", "interativo", "--rigoroso")
    confere("modelo recém-criado: reprova na revisão por marca e dado de exemplo", rigor.returncode != 0 and "dado(s) de exemplo" in rigor.stdout, rigor.stdout[-600:])

    # Modelos preenchidos passam, inclusive na revisão
    for modelo in modelos:
        (pasta / f"interativos/peca-{modelo.stem}.html").write_text(preencher_interativo(modelo.read_text(encoding="utf-8")), encoding="utf-8")
    limpo = validar(projeto, "--so", "interativo", "--rigoroso")
    confere("modelos preenchidos passam na checagem rigorosa", limpo.returncode == 0 and "Nenhum erro e nenhum aviso" in limpo.stdout, limpo.stdout[-900:])
    for modelo in modelos:
        html = modelo.read_text(encoding="utf-8")
        confere(f"modelo '{modelo.stem}': sem endereço de rede", not re.search(r"https?://|//cdn|@import", html))

    # Arquivo único: cada tipo de recurso de fora reprova
    alvo = pasta / "interativos/peca-fluxo.html"
    bom = alvo.read_text(encoding="utf-8")

    def com(trecho: str, nome: str, espera: str = "arquivo único", antes: str = "</body>", deve_reprovar: bool = True) -> None:
        alvo.write_text(bom.replace(antes, trecho + antes, 1), encoding="utf-8")
        saida = validar(projeto, "--so", "interativo")
        ok = (saida.returncode != 0 and espera in saida.stdout) if deve_reprovar else saida.returncode == 0
        confere(nome, ok, saida.stdout[-500:])
        alvo.write_text(bom, encoding="utf-8")

    com('<script src="https://cdn.exemplo.com/grafico.js"></script>', "reprova script de fora")
    com('<script src="lib/grafico.js"></script>', "reprova script em pasta ao lado")
    com('<link rel="stylesheet" href="estilo.css">', "reprova folha de estilo de fora", antes="</head>")
    com('<img src="imagens/mapa.png" alt="Mapa">', "reprova imagem em pasta ao lado")
    com('<iframe src="https://exemplo.com/painel"></iframe>', "reprova quadro embutido")
    com("<style>@font-face { font-family: Marca; src: url(fontes/marca.woff2); }</style>", "reprova fonte em arquivo ao lado", antes="</head>")
    com('<style>@import "tema.css";</style>', "reprova importação de estilo", antes="</head>")
    com('<script>fetch("https://api.exemplo.com/dados").then(function () {});</script>', "reprova chamada de rede")
    com('<img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=" alt="Ponto">', "aceita imagem embutida no arquivo", deve_reprovar=False)
    com('<svg viewBox="0 0 10 10" role="img" aria-label="Marca"><defs><linearGradient id="g"></linearGradient></defs><rect width="10" height="10" fill="url(#g)"></rect></svg>', "aceita SVG desenhado no arquivo", deve_reprovar=False)

    # Estrutura e movimento
    alvo.write_text(bom.replace("prefers-reduced-motion", "prefers-outra-coisa"), encoding="utf-8")
    parado = validar(projeto, "--so", "interativo")
    confere("reprova animação sem movimento reduzido", parado.returncode != 0 and "prefers-reduced-motion" in parado.stdout, parado.stdout[-400:])
    alvo.write_text(bom.replace('<meta name="viewport" content="width=device-width, initial-scale=1">', ""), encoding="utf-8")
    confere("reprova arquivo sem viewport", validar(projeto, "--so", "interativo").returncode != 0)
    alvo.write_text(bom.replace("fontes: E-001", "fontes: E-777"), encoding="utf-8")
    perdida = validar(projeto, "--so", "interativo")
    confere("reprova evidência que não está no registro", perdida.returncode != 0 and "E-777" in perdida.stdout, perdida.stdout[-400:])
    alvo.write_text(bom.replace("</main>", "<p>A equipe aprova — e segue.</p></main>"), encoding="utf-8")
    vicio = validar(projeto, "--so", "interativo")
    confere("o texto visível da peça passa pelas checagens de texto", vicio.returncode != 0 and "[interativo]" in vicio.stdout, vicio.stdout[-400:])
    alvo.write_text(bom, encoding="utf-8")

    # Hooks
    hooks = projeto / "entregaveis/_harness/hooks"

    def hook(nome: str, caminho: str) -> subprocess.CompletedProcess:
        dados = {"cwd": str(projeto), "session_id": "i1", "tool_name": "Write", "tool_input": {"file_path": caminho}}
        return rodar([PY, hooks / nome], projeto, json.dumps(dados))

    confere("antes de gravar: deixa gravar a peça com storyline aprovada", hook("antes_de_gravar.py", "entregaveis/diag/interativos/peca-fluxo.html").returncode == 0)
    (pasta / "storyline.md").write_text(STORYLINE.replace("aprovada: sim", "aprovada: nao"), encoding="utf-8")
    confere("antes de gravar: bloqueia a peça sem storyline aprovada", hook("antes_de_gravar.py", "entregaveis/diag/interativos/peca-fluxo.html").returncode == 2)
    (pasta / "storyline.md").write_text(STORYLINE, encoding="utf-8")
    confere("depois de gravar: peça limpa passa", hook("depois_de_gravar.py", "entregaveis/diag/interativos/peca-fluxo.html").returncode == 0)
    alvo.write_text(bom.replace("</body>", '<script src="https://cdn.exemplo.com/grafico.js"></script></body>'), encoding="utf-8")
    devolvido = hook("depois_de_gravar.py", "entregaveis/diag/interativos/peca-fluxo.html")
    confere("depois de gravar: devolve o recurso de fora ao agente", devolvido.returncode == 2 and "arquivo único" in devolvido.stderr, devolvido.stdout + devolvido.stderr)
    alvo.write_text(bom, encoding="utf-8")

    # A revisão registrada vale para a versão da peça que foi revisada
    (pasta / "revisao.md").write_text(REVISAO, encoding="utf-8")
    validar(projeto, "--carimbar", "diag")
    codigo = "import sys; sys.path.insert(0, 'entregaveis/_harness/scripts'); import comum; print(comum.carimbo(comum.BASE / 'diag'))"
    antes = rodar([PY, "-c", codigo], projeto).stdout.strip()
    alvo.write_text(bom.replace("Caminho de uma campanha", "Caminho de uma campanha de mídia"), encoding="utf-8")
    depois = rodar([PY, "-c", codigo], projeto).stdout.strip()
    confere("o carimbo da revisão muda quando a peça muda", bool(antes) and antes != depois, f"{antes} {depois}")


DOMINIO = """---
estado: rascunho
calibrado_em: 2026-11-23
materiais: M-001
---
# Domínio do projeto

## Contexto e objetivo

A diretoria decide que plataformas ficam. Origem: brief.

## Métodos e frameworks

Inventário por função e por dono. Origem: M-001.
"""

REGRAS_DO_DOMINIO = (
    "id\ttipo\taplica\tonde\tpadrao\tmensagem\tnivel\torigem\n"
    "D-001\tjunto\t*\tconteudo\tnota de maturidade => crit[ée]rio\tToda nota de maturidade vem com o critério que a justifica.\terro\tM-001\n"
    "D-002\tproibido\tapresentacao\ttitulos\t\\bferramentas?\\b\tO projeto chama de plataforma, não de ferramenta.\terro\tM-001\n"
    "D-003\tobrigatorio\t*\tconteudo\tplataformas contratadas\tO material diz quantas plataformas estão contratadas.\terro\tM-001\n"
    "D-004\tordem\t*\tconteudo\tDiagn[óo]stico => desligamento\tO pedido de desligamento só vem depois do diagnóstico.\taviso\tM-001\n"
)

CASOS_DO_DOMINIO = (
    "checagem\tespera\ttexto\n"
    "D-001\tacusa\tA nota de maturidade da frente de dados é 2.\n"
    "D-001\tpassa\tA nota de maturidade da frente de dados é 2. O critério: não há identificador único.\n"
    "D-001\tacusa\tA nota de maturidade é 2.\\n\\nO critério está em outra página.\n"
    "D-002\tacusa\tTrês ferramentas fazem o mesmo trabalho\n"
    "D-002\tpassa\tTrês plataformas fazem o mesmo trabalho\n"
    "D-003\tacusa\tDuas enviam e-mail para a mesma base.\n"
    "D-003\tpassa\tDas 14 plataformas contratadas, duas enviam e-mail.\n"
    "D-004\tacusa\tA diretoria aprova o desligamento.\\n\\nDiagnóstico de martech.\n"
    "D-004\tpassa\tDiagnóstico de martech.\\n\\nA diretoria aprova o desligamento.\n"
)


def testar_dominio(tmp: Path) -> None:
    print("Domínio do projeto")
    modelos = HARNESS / "modelos/dominio"
    regras_do_modelo = [l for l in (modelos / "checagens.tsv").read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    casos_do_modelo = [l for l in (modelos / "casos.tsv").read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    confere("o template traz só o esqueleto: nenhuma regra e nenhum caso de domínio", len(regras_do_modelo) == 1 and len(casos_do_modelo) == 1, str(regras_do_modelo + casos_do_modelo))
    confere("o método do template está em branco", "PREENCHER" in (modelos / "dominio.md").read_text(encoding="utf-8") and "REGRAS = {}" in (modelos / "checagens_extra.py").read_text(encoding="utf-8"))
    na_raiz = RAIZ / "entregaveis/_dominio"
    confere("a raiz do template não tem domínio, registros nem materiais de projeto", not any((RAIZ / "entregaveis" / n).exists() for n in ("_dominio", "_projeto", "_intake")), str(na_raiz))

    projeto = tmp / "dominio"
    projeto.mkdir()
    instalar(projeto)
    dominio = projeto / "entregaveis/_dominio"
    script = projeto / "entregaveis/_harness/scripts/dominio.py"
    confere("a instalação cria _dominio com os cinco arquivos do esqueleto", sorted(a.name for a in dominio.iterdir()) == ["LEIA-ME.md", "casos.tsv", "checagens.tsv", "checagens_extra.py", "dominio.md"], str(list(dominio.iterdir())))
    vazio = rodar([PY, script], projeto)
    confere("sem regras, o teste do domínio passa e diz que não há regra", vazio.returncode == 0 and "nenhuma regra" in vazio.stdout, vazio.stdout + vazio.stderr)

    pasta = montar_exemplo(projeto)
    estado = rodar([PY, "entregaveis/_harness/scripts/estado.py"], projeto)
    confere("o estado avisa que o domínio não foi calibrado", "calibrar-dominio" in estado.stdout, estado.stdout)
    aviso = validar(projeto, "--so", "dominio")
    confere("a validação avisa do domínio não calibrado, sem reprovar", aviso.returncode == 0 and "calibrar-dominio" in aviso.stdout, aviso.stdout)

    (dominio / "dominio.md").write_text(DOMINIO, encoding="utf-8")
    sem_regra = validar(projeto, "--so", "dominio")
    confere("domínio descrito e sem regra gera aviso", sem_regra.returncode == 0 and "nenhuma regra" in sem_regra.stdout, sem_regra.stdout)
    (dominio / "checagens.tsv").write_text(REGRAS_DO_DOMINIO, encoding="utf-8")
    sem_caso = rodar([PY, script], projeto)
    confere("regra sem caso de teste reprova", sem_caso.returncode == 1 and "falta caso de teste" in sem_caso.stdout and sem_caso.stdout.count("D-00") >= 4, sem_caso.stdout)
    confere("a validação do projeto reprova regra sem caso", validar(projeto, "--so", "dominio").returncode == 1)
    (dominio / "casos.tsv").write_text(CASOS_DO_DOMINIO, encoding="utf-8")
    provado = rodar([PY, script], projeto)
    confere("regras com os dois casos passam", provado.returncode == 0 and "4 regra(s) provada(s) em 9 caso(s)" in provado.stdout, provado.stdout + provado.stderr)
    lista = rodar([PY, script, "--listar"], projeto)
    confere("--listar mostra cada regra com os casos", lista.returncode == 0 and "D-001\tjunto" in lista.stdout and "3 caso(s)" in lista.stdout, lista.stdout)
    limpo = validar(projeto, "--so", "dominio")
    confere("o exemplo correto passa nas regras do domínio", limpo.returncode == 0 and "Nenhum erro e nenhum aviso" in limpo.stdout, limpo.stdout)
    confere("o estado para de avisar depois da calibração", "calibrar-dominio" not in rodar([PY, "entregaveis/_harness/scripts/estado.py"], projeto).stdout)

    def com(antes: str, depois: str, espera: str, nome: str, reprova: bool = True) -> None:
        (pasta / "conteudo.md").write_text(CONTEUDO.replace(antes, depois), encoding="utf-8")
        saida = validar(projeto, "--so", "dominio")
        confere(nome, (saida.returncode != 0) == reprova and espera in saida.stdout, saida.stdout[-500:])
        (pasta / "conteudo.md").write_text(CONTEUDO, encoding="utf-8")

    com("Para a diretoria de marketing.", "A nota de maturidade de dados é 2.", "D-001", "junto: acusa a nota sem o critério na mesma página")
    com("Para a diretoria de marketing.", "A nota de maturidade de dados é 2. O critério é a base única.", "Nenhum erro", "junto: aceita a nota com o critério", reprova=False)
    com("## 2. Duas plataformas de e-mail", "## 2. Duas ferramentas de e-mail", "D-002", "proibido: acusa o termo no título")
    com("Das 14 plataformas contratadas, duas", "Das 14 ferramentas contratadas, duas", "D-003", "proibido em títulos não olha o corpo, e obrigatório acusa a falta")
    com("## 1. Diagnóstico de martech", "## 1. Visão geral de martech", "D-004", "ordem: avisa do pedido antes do diagnóstico", reprova=False)
    (pasta / "briefing.md").write_text(BRIEFING.replace("tipo: apresentacao", "tipo: documento"), encoding="utf-8")
    com("## 2. Duas plataformas de e-mail", "## 2. Duas ferramentas de e-mail", "Nenhum erro", "aplica: a regra de apresentação não vale para outro tipo", reprova=False)
    (pasta / "briefing.md").write_text(BRIEFING, encoding="utf-8")

    # Regra com defeito e caso que contradiz a regra
    (dominio / "checagens.tsv").write_text(REGRAS_DO_DOMINIO + "D-005\tproibido\t*\ttudo\t(aberto\tNão feche.\terro\tM-001\nD-006\tsempre\t*\ttudo\tx\tTipo que não existe.\terro\tM-001\n", encoding="utf-8")
    defeito = rodar([PY, script], projeto)
    confere("expressão inválida e tipo desconhecido são apontados", defeito.returncode == 1 and "D-005: expressão inválida" in defeito.stdout and "D-006: tipo" in defeito.stdout, defeito.stdout)
    confere("regra com defeito não derruba a validação do entregável", validar(projeto, "diag", "--so", "dominio").returncode == 0)
    (dominio / "checagens.tsv").write_text(REGRAS_DO_DOMINIO, encoding="utf-8")
    (dominio / "casos.tsv").write_text(CASOS_DO_DOMINIO + "D-002\tpassa\tTrês ferramentas repetidas\nD-009\tacusa\tx\n", encoding="utf-8")
    contradiz = rodar([PY, script], projeto)
    confere("caso que contradiz a regra e caso de regra inexistente reprovam", contradiz.returncode == 1 and "esperava 'passa'" in contradiz.stdout and "'D-009' não existe" in contradiz.stdout, contradiz.stdout)
    (dominio / "casos.tsv").write_text(CASOS_DO_DOMINIO, encoding="utf-8")

    # Regra em Python
    (dominio / "checagens_extra.py").write_text(
        "import re\n\n\ndef parcelas(texto):\n    partes = [int(n) for n in re.findall(r'(\\d+)%', texto)]\n"
        "    if len(partes) > 1 and sum(partes) != 100:\n        return 'As parcelas não somam 100%.'\n    return None\n\n\nREGRAS = {'D-900': parcelas}\n",
        encoding="utf-8",
    )
    confere("regra em Python também exige os dois casos", rodar([PY, script], projeto).returncode == 1)
    (dominio / "casos.tsv").write_text(CASOS_DO_DOMINIO + "D-900\tacusa\tMídia paga 60% e mídia própria 30%.\nD-900\tpassa\tMídia paga 60% e mídia própria 40%.\n", encoding="utf-8")
    python_ok = rodar([PY, script], projeto)
    confere("regra em Python é provada pelos casos", python_ok.returncode == 0 and "5 regra(s)" in python_ok.stdout, python_ok.stdout + python_ok.stderr)
    com("Para a diretoria de marketing.", "Mídia paga leva 60% e mídia própria 30%.", "D-900", "regra em Python acusa no entregável")
    (dominio / "checagens_extra.py").write_text("REGRAS = {'D-900': lambda texto: 1 / 0}\nisto não é python\n", encoding="utf-8")
    quebrado = rodar([PY, script], projeto)
    confere("arquivo Python com defeito vira achado, sem derrubar o validador", quebrado.returncode == 1 and "não carrega" in quebrado.stdout and validar(projeto, "diag", "--so", "texto").returncode == 0, quebrado.stdout + quebrado.stderr)
    (dominio / "checagens_extra.py").write_text((modelos / "checagens_extra.py").read_text(encoding="utf-8"), encoding="utf-8")
    (dominio / "casos.tsv").write_text(CASOS_DO_DOMINIO, encoding="utf-8")

    # Hooks: o achado do domínio volta na gravação, e gravar uma regra roda os casos
    hooks = projeto / "entregaveis/_harness/hooks"

    def hook(nome: str, caminho: str) -> subprocess.CompletedProcess:
        dados = {"cwd": str(projeto), "session_id": "d1", "tool_name": "Write", "tool_input": {"file_path": caminho}}
        return rodar([PY, hooks / nome], projeto, json.dumps(dados))

    (pasta / "conteudo.md").write_text(CONTEUDO.replace("## 2. Duas plataformas de e-mail", "## 2. Duas ferramentas de e-mail"), encoding="utf-8")
    devolvido = hook("depois_de_gravar.py", "entregaveis/diag/conteudo.md")
    confere("depois de gravar: devolve o achado do domínio ao agente", devolvido.returncode == 2 and "[dominio]" in devolvido.stderr and "D-002" in devolvido.stderr, devolvido.stdout + devolvido.stderr)
    (pasta / "conteudo.md").write_text(CONTEUDO, encoding="utf-8")
    confere("depois de gravar: regras provadas passam", hook("depois_de_gravar.py", "entregaveis/_dominio/checagens.tsv").returncode == 0)
    (dominio / "casos.tsv").write_text("checagem\tespera\ttexto\n", encoding="utf-8")
    cobrado = hook("depois_de_gravar.py", "entregaveis/_dominio/checagens.tsv")
    confere("depois de gravar: regra sem caso volta ao agente", cobrado.returncode == 2 and "falta caso de teste" in cobrado.stderr, cobrado.stdout + cobrado.stderr)

    # Atualizar o kit não toca no domínio do projeto
    (dominio / "casos.tsv").write_text(CASOS_DO_DOMINIO, encoding="utf-8")
    instalar(projeto, "--atualizar")
    confere("--atualizar preserva o domínio do projeto", (dominio / "checagens.tsv").read_text(encoding="utf-8") == REGRAS_DO_DOMINIO and (dominio / "dominio.md").read_text(encoding="utf-8") == DOMINIO)


class _ServidorDeGit(http.server.BaseHTTPRequestHandler):
    """Responde como um servidor de git: um repositório aberto, um fechado e um que devolve uma página."""

    def do_GET(self):  # noqa: N802 - nome exigido pela biblioteca
        if self.path.startswith("/time/aberto.git/info/refs"):
            self.send_response(200)
            self.send_header("Content-Type", "application/x-git-upload-pack-advertisement")
            self.end_headers()
            self.wfile.write(b"001e# service=git-upload-pack\n0000")
        elif self.path.startswith("/time/pagina.git/info/refs"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html>entre</html>")
        else:
            self.send_response(401)
            self.end_headers()

    def log_message(self, *args):
        pass


def testar_repositorio(tmp: Path) -> None:
    print("Repositório local ou privado")
    if shutil.which("git") is None:
        print("  (sem git nesta máquina: testes do repositório pulados)")
        return
    servidor = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _ServidorDeGit)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{servidor.server_address[1]}/time"
    try:
        projeto = tmp / "repositorio"
        projeto.mkdir()
        instalar(projeto)
        script = projeto / "entregaveis/_harness/scripts/repositorio.py"
        hooks = projeto / "entregaveis/_harness/hooks"

        def situacao() -> subprocess.CompletedProcess:
            return rodar([PY, script], projeto)

        def gravar(caminho: str) -> subprocess.CompletedProcess:
            dados = {"cwd": str(projeto), "session_id": "r1", "tool_name": "Write", "tool_input": {"file_path": caminho}}
            return rodar([PY, hooks / "antes_de_gravar.py"], projeto, json.dumps(dados))

        def comando(texto: str) -> subprocess.CompletedProcess:
            dados = {"cwd": str(projeto), "session_id": "r1", "tool_name": "Bash", "tool_input": {"command": texto}}
            return rodar([PY, hooks / "antes_de_comando.py"], projeto, json.dumps(dados))

        def remoto(url: str | None) -> None:
            rodar(["git", "remote", "remove", "origin"], projeto)
            if url:
                rodar(["git", "remote", "add", "origin", url], projeto)

        sem_git = situacao()
        confere("pasta sem git é aceita", sem_git.returncode == 0 and "Sem repositório remoto" in sem_git.stdout, sem_git.stdout + sem_git.stderr)
        rodar(["git", "init", "-q"], projeto)
        confere("git local sem remoto é aceito", situacao().returncode == 0 and gravar("entregaveis/_projeto/brief.md").returncode == 0)
        remoto("/srv/git/projeto.git")
        confere("remoto em disco conta como local", situacao().returncode == 0)

        # Remoto público
        remoto(f"{base}/aberto.git")
        publico = situacao()
        confere("remoto que entrega o clone sem credencial é público", publico.returncode == 1 and "PÚBLICO" in publico.stdout and "privado" in publico.stdout, publico.stdout + publico.stderr)
        barrado = gravar("entregaveis/_projeto/brief.md")
        confere("antes de gravar: bloqueia o brief em repositório público", barrado.returncode == 2 and "público" in barrado.stderr, barrado.stderr)
        confere("antes de gravar: bloqueia o domínio e o intake em repositório público", gravar("entregaveis/_dominio/dominio.md").returncode == 2 and gravar("entregaveis/_intake/registro.tsv").returncode == 2)
        confere("antes de gravar: bloqueia o briefing de um entregável novo", gravar("entregaveis/novo/briefing.md").returncode == 2)
        confere("antes de gravar: não barra o resto do repositório", gravar("src/app.py").returncode == 0 and gravar("entregaveis/_harness/REGRAS.md").returncode == 0 and gravar("README.md").returncode == 0)
        estado = rodar([PY, "entregaveis/_harness/scripts/estado.py"], projeto)
        confere("o estado diz que o repositório é público", "PÚBLICO" in estado.stdout, estado.stdout)
        confere("antes de comando: sem projeto, o envio do template passa", comando("git push -u origin main").returncode == 0)
        confere("sem projeto, a validação não cobra o repositório", "[repositorio]" not in validar(projeto).stdout)
        negada = rodar([PY, script, "--confirmar", "é privado, pode seguir"], projeto)
        confere("um remoto público não aceita confirmação", negada.returncode == 1 and not (projeto / "entregaveis/_projeto/repositorio.tsv").exists(), negada.stdout)

        montar_exemplo(projeto)
        envio = comando("git add -A && git commit -m x && git push -u origin main")
        confere("antes de comando: com projeto, bloqueia o envio a repositório público", envio.returncode == 2 and "público" in envio.stderr, envio.stderr)
        confere("antes de comando: não olha os outros comandos", comando("git status").returncode == 0 and comando("python3 entregaveis/_harness/scripts/validar.py").returncode == 0)
        confere("antes de comando: bloqueia tornar o repositório público", comando("gh repo create cliente-x --public --source .").returncode == 2 and comando("gh repo edit --visibility public").returncode == 2)
        confere("antes de comando: deixa criar repositório privado", comando("gh repo create cliente-x --private --source .").returncode == 0)
        reprovado = validar(projeto, "--so", "repositorio")
        confere("com projeto, a validação reprova o repositório público", reprovado.returncode == 1 and "[repositorio]" in reprovado.stdout, reprovado.stdout)

        # Remoto privado
        remoto(f"{base}/fechado.git")
        privado = situacao()
        confere("remoto que pede identificação é privado", privado.returncode == 0 and "privado" in privado.stdout, privado.stdout + privado.stderr)
        confere("em repositório privado, a gravação e o envio passam", gravar("entregaveis/_projeto/brief.md").returncode == 0 and comando("git push origin main").returncode == 0 and validar(projeto, "--so", "repositorio").returncode == 0)

        # Remoto que não dá para verificar
        for nome, url in (("servidor que não responde", "http://127.0.0.1:1/time/sumido.git"), ("resposta que não é de git", f"{base}/pagina.git")):
            remoto(url)
            duvida = situacao()
            confere(f"{nome}: fica como não verificado e não é aceito", duvida.returncode == 1 and "não verificado" in duvida.stdout and "--confirmar" in duvida.stdout, duvida.stdout + duvida.stderr)
        confere("antes de gravar e antes de comando: bloqueiam o remoto não verificado", gravar("entregaveis/_projeto/brief.md").returncode == 2 and comando("git push").returncode == 2)
        confirmada = rodar([PY, script, "--confirmar", "sim, é o repositório privado do time"], projeto)
        registro = projeto / "entregaveis/_projeto/repositorio.tsv"
        confere("a confirmação do consultor fica registrada com as palavras dele", confirmada.returncode == 0 and "sim, é o repositório privado do time" in registro.read_text(encoding="utf-8"), confirmada.stdout + confirmada.stderr)
        confere("depois da confirmação, o remoto não verificado é aceito", situacao().returncode == 0 and gravar("entregaveis/_projeto/brief.md").returncode == 0 and comando("git push").returncode == 0)
        remoto(f"{base}/aberto.git")
        confere("a confirmação de um remoto não vale para outro", situacao().returncode == 1)

        codigo = (
            "import sys; sys.path.insert(0, 'entregaveis/_harness/scripts'); import repositorio as r; "
            "print(r.endereco('git@github.com:time/projeto.git'), r.endereco('ssh://git@git.exemplo.com:2222/time/projeto.git'), "
            "r.endereco('https://usuario@gitlab.com/grupo/sub/projeto.git'), r.endereco('../outro'), r.endereco('C:/git/projeto'))"
        )
        lidos = rodar([PY, "-c", codigo], projeto).stdout
        confere("lê endereços de remoto em ssh, https e disco", "('https', 'github.com', 'time/projeto') ('https', 'git.exemplo.com', 'time/projeto') ('https', 'gitlab.com', 'grupo/sub/projeto') None None" in lidos, lidos)
    finally:
        servidor.shutdown()


CONTEUDO_COM_VISUAIS = CONTEUDO.replace(
    "Das 14 plataformas contratadas, duas enviam e-mail para a mesma base.\n",
    """Das 14 plataformas contratadas, duas enviam e-mail para a mesma base.

- A plataforma A cobre **campanhas** e jornadas.
- A plataforma B cobre só campanhas.

```grafico
tipo: barras
destaque: E-mail
dados:
Função | Plataformas
E-mail | 2
Dados | 1
Mídia | 1
```
""",
).replace(
    "A diretora de marketing aprova o plano de migração.\n",
    """A diretora de marketing aprova o plano de migração.

| Quem | Faz o quê | Até quando |
| --- | --- | --- |
| Diretoria | Aprova o desligamento | Dezembro |
| Operações | Migra as jornadas | Fevereiro |
""",
)

DOCUMENTO = """# Diagnóstico de martech

A diretoria aprova o desligamento de uma plataforma de e-mail até dezembro.

## Duas plataformas fazem o mesmo trabalho

Das 14 plataformas contratadas, duas enviam e-mail para a mesma base [E-001].

- A plataforma A cobre **campanhas** e jornadas.
- A plataforma B cobre só campanhas.

| Função | Plataformas |
| --- | --- |
| E-mail | 2 |
| Dados | 1 |

## O pedido

1. A diretoria aprova o desligamento.
2. Operações migra as jornadas.
"""

PLANILHA = """# Planilha

## Perguntas que a planilha responde

- Que plataformas estão contratadas e quanto custam.

## Abas

| Aba | O que contém | Origem dos dados (E-nnn) | Data dos dados |
| --- | --- | --- | --- |
| Inventário | Uma linha por plataforma contratada | E-001 | 2026-10-01 |

## Dicionário de dados

| Aba | Coluna | Definição | Unidade | Regra de cálculo |
| --- | --- | --- | --- | --- |
| Inventário | Custo anual | Valor do contrato em doze meses | R$ | Soma das parcelas |

## Gráficos e análises

| Gráfico ou análise | Pergunta que responde | Achado que o título deve dizer |
| --- | --- | --- |
| Custo por plataforma | Onde está o gasto | A plataforma de dados custa mais que as duas de e-mail |

```grafico
aba: Inventário
tipo: colunas
titulo: A plataforma de dados custa mais que as duas de e-mail
categorias: Plataforma
valores: Custo anual
```
"""


def tem_pacote(nome: str) -> bool:
    try:
        __import__(nome)
        return True
    except ImportError:
        return False


def testar_gerador(tmp: Path) -> None:
    print("Gerador de arquivos")
    projeto = tmp / "gerador"
    projeto.mkdir()
    instalar(projeto)
    pasta = montar_exemplo(projeto)
    saida = pasta / "saida"
    materiais = projeto / "entregaveis/_intake/materiais"
    marca = projeto / "entregaveis/_projeto/marca.md"
    marca_em_branco = marca.read_text(encoding="utf-8")

    def gerar(*opcoes: str) -> subprocess.CompletedProcess:
        return rodar([PY, "entregaveis/_harness/scripts/gerar.py", *opcoes], projeto)

    (pasta / "conteudo.md").write_text(CONTEUDO_COM_VISUAIS, encoding="utf-8")
    grande = CONTEUDO_COM_VISUAIS.replace("Mídia | 1\n", "".join(f"Função {n} | {n}\n" for n in range(40)))
    (pasta / "conteudo.md").write_text(grande, encoding="utf-8")
    confere("os dados de um bloco de gráfico não contam como texto da página", "[densidade]" not in validar(projeto, "diag").stdout)
    (pasta / "conteudo.md").write_text(CONTEUDO_COM_VISUAIS, encoding="utf-8")
    confere("recusa formato que o script não gera", gerar("diag", "--formato", "html").returncode != 0)
    confere("recusa entregável que não existe", gerar("nada").returncode != 0)

    if not tem_pacote("pptx"):
        sem = gerar("diag")
        confere("sem o pacote, diz como instalar", sem.returncode != 0 and "pip install python-pptx" in sem.stdout + sem.stderr, sem.stdout + sem.stderr)
        print("  (python-pptx não está instalado: testes de PowerPoint pulados)")
    else:
        from pptx import Presentation
        from pptx.dml.color import RGBColor

        def textos(slide) -> str:
            return "\n".join(f.text_frame.text for f in slide.shapes if f.has_text_frame)

        (pasta / "storyline.md").write_text(STORYLINE.replace("aprovada: sim", "aprovada: nao"), encoding="utf-8")
        recusa = gerar("diag")
        confere("recusa gerar sem storyline aprovada", recusa.returncode != 0 and "storyline" in recusa.stdout + recusa.stderr and not saida.exists(), recusa.stdout + recusa.stderr)
        (pasta / "storyline.md").write_text(STORYLINE, encoding="utf-8")
        (pasta / "conteudo.md").write_text(CONTEUDO_COM_VISUAIS + "\nA equipe aprova — e segue.\n", encoding="utf-8")
        reprovado = gerar("diag")
        confere("recusa gerar o que reprova nas checagens", reprovado.returncode != 0 and "[texto]" in reprovado.stdout and not (saida / "diag.pptx").exists(), reprovado.stdout + reprovado.stderr)
        rascunho = gerar("diag", "--rascunho")
        confere("--rascunho gera com a marca de rascunho em cada página", rascunho.returncode == 0 and all("RASCUNHO" in textos(s) for s in Presentation(str(saida / "diag-rascunho.pptx")).slides), rascunho.stdout + rascunho.stderr)
        (pasta / "conteudo.md").write_text(CONTEUDO_COM_VISUAIS, encoding="utf-8")

        neutro = gerar("diag")
        confere("gera o PowerPoint e avisa que não há modelo", neutro.returncode == 0 and "desenho neutro" in neutro.stdout and (saida / "diag.pptx").is_file(), neutro.stdout + neutro.stderr)
        slides = list(Presentation(str(saida / "diag.pptx")).slides)
        confere("uma página por slide, com o título de cada uma", [s.shapes.title.text_frame.text for s in slides] == ["Diagnóstico de martech", "Duas plataformas de e-mail fazem o mesmo trabalho", "A diretoria aprova o desligamento até dezembro"])
        confere("a capa leva o texto para o subtítulo", "Para a diretoria de marketing." in textos(slides[0]))
        confere("as notas vão para as notas de quem apresenta", "campanha de aniversário" in slides[1].notes_slide.notes_text_frame.text and "campanha de aniversário" not in textos(slides[1]))
        confere("a lista e o negrito chegam ao slide", "A plataforma B cobre só campanhas." in textos(slides[1]) and any(c.font.bold for f in slides[1].shapes if f.has_text_frame for par in f.text_frame.paragraphs for c in par.runs))
        graficos = [f.chart for f in slides[1].shapes if getattr(f, "has_chart", False)]
        confere("o bloco de gráfico vira gráfico nativo com os dados", len(graficos) == 1 and list(graficos[0].plots[0].categories) == ["E-mail", "Dados", "Mídia"] and list(graficos[0].plots[0].series[0].values) == [2, 1, 1])
        pontos = graficos[0].plots[0].series[0].points
        confere("o destaque fica na categoria citada e o resto em cinza", pontos[0].format.fill.fore_color.rgb == RGBColor.from_string("0B5CAD") and pontos[1].format.fill.fore_color.rgb == RGBColor.from_string("A9B3BD"))
        confere("a página que cita evidência ganha a linha de fonte", "Fonte: Inventário de contratos, 2026-10-01." in textos(slides[1]) and "Fonte:" not in textos(slides[2]))
        tabelas = [f.table for f in slides[2].shapes if getattr(f, "has_table", False)]
        confere("a tabela Markdown vira tabela", len(tabelas) == 1 and len(tabelas[0].rows) == 3 and tabelas[0].cell(2, 1).text == "Migra as jornadas")

        # Sobre um modelo: layouts com nome próprio e páginas de exemplo
        modelo = Presentation()
        for indice, nome in ((0, "Capa da casa"), (1, "Texto da casa"), (2, "Divisor da casa"), (5, "Só título da casa")):
            modelo.slide_layouts[indice].name = nome
        for _ in range(2):
            modelo.slides.add_slide(modelo.slide_layouts[1]).shapes.title.text_frame.text = "EXEMPLO DO MODELO"
        modelo.save(str(materiais / "modelo.pptx"))
        marca.write_text(
            marca_em_branco.replace("| Modelo de apresentação | | |", "| Modelo de apresentação | entregaveis/_intake/materiais/modelo.pptx | M-001 |")
            .replace("| Cores de destaque em gráficos | | |", "| Cores de destaque em gráficos | #C2410C e #D4D4D8 | M-001 |")
            .replace("| Tipo de página | Layout |\n| --- | --- |\n| | |", "| Tipo de página | Layout |\n| --- | --- |\n| pedido | Só título da casa |"),
            encoding="utf-8",
        )
        com_modelo = gerar("diag")
        slides = list(Presentation(str(saida / "diag.pptx")).slides)
        confere("gera sobre o modelo registrado na marca", com_modelo.returncode == 0 and "sobre modelo.pptx" in com_modelo.stdout and "desenho neutro" not in com_modelo.stdout, com_modelo.stdout + com_modelo.stderr)
        confere("as páginas de exemplo do modelo saem", len(slides) == 3 and not any("EXEMPLO DO MODELO" in textos(s) for s in slides))
        confere("o layout é escolhido pelo tipo de página e pela tabela da marca", [s.slide_layout.name for s in slides] == ["Capa da casa", "Texto da casa", "Só título da casa"], str([s.slide_layout.name for s in slides]))
        ponto = [f.chart for f in slides[1].shapes if getattr(f, "has_chart", False)][0].plots[0].series[0].points[0]
        confere("as cores do gráfico vêm da marca", ponto.format.fill.fore_color.rgb == RGBColor.from_string("C2410C"))
        lista = gerar("--layouts")
        confere("--layouts lista os layouts do modelo com os campos", lista.returncode == 0 and "Capa da casa: center_title" in lista.stdout, lista.stdout + lista.stderr)
        (pasta / "conteudo.md").write_text(CONTEUDO_COM_VISUAIS.replace("<!-- tipo: capa; secao: ; fonte: ; recurso: -->", "<!-- tipo: capa; secao: ; fonte: ; recurso: ; layout: Divisor da casa -->"), encoding="utf-8")
        gerar("diag")
        confere("o campo layout da página vence a escolha automática", Presentation(str(saida / "diag.pptx")).slides[0].slide_layout.name == "Divisor da casa")
        (pasta / "conteudo.md").write_text(CONTEUDO_COM_VISUAIS, encoding="utf-8")
        marca.write_text(marca_em_branco.replace("| Modelo de apresentação | | |", "| Modelo de apresentação | modelos/sumiu.pptx | M-001 |"), encoding="utf-8")
        sumido = gerar("diag")
        confere("modelo registrado e não encontrado é erro, não desenho neutro", sumido.returncode != 0 and "sumiu.pptx" in sumido.stdout + sumido.stderr)
        marca.write_text(marca_em_branco, encoding="utf-8")

        # Modelo exportado por outro programa: nomes e números de campo repetidos, propriedades ligadas fora do padrão
        import zipfile

        from pptx.util import Pt

        confere("o título que não cabe no campo tem a letra reduzida, e o que cabe fica como está",
                slides[0].shapes.title.text_frame.paragraphs[0].runs[0].font.size is None
                and (slides[1].shapes.title.text_frame.paragraphs[0].runs[0].font.size or Pt(99)) < Pt(44))
        estranho = Presentation()
        estranho.slide_layouts[0].name = estranho.slide_layouts[1].name = "Da casa"
        estranho.slide_layouts[1].placeholders[1]._element.ph.idx = 0
        estranho.save(str(tmp / "bruto.pptx"))
        padrao = b"http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties"
        with zipfile.ZipFile(tmp / "bruto.pptx") as origem, zipfile.ZipFile(materiais / "estranho.pptx", "w", zipfile.ZIP_DEFLATED) as copia:
            for item in origem.infolist():
                dados = origem.read(item.filename)
                if item.filename == "_rels/.rels":
                    dados = dados.replace(padrao, padrao.replace(b"/package/", b"/officedocument/"))
                copia.writestr(item, dados)
        lista = gerar("--layouts", str(materiais / "estranho.pptx"))
        confere("--layouts numera os layouts e avisa dos nomes repetidos", "1. Da casa" in lista.stdout and "2. Da casa" in lista.stdout and "use o número" in lista.stdout, lista.stdout + lista.stderr)
        (pasta / "conteudo.md").write_text(CONTEUDO_COM_VISUAIS.replace("<!-- tipo: capa; secao: ; fonte: ; recurso: -->", "<!-- tipo: capa; secao: ; fonte: ; recurso: ; layout: 6 -->"), encoding="utf-8")
        de_fora = gerar("diag", "--modelo", str(materiais / "estranho.pptx"))
        slides_de_fora = list(Presentation(str(saida / "diag.pptx")).slides)
        confere("o layout também é escolhido pelo número", de_fora.returncode == 0 and slides_de_fora[0].slide_layout.name == "Title Only", de_fora.stdout + de_fora.stderr)
        with zipfile.ZipFile(saida / "diag.pptx") as gerado:
            confere("as propriedades ligadas fora do padrão não são duplicadas", gerado.namelist().count("docProps/core.xml") == 1)
        campos = [f for f in slides_de_fora[1].placeholders]
        confere("com número de campo repetido, o corpo fica na posição do corpo, abaixo do título",
                len(campos) == 2 and campos[1].top >= campos[0].top + campos[0].height, str([(f.top, f.height) for f in campos]))
        (pasta / "conteudo.md").write_text(CONTEUDO_COM_VISUAIS, encoding="utf-8")

        # Outro idioma
        (pasta / "conteudo.es.md").write_text(CONTEUDO_COM_VISUAIS, encoding="utf-8")
        versao = gerar("diag", "--idioma", "es", "--rascunho")
        confere("--idioma gera a versão com o nome e o rótulo do idioma", versao.returncode == 0 and "Fuente: Inventário" in textos(Presentation(str(saida / "diag-es-rascunho.pptx")).slides[1]), versao.stdout + versao.stderr)
        (pasta / "conteudo.es.md").unlink()

        pdf = gerar("diag", "--pdf")
        confere("--pdf gera o PDF, ou diz por que não gerou", pdf.returncode == 0 and ((saida / "diag.pdf").is_file() or "PDF não foi gerado" in pdf.stdout), pdf.stdout + pdf.stderr)

    if not tem_pacote("docx"):
        print("  (python-docx não está instalado: testes de Word pulados)")
    else:
        from docx import Document

        (pasta / "documento.md").write_text(DOCUMENTO, encoding="utf-8")
        modelo = Document()
        modelo.add_paragraph("TEXTO DE EXEMPLO DO MODELO")
        modelo.sections[0].header.paragraphs[0].text = "Cabeçalho da casa"
        modelo.save(str(materiais / "modelo.docx"))
        marca.write_text(marca_em_branco.replace("| Modelo de documento | | |", "| Modelo de documento | entregaveis/_intake/materiais/modelo.docx | M-002 |"), encoding="utf-8")
        feito = gerar("diag", "--formato", "docx")
        confere("gera o Word sobre o modelo", feito.returncode == 0 and (saida / "diag.docx").is_file() and "sobre modelo.docx" in feito.stdout, feito.stdout + feito.stderr)
        doc = Document(str(saida / "diag.docx"))
        estilos = [(par.style.name, par.text) for par in doc.paragraphs if par.text.strip()]
        confere("título e seções usam os estilos do modelo", ("Title", "Diagnóstico de martech") in estilos and ("Heading 1", "O pedido") in estilos, str(estilos[:6]))
        confere("o texto de exemplo sai e o cabeçalho do modelo fica", not any("EXEMPLO" in texto for _, texto in estilos) and doc.sections[0].header.paragraphs[0].text == "Cabeçalho da casa")
        confere("listas e tabela chegam ao documento", ("List Bullet", "A plataforma B cobre só campanhas.") in estilos and ("List Number", "Operações migra as jornadas.") in estilos and len(doc.tables) == 1 and doc.tables[0].cell(1, 1).text == "2")
        confere("as evidências citadas formam a seção de fontes", ("Heading 1", "Fontes") in estilos and any(texto.startswith("E-001: Inventário de contratos") for _, texto in estilos))
        marca.write_text(marca_em_branco, encoding="utf-8")
        (pasta / "documento.md").unlink()

    if not tem_pacote("openpyxl"):
        print("  (openpyxl não está instalado: testes de Excel pulados)")
    else:
        from openpyxl import load_workbook

        (pasta / "planilha.md").write_text(PLANILHA, encoding="utf-8")
        (pasta / "dados").mkdir()
        (pasta / "dados/inventario.csv").write_text("Plataforma;Função;Custo anual;Usuários\nA;E-mail;120000;14\nB;E-mail;95000,50;6\nC;Dados;300000;22\n", encoding="utf-8")
        feito = gerar("diag", "--formato", "xlsx")
        confere("gera o Excel", feito.returncode == 0 and (saida / "diag.xlsx").is_file(), feito.stdout + feito.stderr)
        livro = load_workbook(str(saida / "diag.xlsx"))
        confere("a planilha tem leitura, gráficos, dados e dicionário", livro.sheetnames == ["Leitura", "Gráficos", "Inventário", "Dicionário"], str(livro.sheetnames))
        dados = livro["Inventário"]
        confere("os números entram como números, com a vírgula decimal lida", dados["C2"].value == 120000 and dados["C3"].value == 95000.5 and dados["A2"].value == "A")
        confere("a aba de dados tem cabeçalho fixo e filtro", dados.freeze_panes == "A2" and dados.auto_filter.ref == "A1:D4" and dados["A1"].font.bold)
        confere("a aba de leitura diz a pergunta e a origem dos dados", any("Que plataformas estão contratadas" in str(c.value) for c in livro["Leitura"]["A"]) and any("Inventário de contratos" in str(c.value) for linha in livro["Leitura"].iter_rows() for c in linha))
        confere("o gráfico é nativo e o dicionário traz a definição", len(livro["Gráficos"]._charts) == 1 and livro["Dicionário"]["C2"].value == "Valor do contrato em doze meses")
        (pasta / "planilha.md").write_text(PLANILHA.replace("valores: Custo anual", "valores: Custo mensal"), encoding="utf-8")
        errado = gerar("diag", "--formato", "xlsx")
        confere("gráfico que cita coluna inexistente é erro", errado.returncode != 0 and "Custo mensal" in errado.stdout + errado.stderr)


def testar_pacotes(tmp: Path) -> None:
    print("Pacotes")
    pacotes = sorted(p for p in (HARNESS / "pacotes").iterdir() if p.is_dir())
    confere("há ao menos um pacote", bool(pacotes))
    leia_me = (HARNESS / "pacotes" / "LEIA-ME.md").read_text(encoding="utf-8")
    for pacote in pacotes:
        nome = pacote.name
        for arquivo in ("PACOTE.md", "pedido-de-dados.tsv", "entrevistas.md", "glossario.tsv", "skill/SKILL.md"):
            confere(f"{nome}: tem {arquivo}", (pacote / arquivo).is_file())
        confere(f"{nome}: está na lista de pacotes disponíveis", f"`{nome}`" in leia_me)
        skill = (pacote / "skill/SKILL.md").read_text(encoding="utf-8")
        cabecalho = skill.split("---\n")[1]
        campos = dict(re.findall(r"^(\w+): (.*)$", cabecalho, flags=re.MULTILINE))
        descricao = campos.get("description", "")
        confere(f"{nome}: a skill se chama pacote-{nome}", campos.get("name") == f"pacote-{nome}")
        confere(f"{nome}: a descrição da skill começa por 'Use' e é um valor YAML simples", descricao.startswith("Use ") and ": " not in descricao and " #" not in descricao and len(descricao) <= 1024)
        confere(f"{nome}: a skill traz a marca de origem do kit", "origem: harness-de-entregaveis" in cabecalho)
        titulos = set(re.findall(r"^#{2,3} (.+)$", (pacote / "PACOTE.md").read_text(encoding="utf-8"), flags=re.MULTILINE))
        for secao in re.findall(r'"([^"]+)"', " ".join(skill.split())):
            confere(f"{nome}: a seção '{secao}' citada na skill existe em PACOTE.md", secao in titulos)
        for arquivo, colunas in (("pedido-de-dados.tsv", 5), ("glossario.tsv", 4)):
            linhas = [l for l in (pacote / arquivo).read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
            tortas = [l for l in linhas if len(l.split("\t")) != colunas]
            confere(f"{nome}: {arquivo} tem {colunas} colunas em toda linha", len(linhas) > 5 and not tortas, "\n".join(tortas[:3]))
        prioridades = {l.split("\t")[4] for l in (pacote / "pedido-de-dados.tsv").read_text(encoding="utf-8").splitlines()[4:] if "\t" in l}
        confere(f"{nome}: as prioridades do pedido de dados são as três previstas", prioridades <= {"essencial", "importante", "complementar"}, str(prioridades))

    projeto = tmp / "pacotes"
    projeto.mkdir()
    instalar(projeto, "--pasta", "consultoria")
    preparar = [PY, "consultoria/_harness/scripts/preparar.py"]
    inexistente = rodar(preparar + ["--pacote", "nao-existe"], projeto)
    confere("ativar pacote que não existe falha e lista os disponíveis", inexistente.returncode != 0 and "martech-adtech" in inexistente.stdout + inexistente.stderr, inexistente.stdout + inexistente.stderr)
    ativacao = rodar(preparar + ["--pacote", "martech-adtech"], projeto)
    skill = projeto / ".claude/skills/pacote-martech-adtech/SKILL.md"
    confere("ativar o pacote copia a skill", ativacao.returncode == 0 and skill.is_file(), ativacao.stdout + ativacao.stderr)
    confere("a skill ativada aponta para a pasta deste projeto", skill.is_file() and "consultoria/_harness/pacotes/martech-adtech/" in skill.read_text(encoding="utf-8") and "entregaveis/" not in skill.read_text(encoding="utf-8"))
    glossario = (projeto / "consultoria/_projeto/glossario.tsv").read_text(encoding="utf-8")
    confere("ativar o pacote soma os termos ao glossário", "\nCDP\t" in glossario and "\nDSP\t" in glossario)
    confere("ativar o pacote preenche o campo do brief", "pacotes: martech-adtech\n" in (projeto / "consultoria/_projeto/brief.md").read_text(encoding="utf-8"))
    rodar(preparar + ["--pacote", "martech-adtech"], projeto)
    depois = (projeto / "consultoria/_projeto/glossario.tsv").read_text(encoding="utf-8")
    confere("ativar de novo não repete termos nem o nome no brief", depois == glossario and "pacotes: martech-adtech\n" in (projeto / "consultoria/_projeto/brief.md").read_text(encoding="utf-8"))
    estado = rodar([PY, "consultoria/_harness/scripts/validar.py"], projeto)
    confere("as checagens rodam com o pacote ativo", estado.returncode == 0, estado.stdout + estado.stderr)
    skill.write_text(skill.read_text(encoding="utf-8") + "\nlinha de versão antiga\n", encoding="utf-8")
    instalar(projeto, "--pasta", "consultoria", "--atualizar")
    confere("--atualizar renova a skill do pacote ativado", "linha de versão antiga" not in skill.read_text(encoding="utf-8"))
    todos = tmp / "todos-os-pacotes"
    todos.mkdir()
    instalar(todos)
    for pacote in pacotes:
        rodar([PY, "entregaveis/_harness/scripts/preparar.py", "--pacote", pacote.name], todos)
    ativos = (todos / "entregaveis/_projeto/brief.md").read_text(encoding="utf-8")
    confere("um projeto pode ativar todos os pacotes", all((todos / f".claude/skills/pacote-{p.name}/SKILL.md").is_file() and p.name in ativos for p in pacotes), ativos[:300])
    chaves = [tuple(l.split("\t")[i] for i in (0, 3)) for l in (todos / "entregaveis/_projeto/glossario.tsv").read_text(encoding="utf-8").splitlines() if "\t" in l and not l.startswith("#")]
    confere("pacotes somados não repetem termos no glossário", len(chaves) == len({(t.lower(), i) for t, i in chaves}), str([c for c in chaves if chaves.count(c) > 1][:5]))
    sem_pacote = tmp / "sem-pacote"
    sem_pacote.mkdir()
    instalar(sem_pacote)
    confere("a skill de pacote não é instalada em projeto que não o ativou", not (sem_pacote / ".claude/skills/pacote-martech-adtech").exists())


def testar_levantamento(tmp: Path) -> None:
    print("Levantamento de projeto existente")
    projeto = tmp / "levantar"
    (projeto / "docs").mkdir(parents=True)
    (projeto / "docs/modelo-da-marca.potx").write_text("x", encoding="utf-8")
    (projeto / "docs/proposta.docx").write_text("x", encoding="utf-8")
    (projeto / "AGENTS.md").write_text("Regras.\n", encoding="utf-8")
    instalar(projeto)
    saida = rodar([PY, "entregaveis/_harness/scripts/levantar.py"], projeto)
    confere("levantar.py lista o que o projeto já tem", saida.returncode == 0 and "proposta.docx" in saida.stdout and "AGENTS.md" in saida.stdout, saida.stdout + saida.stderr)


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="kit-"))
    try:
        testar_skills()
        testar_referencias()
        testar_texto_do_kit()
        testar_instalador(tmp)
        testar_checagens(tmp)
        testar_hooks(tmp)
        testar_interativos(tmp)
        testar_dominio(tmp)
        testar_repositorio(tmp)
        testar_gerador(tmp)
        testar_pacotes(tmp)
        testar_levantamento(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print()
    if falhas:
        print(f"{len(falhas)} de {total} conferências falharam:")
        for f in falhas:
            print(f"  - {f}")
        return 1
    print(f"Tudo certo: {total} conferências passaram.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
