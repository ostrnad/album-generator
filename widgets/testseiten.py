#!/usr/bin/env python3
"""Alle Testseiten der Web Components erzeugen (ARCHITEKTUR.md 7).

Aufruf:  python widgets/testseiten.py <ausgabeordner> [--branch NAME]

Ruft für jedes Verzeichnis widgets/<name>/ mit einer testseite.py diese auf (Ausgabe nach
<ausgabeordner>/<name>/) und schreibt eine Übersicht <ausgabeordner>/index.html.
"""
from __future__ import annotations

import argparse
import html
import subprocess
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent


def main() -> None:
    ap = argparse.ArgumentParser(description="Testseiten aller Web Components erzeugen.")
    ap.add_argument("ausgabe", help="Ausgabeordner")
    ap.add_argument("--branch", default="", help="Name des Branches für die Überschrift")
    args = ap.parse_args()
    ausgabe = Path(args.ausgabe)
    ausgabe.mkdir(parents=True, exist_ok=True)
    namen = sorted(d.name for d in HIER.iterdir() if (d / "testseite.py").is_file())
    for name in namen:
        print(f"── {name}")
        subprocess.run([sys.executable, str(HIER / name / "testseite.py"), str(ausgabe / name)], check=True)
    titel = "Testseiten" + (f" – {args.branch}" if args.branch else "")
    eintraege = "".join(f'<li><a href="{n}/">{html.escape(n)}</a></li>' for n in namen)
    (ausgabe / "index.html").write_text(f"""<!DOCTYPE html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(titel)}</title>
<style>body{{margin:0;padding:24px 16px;font:16px/1.5 system-ui,sans-serif;background:#DCE3DD;color:#1F2A24}}
@media (prefers-color-scheme:dark){{body{{background:#161C18;color:#E6ECE7}}}}a{{color:inherit}}</style></head>
<body><h1>{html.escape(titel)}</h1><ul>{eintraege}</ul><p><a href="../">Alle Branches</a></p></body></html>
""", encoding="utf-8")
    print(f"Übersicht: {ausgabe / 'index.html'}")


if __name__ == "__main__":
    main()
