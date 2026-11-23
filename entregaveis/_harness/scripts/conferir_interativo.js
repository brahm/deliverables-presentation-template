#!/usr/bin/env node
/*
 * Abre um HTML interativo em um navegador sem interface e confere o que só aparece renderizado.
 *
 *   node entregaveis/_harness/scripts/conferir_interativo.js ARQUIVO.html [--saida PASTA]
 *
 * Confere, no computador e no celular, no tema claro e no escuro:
 *   - erro de script e erro no console;
 *   - pedido de qualquer recurso fora do arquivo (todos são bloqueados e listados);
 *   - rolagem horizontal da página;
 *   - página vazia ao abrir.
 * Grava uma imagem de cada combinação, mais uma com movimento reduzido e uma da versão de impressão.
 *
 * É opcional: precisa de Node e do pacote playwright com um Chromium instalado.
 * Sem eles, a conferência é feita abrindo o arquivo em um navegador.
 * Sai com 0 quando nada foi encontrado, 1 quando há achados e 2 quando não conseguiu rodar.
 */
"use strict";
const fs = require("fs");
const path = require("path");
const url = require("url");

const argumentos = process.argv.slice(2);
const arquivo = argumentos.find((a) => !a.startsWith("--"));
const iSaida = argumentos.indexOf("--saida");
if (!arquivo || !fs.existsSync(arquivo)) {
  console.error("Uso: node conferir_interativo.js ARQUIVO.html [--saida PASTA]");
  process.exit(2);
}
let playwright;
try {
  playwright = require("playwright");
} catch (erro) {
  console.error("O pacote playwright não está instalado. Abra o arquivo em um navegador e confira à mão.");
  process.exit(2);
}
const absoluto = path.resolve(arquivo);
const nome = path.basename(absoluto, ".html");
const saida = path.resolve(iSaida >= 0 ? argumentos[iSaida + 1] : path.join(path.dirname(absoluto), "..", "saida", "conferencia"));
fs.mkdirSync(saida, { recursive: true });
const endereco = url.pathToFileURL(absoluto).href;

const TELAS = [
  { rotulo: "computador", viewport: { width: 1280, height: 720 } },
  { rotulo: "celular", viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true },
];
const TEMAS = ["light", "dark"];

async function abrir(navegador, tela, tema, opcoes, achados, onde) {
  const contexto = await navegador.newContext({
    viewport: tela.viewport,
    isMobile: Boolean(tela.isMobile),
    hasTouch: Boolean(tela.hasTouch),
    colorScheme: tema,
    reducedMotion: opcoes.semMovimento ? "reduce" : "no-preference",
  });
  // Nada sai do arquivo: todo pedido que não é o próprio arquivo é bloqueado e anotado.
  await contexto.route("**/*", (rota) => {
    const pedido = rota.request().url();
    if (pedido === endereco || pedido.startsWith("data:") || pedido.startsWith("blob:")) { return rota.continue(); }
    achados.push(`${onde}: pediu um recurso fora do arquivo (${pedido})`);
    return rota.abort();
  });
  const pagina = await contexto.newPage();
  pagina.on("pageerror", (erro) => achados.push(`${onde}: erro de script (${erro.message})`));
  pagina.on("console", (mensagem) => {
    if (mensagem.type() === "error" && !/net::ERR_FAILED|ERR_BLOCKED/.test(mensagem.text())) {
      achados.push(`${onde}: erro no console (${mensagem.text()})`);
    }
  });
  await pagina.goto(endereco);
  await pagina.waitForTimeout(700);
  return { contexto, pagina };
}

(async () => {
  const achados = [];
  let navegador;
  try {
    navegador = await playwright.chromium.launch();
  } catch (erro) {
    console.error("Não foi possível abrir o Chromium: " + erro.message.split("\n")[0]);
    process.exit(2);
  }
  for (const tela of TELAS) {
    for (const tema of TEMAS) {
      const onde = `${tela.rotulo}, tema ${tema === "light" ? "claro" : "escuro"}`;
      const { contexto, pagina } = await abrir(navegador, tela, tema, {}, achados, onde);
      const medida = await pagina.evaluate(() => ({
        largura: document.documentElement.scrollWidth,
        janela: window.innerWidth,
        texto: document.body.innerText.trim().length,
      }));
      if (medida.largura > medida.janela + 1) {
        achados.push(`${onde}: a página rola para o lado (${medida.largura} px de conteúdo em ${medida.janela} px de tela)`);
      }
      if (medida.texto < 40) { achados.push(`${onde}: a página abre quase vazia`); }
      await pagina.screenshot({ path: path.join(saida, `${nome}-${tela.rotulo}-${tema === "light" ? "claro" : "escuro"}.png`), fullPage: true });
      await contexto.close();
    }
  }
  {
    const onde = "movimento reduzido";
    const { contexto, pagina } = await abrir(navegador, TELAS[0], "light", { semMovimento: true }, achados, onde);
    const correndo = await pagina.evaluate(() => document.getAnimations().filter((a) => a.playState === "running").length);
    if (correndo > 0) { achados.push(`${onde}: ${correndo} animação(ões) continuam rodando`); }
    await pagina.screenshot({ path: path.join(saida, `${nome}-sem-movimento.png`), fullPage: true });
    await contexto.close();
  }
  {
    const onde = "impressão";
    const { contexto, pagina } = await abrir(navegador, TELAS[0], "light", {}, achados, onde);
    await pagina.emulateMedia({ media: "print" });
    await pagina.screenshot({ path: path.join(saida, `${nome}-impressao.png`), fullPage: true });
    await contexto.close();
  }
  await navegador.close();
  if (achados.length) {
    console.log(`${nome}: ${achados.length} achado(s)`);
    for (const a of [...new Set(achados)]) { console.log("  - " + a); }
  } else {
    console.log(`${nome}: nada encontrado. Imagens em ${saida}`);
  }
  process.exit(achados.length ? 1 : 0);
})().catch((erro) => {
  console.error("A conferência falhou: " + erro.message);
  process.exit(2);
});
