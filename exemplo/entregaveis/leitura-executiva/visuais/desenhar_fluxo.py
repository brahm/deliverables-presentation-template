"""Desenha o fluxo da página 5: o caminho do carrinho abandonado até o e-mail.

Uso: python3 desenhar_fluxo.py
Precisa do pacote Pillow. Grava carrinho.png ao lado deste arquivo. Os
tempos vêm da evidência E-004 do exemplo, que é inventada.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

LARGURA, ALTURA = 2000, 760
DESTAQUE, NEUTRA, TEXTO, FUNDO = "#0B5CAD", "#A9B3BD", "#1F2933", "#FFFFFF"

PASSOS = [
    ("O cliente abandona", "o carrinho no site", ""),
    ("O evento espera", "a carga noturna", "até 1 dia"),
    ("Um analista monta", "a lista à mão", "mais 1 dia"),
    ("O e-mail", "é enviado", "2 dias depois"),
]


def fonte(tamanho: int, negrito: bool = False) -> ImageFont.FreeTypeFont:
    nomes = ["Carlito-Bold.ttf", "DejaVuSans-Bold.ttf"] if negrito else ["Carlito-Regular.ttf", "DejaVuSans.ttf"]
    for nome in nomes:
        try:
            return ImageFont.truetype(nome, tamanho)
        except OSError:
            continue
    return ImageFont.load_default()


def main() -> None:
    imagem = Image.new("RGB", (LARGURA, ALTURA), FUNDO)
    desenho = ImageDraw.Draw(imagem)
    margem, vao = 40, 110
    largura = (LARGURA - 2 * margem - vao * (len(PASSOS) - 1)) // len(PASSOS)
    topo, base = 250, 560
    for i, (linha1, linha2, tempo) in enumerate(PASSOS):
        x = margem + i * (largura + vao)
        ultimo = i == len(PASSOS) - 1
        cor = DESTAQUE if ultimo else NEUTRA
        desenho.rounded_rectangle([x, topo, x + largura, base], radius=28, fill=cor)
        cor_do_texto = "#FFFFFF" if ultimo else TEXTO
        for n, linha in enumerate((linha1, linha2)):
            desenho.text((x + largura / 2, topo + 122 + n * 62), linha, font=fonte(42), fill=cor_do_texto, anchor="mm")
        desenho.text((x + largura / 2, topo - 150), str(i + 1), font=fonte(64, True), fill=cor, anchor="mm")
        if tempo:
            desenho.text((x + largura / 2, base + 80), tempo, font=fonte(56, True), fill=DESTAQUE if ultimo else TEXTO, anchor="mm")
        if not ultimo:
            meio = (topo + base) // 2
            inicio, fim = x + largura + 18, x + largura + vao - 18
            desenho.line([inicio, meio, fim - 26, meio], fill=TEXTO, width=8)
            desenho.polygon([(fim, meio), (fim - 34, meio - 24), (fim - 34, meio + 24)], fill=TEXTO)
    imagem.save(Path(__file__).with_name("carrinho.png"), optimize=True)


if __name__ == "__main__":
    main()
