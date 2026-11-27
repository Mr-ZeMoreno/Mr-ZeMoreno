"""Convierte una imagen en arte ASCII a color (data/portrait.json).

Solo hay que ejecutarlo cuando cambie la foto (requiere Pillow):
    python scripts/portrait.py ruta/a/foto.png
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter

COLS, ROWS = 78, 47
RAMP = " .:-=+*#%@"


def main(source):
    img = Image.open(source).convert("RGB")
    img = ImageEnhance.Contrast(img).enhance(1.15)
    # realce local: recupera los bordes de la figura sobre el fondo
    img = img.filter(ImageFilter.UnsharpMask(radius=9, percent=220, threshold=0))
    img = img.resize((COLS, ROWS), Image.LANCZOS)
    rows = []
    for y in range(ROWS):
        runs = []  # [color, texto] agrupando caracteres del mismo color
        for x in range(COLS):
            r, g, b = img.getpixel((x, y))
            lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            # los rojos pesan poco en luminancia: se refuerzan
            level = max(lum, r / 255 * 0.75)
            char = RAMP[min(int(level ** 1.05 * len(RAMP)), len(RAMP) - 1)]
            if max(g, b) > r:  # sin azules: los tonos fríos pasan a gris
                r = g = b = int(lum * 255)
            peak = max(r, g, b, 1)
            gain = min(255 / peak, 1.7)
            color = "#" + "".join(
                f"{min(int(c * gain) // 24 * 24 + 12, 255):02x}" for c in (r, g, b)
            )
            if runs and (runs[-1][0] == color or char == " "):
                runs[-1][1] += char
            else:
                runs.append([color, char])
        rows.append(runs)
    out = Path(__file__).resolve().parent.parent / "data" / "portrait.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(rows, separators=(",", ":")), encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1])
