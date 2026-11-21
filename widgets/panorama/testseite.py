#!/usr/bin/env python3
"""Testseite für <album-panorama> erzeugen (ARCHITEKTUR.md 7.1).

Aufruf:  python widgets/panorama/testseite.py <ausgabeordner>

Erzeugt die synthetischen Testpanoramen (testdaten/erzeugen.py), verarbeitet sie wie der Bau des Albums und
schreibt die Testseite samt Fallseiten nach <ausgabeordner>. Zusätzlich entsteht ein kleines Beispielalbum, das
mit `fotoalbum.py build` gebaut wird und die Panoramen zwischen gewöhnlichen Fotos zeigt.

Prüfen: Die Gitterlinien müssen im Widget gerade sein, auch beim Schwenken, Neigen und Zoomen.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER.parent / "gemeinsam"))
sys.path.insert(0, str(HIER / "testdaten"))
import testseite as ts  # noqa: E402
import erzeugen  # noqa: E402

fa = ts.fa


def faelle(ordner: Path) -> list[dict]:
    ergebnis = []
    for f in erzeugen.erzeugen(ordner):
        b = fa.bild_verarbeiten(f["datei"], dict(fa.DEFAULTS), pano=True)
        unterschrift = f["beschreibung"]
        ergebnis.append({
            "name": f["name"],
            "beschreibung": f"{f['beschreibung']} – Panorama {b['w']} × {b['h']} px",
            "inhalt": fa.panorama_figur("panorama-1", b["vorschau"], b["vw"], b["vh"], unterschrift, unterschrift),
            "widget_daten": {"panorama-1": {"version": 1, "bild": "pano-1", "breite": b["w"], "hoehe": b["h"],
                                            "bildwinkel": float(f["bildwinkel"])}},
            "bloecke": [fa.eingebettet("pano-1", b["pano"])],
        })
    return ergebnis


def beispielalbum(ordner: Path, ausgabe: Path) -> None:
    """Kleines Album aus zwei Panoramen und vier einfarbigen Fotos, gebaut mit fotoalbum.py."""
    from PIL import Image, ImageDraw
    farben = [((214, 96, 77), (1200, 900)), ((86, 150, 214), (900, 1200)), ((112, 180, 98), (1000, 1000)),
              ((222, 186, 82), (1200, 800))]
    zeilen = ['titel = "Beispielalbum Panorama"', 'untertitel = "Synthetische Testdaten"', ""]
    for i, (farbe, groesse) in enumerate(farben, 1):
        im = Image.new("RGB", groesse, farbe)
        ImageDraw.Draw(im).text((40, 40), f"Foto {i}", fill=(255, 255, 255))
        im.save(ordner / f"foto-{i}.jpg", "JPEG", quality=85)
    reihenfolge = ["foto-1.jpg", "rund-360.jpg", "foto-2.jpg", "foto-3.jpg", "schmal-120.jpg", "foto-4.jpg"]
    for datei in reihenfolge:
        zeilen += ["[[bild]]", f'datei = "{datei}"', f'unterschrift = "{datei}"']
        if not datei.startswith("foto"):
            zeilen.append("panorama = true")
        zeilen.append("")
    (ordner / "album.toml").write_text("\n".join(zeilen), encoding="utf-8")
    subprocess.run([sys.executable, str(fa.__file__), "build", str(ordner), "-o", str(ausgabe)], check=True)


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    ausgabe = Path(sys.argv[1])
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        alle = faelle(tmp)
        ausgabe.mkdir(parents=True, exist_ok=True)
        beispielalbum(tmp, ausgabe / "beispielalbum.html")
    index = ts.schreiben(
        ausgabe, "Testseite: Panorama",
        "Synthetische Zylinder-Panoramen eines Raums mit Gitterlinien. Im Widget müssen alle Linien gerade sein; "
        "ohne JavaScript erscheint der flache Streifen.",
        alle, ["panorama"],
        extra_links='<p><a href="beispielalbum.html">Beispielalbum</a> (mit fotoalbum.py gebaut)</p>')
    print(f"Testseite: {index}")


if __name__ == "__main__":
    main()
