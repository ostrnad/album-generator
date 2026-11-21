#!/usr/bin/env python3
"""Synthetische Testpanoramen für <album-panorama> erzeugen (deterministisch, ohne Zufall und ohne Netz).

Jedes Panorama zeigt einen Quader (Raum) mit Gitterlinien, aufgenommen aus seiner Mitte und zylindrisch
projiziert, so wie ein Handy-Panorama (Gerät hochkant, seitwärts geschwenkt, SPEC.md 6.7):

    Spalte x  ->  Blickrichtung  phi = (x / Breite - 0,5) * Schwenkwinkel
    Zeile  y  ->  tan(Höhenwinkel) = (0,5 - y / Höhe) * 2 * tan(Bildwinkel / 2)

Im Panorama sind die waagerechten Gitterlinien gebogen. Entzerrt das Widget richtig, sind alle Linien gerade.
Jede Wand hat ihre eigene Farbe, damit man sieht, wohin man schaut.

Aufruf:  python erzeugen.py <ordner>   schreibt die Testfälle als JPEG in <ordner>
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

# Raum: halbe Breiten in x und z, Boden und Decke relativ zur Kamera, Abstand der Gitterlinien (alles in Metern)
RAUM_X, RAUM_Z, BODEN, DECKE, GITTER = 4.0, 3.0, -1.5, 1.5, 0.5
WAENDE = {  # Wand: (Grundfarbe, Linienfarbe)
    "vorn": ((214, 96, 77), (90, 30, 20)),     # z = +RAUM_Z, Blickrichtung 0°
    "rechts": ((86, 150, 214), (20, 50, 90)),  # x = +RAUM_X
    "hinten": ((112, 180, 98), (30, 70, 25)),  # z = -RAUM_Z
    "links": ((222, 186, 82), (95, 75, 15)),   # x = -RAUM_X
}
BODENFARBE, DECKENFARBE, KANTE = (96, 96, 96), (236, 236, 236), (20, 20, 20)

# Testfälle: Name, Schwenkwinkel in Grad, senkrechter Bildwinkel in Grad, Höhe in Pixeln, Beschreibung
FAELLE = [
    ("rund-360", 360, 54, 680, "Ganzer Kreis (360°), Bildwinkel 54° wie die iPhone-Hauptkamera"),
    ("halb-180", 180, 54, 900, "Halbkreis (180°), Bildwinkel 54°"),
    ("schmal-120", 120, 54, 1100, "Schmal (120°): Mindestzoom greift, Ausschnitt bleibt im Bild"),
    ("weit-70", 240, 70, 900, "240° mit größerem Bildwinkel (70°)"),
]


def wand(phi: float) -> tuple[str, float, float]:
    """Trifft der waagerechte Strahl in Richtung phi auf eine Wand: (Wand, Abstand, Position entlang der Wand)."""
    sx, cz = math.sin(phi), math.cos(phi)
    tx = RAUM_X / abs(sx) if abs(sx) > 1e-12 else math.inf
    tz = RAUM_Z / abs(cz) if abs(cz) > 1e-12 else math.inf
    if tz <= tx:
        return ("vorn" if cz > 0 else "hinten"), tz, tz * sx
    return ("rechts" if sx > 0 else "links"), tx, tx * cz


def panorama(schwenk_grad: float, bildwinkel_grad: float, hoehe: int) -> Image.Image:
    tanp = math.tan(math.radians(bildwinkel_grad) / 2)
    theta = math.radians(schwenk_grad)
    breite = round(hoehe * theta / (2 * tanp))
    im = Image.new("RGB", (breite, hoehe), DECKENFARBE)
    zeichnen = ImageDraw.Draw(im)

    def zeile(t: float) -> float:  # tan(Höhenwinkel) -> Zeile
        return (0.5 - t / (2 * tanp)) * hoehe

    def spalte_info(x: float):
        return wand((x / breite - 0.5) * theta)

    for x in range(breite):
        name, abstand, pos = spalte_info(x + 0.5)
        grund, linie = WAENDE[name]
        oben, unten = zeile(DECKE / abstand), zeile(BODEN / abstand)
        zeichnen.line([(x, oben), (x, unten)], fill=grund)
        zeichnen.line([(x, unten), (x, hoehe)], fill=BODENFARBE)
        # senkrechte Gitterlinie oder Raumecke zwischen dieser und der nächsten Spalte?
        name2, _, pos2 = spalte_info(x + 1.5)
        if name2 != name:
            zeichnen.rectangle([x, oben, x + 2, unten], fill=KANTE)
        elif math.floor(pos / GITTER) != math.floor(pos2 / GITTER):
            zeichnen.rectangle([x - 1, oben, x + 1, unten], fill=linie)
        # waagerechte Gitterlinien: Höhe auf der Wand = Abstand * tan(Höhenwinkel)
        k = math.ceil(BODEN / GITTER)
        while k * GITTER <= DECKE + 1e-9:
            y = zeile(k * GITTER / abstand)
            farbe = KANTE if abs(k * GITTER) < 1e-9 else linie  # Augenhöhe kräftig
            zeichnen.rectangle([x, y - 2, x, y + 2], fill=farbe)
            k += 1
        # Boden- und Deckenkante
        zeichnen.rectangle([x, oben - 1, x, oben + 1], fill=KANTE)
        zeichnen.rectangle([x, unten - 1, x, unten + 1], fill=KANTE)
    return im


def erzeugen(ordner: Path) -> list[dict]:
    """Schreibt alle Testfälle als JPEG nach ordner und gibt ihre Beschreibung zurück."""
    ordner.mkdir(parents=True, exist_ok=True)
    faelle = []
    for name, schwenk, bildwinkel, hoehe, text in FAELLE:
        datei = ordner / f"{name}.jpg"
        panorama(schwenk, bildwinkel, hoehe).save(datei, "JPEG", quality=90)
        faelle.append({"name": name, "datei": datei, "bildwinkel": bildwinkel, "beschreibung": text})
    return faelle


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    for f in erzeugen(Path(sys.argv[1])):
        print(f["datei"])
