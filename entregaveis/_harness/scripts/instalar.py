#!/usr/bin/env python3
"""Instala o harness de entregáveis em um projeto.

O projeto de destino pode ser qualquer um: vazio, um repositório de
código, uma pasta só com apresentações, com ou sem git, com ou sem
regras de agente próprias. O instalador não supõe nada e nunca
sobrescreve um arquivo do projeto. Ele acrescenta a pasta do harness, as
skills, os hooks e um bloco marcado nos arquivos de instrução que já
existirem. Pode rodar de novo sem duplicar nada.

Uso:
    instalar.py [--destino PASTA] [--pasta NOME] [--simular] [--atualizar] [--ci]

    --destino    raiz do projeto que recebe o harness (padrão: pasta atual)
    --pasta      nome da pasta de entregáveis no destino (padrão: entregaveis)
    --simular    só mostra o que seria feito
    --atualizar  substitui o que pertence ao kit pela versão desta cópia
    --ci         instala também o workflow de checagens do GitHub Actions
"""
from __future__ import annotations

import argparse
import filecmp
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1]
ORIGEM = HARNESS.parents[1]
PADRAO = "entregaveis"
INICIO = "harness-de-entregaveis: inicio"
FIM = "harness-de-entregaveis: fim"
IGNORAR = shutil.ignore_patterns("__pycache__", ".estado", "*.pyc")
# Linha que toda skill do kit traz no cabeçalho. Skill sem ela é do projeto.
MARCA_DE_SKILL = "origem: harness-de-entregaveis"
# Skills do kit que mudaram de nome. A antiga sai na atualização.
SKILLS_RENOMEADAS = {"relatar-ao-dono": "relatar-ao-consultor"}

# Arquivos de instrução de outros agentes. Recebem o bloco só se já existem.
OUTROS_AGENTES = ["GEMINI.md", ".github/copilot-instructions.md", ".cursorrules", ".windsurfrules"]


