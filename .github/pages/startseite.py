#!/usr/bin/env python3
"""Startseite von gh-pages: listet die Ordner aller Branches mit Testseiten (ARCHITEKTUR.md 7.2).

Aufruf:  python startseite.py <gh-pages-Verzeichnis>
"""
import html
import sys
from pathlib import Path

wurzel = Path(sys.argv[1])
ordner = sorted(d.name for d in wurzel.iterdir() if d.is_dir() and not d.name.startswith(".")
                and (d / "index.html").is_file())
eintraege = "".join(f'<li><a href="{html.escape(n, quote=True)}/">{html.escape(n)}</a></li>' for n in ordner)
(wurzel / "index.html").write_text(f"""<!DOCTYPE html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Testseiten – album-generator</title>
<style>body{{margin:0;padding:24px 16px;font:16px/1.5 system-ui,sans-serif;background:#DCE3DD;color:#1F2A24}}
@media (prefers-color-scheme:dark){{body{{background:#161C18;color:#E6ECE7}}}}a{{color:inherit}}</style></head>
<body><h1>Testseiten</h1><p>Je Branch die Testseiten der Web Components (synthetische Testdaten).</p>
<ul>{eintraege or "<li>noch keine</li>"}</ul></body></html>
""", encoding="utf-8")