class Instalador:
    def __init__(self, destino: Path, pasta: str, simular: bool, atualizar: bool, ci: bool):
        self.destino = destino
        self.pasta = pasta
        self.simular = simular
        self.atualizar = atualizar
        self.ci = ci
        self.feito: list[str] = []
        self.mantido: list[str] = []

    # --- utilidades -------------------------------------------------------

    def nota(self, texto: str) -> None:
        self.feito.append(texto)

    def ajustar(self, texto: str) -> str:
        """Troca o nome padrão da pasta pelo nome escolhido para o destino."""
        if self.pasta == PADRAO:
            return texto
        return texto.replace(f"{PADRAO}/", f"{self.pasta}/")

    def gravar(self, arquivo: Path, texto: str) -> None:
        if not self.simular:
            arquivo.parent.mkdir(parents=True, exist_ok=True)
            arquivo.write_text(texto, encoding="utf-8")

    def ajustar_arvore(self, raiz: Path) -> None:
        if self.pasta == PADRAO or self.simular:
            return
        for arquivo in raiz.rglob("*"):
            if arquivo.is_file() and (arquivo.suffix in {".md", ".json", ".yml", ".tsv", ".txt"} or arquivo.name == "gitignore"):
                texto = arquivo.read_text(encoding="utf-8")
                novo = self.ajustar(texto)
                if novo != texto:
                    arquivo.write_text(novo, encoding="utf-8")

    # --- passos -----------------------------------------------------------

    def copiar_harness(self) -> None:
        alvo = self.destino / self.pasta / "_harness"
        versao_kit = (HARNESS / "VERSAO").read_text(encoding="utf-8").strip()
        if alvo.exists():
            instalada = (alvo / "VERSAO").read_text(encoding="utf-8").strip() if (alvo / "VERSAO").is_file() else "?"
            if not self.atualizar:
                if instalada != versao_kit:
                    self.mantido.append(f"{self.pasta}/_harness está na versão {instalada} e esta cópia do kit é a {versao_kit}. Use --atualizar para trocar.")
                return
            if not self.simular:
                for item in alvo.iterdir():
                    if item.name == ".estado":
                        continue
                    shutil.rmtree(item) if item.is_dir() else item.unlink()
            self.nota(f"{self.pasta}/_harness atualizado de {instalada} para {versao_kit}")
        else:
            self.nota(f"{self.pasta}/_harness criado (versão {versao_kit})")
        if not self.simular:
            shutil.copytree(HARNESS, alvo, ignore=IGNORAR, dirs_exist_ok=True)
            self.ajustar_arvore(alvo)

    def copiar_skills(self) -> None:
        origem = ORIGEM / ".claude" / "skills"
        if not origem.is_dir():
            self.mantido.append("Esta cópia do kit não tem .claude/skills. As skills não foram instaladas.")
            return
        skills = [(p.name, p) for p in sorted(origem.iterdir()) if p.is_dir()]
        # A skill de um pacote só existe no projeto que ativou o pacote. Ela acompanha a atualização.
        for pacote in sorted((HARNESS / "pacotes").glob("*/skill")):
            nome = f"pacote-{pacote.parent.name}"
            if (self.destino / ".claude" / "skills" / nome).exists():
                skills.append((nome, pacote))
        for antiga, nova in SKILLS_RENOMEADAS.items():
            alvo = self.destino / ".claude" / "skills" / antiga
            arquivo = alvo / "SKILL.md"
            if not arquivo.is_file() or MARCA_DE_SKILL not in arquivo.read_text(encoding="utf-8"):
                continue  # não existe, ou é uma skill do projeto com o mesmo nome
            if not self.atualizar:
                self.mantido.append(f".claude/skills/{antiga} é de outra versão do kit, em que ela passou a se chamar {nova}. Use --atualizar para trocar.")
                continue
            if not self.simular:
                shutil.rmtree(alvo)
            self.nota(f".claude/skills/{antiga} retirada: ela passou a se chamar {nova}")
        for nome_da_skill, skill in skills:
            alvo = self.destino / ".claude" / "skills" / nome_da_skill
            if alvo.exists():
                texto_kit = self.ajustar((skill / "SKILL.md").read_text(encoding="utf-8"))
                atual = (alvo / "SKILL.md").read_text(encoding="utf-8") if (alvo / "SKILL.md").is_file() else ""
                if atual == texto_kit:
                    continue
                if MARCA_DE_SKILL not in atual:
                    # A skill é do projeto e só coincide no nome. Nunca é trocada.
                    self.mantido.append(
                        f".claude/skills/{nome_da_skill} já existia no projeto e não veio do kit. Ela foi mantida e a do kit "
                        f"não foi instalada. A versão do kit está em {skill / 'SKILL.md'}: decida com o consultor qual fica "
                        "ou renomeie a do projeto."
                    )
                    continue
                if not self.atualizar:
                    self.mantido.append(f".claude/skills/{nome_da_skill} é de outra versão do kit. Mantida. Use --atualizar para trocar.")
                    continue
                if not self.simular:
                    shutil.rmtree(alvo)
                self.nota(f".claude/skills/{nome_da_skill} atualizada")
            else:
                self.nota(f".claude/skills/{nome_da_skill} criada")
            if not self.simular:
                shutil.copytree(skill, alvo, ignore=IGNORAR)
                self.ajustar_arvore(alvo)

    def mesclar_settings(self) -> None:
        arquivo = self.destino / ".claude" / "settings.json"
        nosso = json.loads(self.ajustar((HARNESS / "instalacao" / "settings.json").read_text(encoding="utf-8")))
        if arquivo.is_file():
            try:
                atual = json.loads(arquivo.read_text(encoding="utf-8"))
            except ValueError:
                self.mantido.append(".claude/settings.json existe e não é um JSON válido. Os hooks não foram instalados: corrija o arquivo e rode de novo.")
                return
        else:
            atual = {}
        antes = json.dumps(atual, sort_keys=True)
        permitidos = atual.setdefault("permissions", {}).setdefault("allow", [])
        for regra in nosso["permissions"]["allow"]:
            if regra not in permitidos:
                permitidos.append(regra)
        hooks = atual.setdefault("hooks", {})
        for evento, grupos in nosso["hooks"].items():
            existentes = hooks.setdefault(evento, [])
            comandos = {h.get("command") for g in existentes for h in g.get("hooks", [])}
            # Um hook do harness instalado com outro nome de pasta é trocado, não duplicado.
            for grupo in grupos:
                script = re.search(r"_harness/hooks/(\w+\.py)", grupo["hooks"][0]["command"]).group(1)
                if grupo["hooks"][0]["command"] in comandos:
                    continue
                existentes[:] = [g for g in existentes if not any(f"_harness/hooks/{script}" in h.get("command", "") for h in g.get("hooks", []))]
                existentes.append(grupo)
        if json.dumps(atual, sort_keys=True) != antes:
            self.gravar(arquivo, json.dumps(atual, indent=2, ensure_ascii=False) + "\n")
            self.nota(".claude/settings.json: hooks e permissões do harness " + ("mesclados" if antes != "{}" else "criados"))

    def inserir_bloco(self, arquivo: Path, bloco: str, titulo: str | None, criar: bool) -> None:
        """Põe o bloco entre as linhas marcadoras, ou troca o que já está lá."""
        bloco = self.ajustar(bloco).strip() + "\n"
        nome = str(arquivo.relative_to(self.destino))
        if not arquivo.is_file():
            if not criar:
                return
            self.gravar(arquivo, (f"# {titulo}\n\n" if titulo else "") + bloco)
            self.nota(f"{nome} criado com o bloco do harness")
            return
        texto = arquivo.read_text(encoding="utf-8")
        padrao = re.compile(r"^[^\n]*" + re.escape(INICIO) + r".*?" + re.escape(FIM) + r"[^\n]*\n?", flags=re.DOTALL | re.MULTILINE)
        if padrao.search(texto):
            novo = padrao.sub(lambda _: bloco, texto, count=1)
        else:
            novo = texto.rstrip("\n") + "\n\n" + bloco if texto.strip() else bloco
        if novo != texto:
            self.gravar(arquivo, novo)
            self.nota(f"{nome}: bloco do harness " + ("atualizado" if padrao.search(texto) else "acrescentado ao fim"))

    def blocos(self) -> None:
        agentes = (HARNESS / "instalacao" / "bloco-agents.md").read_text(encoding="utf-8")
        claude = (HARNESS / "instalacao" / "bloco-claude.md").read_text(encoding="utf-8")
        self.inserir_bloco(self.destino / "AGENTS.md", agentes, "Instruções para agentes", criar=True)
        self.inserir_bloco(self.destino / "CLAUDE.md", claude, "Claude", criar=True)
        for nome in OUTROS_AGENTES:
            self.inserir_bloco(self.destino / nome, agentes, None, criar=False)

    def gitignore(self) -> None:
        arquivo = self.destino / ".gitignore"
        if not arquivo.is_file() and not (self.destino / ".git").exists():
            return
        bloco = (HARNESS / "instalacao" / "gitignore").read_text(encoding="utf-8")
        self.inserir_bloco(arquivo, bloco, None, criar=True)

    def workflow(self) -> None:
        if not self.ci:
            return
        alvo = self.destino / ".github" / "workflows" / "entregaveis.yml"
        texto = self.ajustar((HARNESS / "instalacao" / "entregaveis.yml").read_text(encoding="utf-8"))
        if alvo.is_file() and alvo.read_text(encoding="utf-8") == texto:
            return
        if alvo.is_file() and not self.atualizar:
            self.mantido.append(".github/workflows/entregaveis.yml já existe e é diferente. Mantido.")
            return
        self.gravar(alvo, texto)
        self.nota(".github/workflows/entregaveis.yml instalado")

    def registros(self) -> None:
        script = self.destino / self.pasta / "_harness" / "scripts" / "preparar.py"
        if self.simular or not script.is_file():
            return
        saida = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=60)
        criados = [l.strip() for l in saida.stdout.splitlines() if l.startswith("  ")]
        if criados:
            self.nota(f"{len(criados)} registros do projeto criados em {self.pasta}/_projeto, {self.pasta}/_intake, {self.pasta}/_dominio e {self.pasta}/_atas")

    def instalar(self) -> int:
        base = self.destino / self.pasta
        if base.exists() and not (base / "_harness").exists() and any(base.iterdir()):
            self.mantido.append(f"A pasta {self.pasta}/ já existia com arquivos do projeto. Eles não foram tocados: o harness só usa as subpastas que começam por '_' e as que têm briefing.md. Se preferir outra pasta, rode de novo com --pasta NOME.")
        self.copiar_harness()
        self.copiar_skills()
        self.mesclar_settings()
        self.blocos()
        self.gitignore()
        self.workflow()
        self.registros()

        print(("Simulação: nada foi gravado.\n" if self.simular else "") + f"Destino: {self.destino}")
        if self.feito:
            print("\nFeito:" if not self.simular else "\nSeria feito:")
            for linha in self.feito:
                print(f"  {linha}")
        else:
            print("\nNada a fazer: o harness já está instalado nesta versão.")
        try:
            import ambiente  # noqa: PLC0415

            falta = ambiente.faltas_em_uma_linha()
        except Exception:  # noqa: BLE001 - a instalação não falha por causa da conferência do ambiente
            falta = ""
        if falta:
            self.mantido.append(falta + f" Rode: python3 {self.pasta}/_harness/scripts/ambiente.py")
        if self.mantido:
            print("\nAtenção:")
            for linha in self.mantido:
                print(f"  {linha}")
        if not self.simular:
            print(
                "\nPróximo passo: abra o agente no projeto e diga do que é o projeto.\n"
                "Em projeto novo ele segue a skill iniciar-projeto. Em projeto que já estava\n"
                "em andamento, ele segue adotar-projeto: levanta o que existe, encaixa o\n"
                "harness e pergunta só o que os arquivos não respondem."
            )
        return 0


def main() -> int:
    analisador = argparse.ArgumentParser(description="Instala o harness de entregáveis em um projeto.")
    analisador.add_argument("--destino", default=".", help="raiz do projeto de destino")
    analisador.add_argument("--pasta", default=PADRAO, help="nome da pasta de entregáveis no destino")
    analisador.add_argument("--simular", action="store_true")
    analisador.add_argument("--atualizar", action="store_true")
    analisador.add_argument("--ci", action="store_true")
    args = analisador.parse_args()

    destino = Path(args.destino).resolve()
    if not destino.is_dir():
        print(f"A pasta de destino não existe: {destino}")
        return 2
    if destino == ORIGEM:
        print("O destino é a própria cópia do kit. Indique o projeto com --destino.")
        return 2
    if not re.fullmatch(r"[\w][\w.-]*", args.pasta):
        print("O nome da pasta usa letras, números, ponto, hífen e sublinhado.")
        return 2
    return Instalador(destino, args.pasta, args.simular, args.atualizar, args.ci).instalar()


if __name__ == "__main__":
    sys.exit(main())
