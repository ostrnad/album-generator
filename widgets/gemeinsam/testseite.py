"""Gemeinsamer Rahmen für die Testseiten der Web Components (ARCHITEKTUR.md 7.1).

Eine Testseite zeigt alle Testfälle einer Component untereinander, jeweils
- in Handy- und Desktopbreite (feste Breite per <iframe>),
- ohne JavaScript (<iframe sandbox> ohne allow-scripts),
- hell oder dunkel (Umschalter oben; jede Fallseite gibt es fest hell und fest dunkel).

Jeder Fall ist eine eigene, vollständige Seite, die die Component so einbindet wie das Album: CSS und Schrift
aus fotoalbum.py, Daten im JSON-Block, Übergabeskript, Bilddaten in <script>-Blöcken. Die Fallseiten lassen sich
auch einzeln öffnen, z. B. am Handy.
"""
from __future__ import annotations

import html
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
import fotoalbum as fa  # noqa: E402

BREITEN = (("Handy", 390, 620), ("Desktop", 1200, 820))  # Name, Breite, Höhe des <iframe>


def css() -> str:
    """Das CSS des Albums samt Schrift und Dunkelmodus."""
    return (fa.CSS.replace("%%FONT400%%", fa.FONT_400).replace("%%FONT600%%", fa.FONT_600)
            .replace("%%DARK_AUTO%%", fa.dark_css(":root:not([data-theme=light])"))
            .replace("%%DARK_SET%%", fa.dark_css(":root[data-theme=dark]")))


def fallseite(titel: str, inhalt: str, widget_daten: dict, bloecke: list[str], komponenten: list[str],
              thema: str) -> str:
    """Eine vollständige Seite für einen Testfall; thema ist "light" oder "dark"."""
    return f"""<!DOCTYPE html>
<html lang="de" data-theme="{thema}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(titel)}</title>
<script>document.documentElement.classList.add("js")</script>
<style>{css()}</style>
</head>
<body>
<div class="seite"><div class="inhalt"><main class="raster">
{inhalt}
</main></div></div>
{chr(10).join(bloecke)}
{fa.widget_daten_json(widget_daten)}
<script>{fa.komponenten_js(komponenten)}{fa.UEBERGABE_JS}</script>
</body>
</html>
"""


INDEX_CSS = """
:root{--bg:#DCE3DD;--fg:#1F2A24;--muted:#4A584F;--rahmen:#B9C4BB;color-scheme:light}
@media (prefers-color-scheme:dark){:root{--bg:#161C18;--fg:#E6ECE7;--muted:#A9B5AC;--rahmen:#36413A;color-scheme:dark}}
*{box-sizing:border-box}
body{margin:0;padding:24px 16px 64px;background:var(--bg);color:var(--fg);font:16px/1.4 system-ui,sans-serif}
h1{font-size:24px;margin:0 0 4px}
h2{font-size:19px;margin:40px 0 4px}
p{margin:4px 0;color:var(--muted)}
a{color:inherit}
.leiste{position:sticky;top:0;z-index:1;background:var(--bg);padding:8px 0;display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.leiste button{font:inherit;min-height:44px;padding:0 16px;border-radius:999px;border:1px solid var(--muted);background:transparent;color:inherit;cursor:pointer}
.leiste button[aria-pressed=true]{background:var(--fg);color:var(--bg)}
.ansichten{display:flex;flex-direction:column;gap:20px;margin-top:12px}
.ansicht h3{font-size:14px;font-weight:600;margin:0 0 6px;color:var(--muted)}
.rahmen{overflow:auto;width:max-content;max-width:100%;border:1px solid var(--rahmen)}
iframe{display:block;border:0;background:#fff}
"""

INDEX_JS = """
(function(){
var knoepfe=document.querySelectorAll("[data-thema]");
function setze(t){
  [].forEach.call(document.querySelectorAll("iframe[data-basis]"),function(f){f.src=f.getAttribute("data-basis")+"-"+t+".html"});
  [].forEach.call(document.querySelectorAll("a[data-basis]"),function(a){a.href=a.getAttribute("data-basis")+"-"+t+".html"});
  [].forEach.call(knoepfe,function(k){k.setAttribute("aria-pressed",k.getAttribute("data-thema")===t?"true":"false")});
}
[].forEach.call(knoepfe,function(k){k.addEventListener("click",function(){setze(k.getAttribute("data-thema"))})});
})();
"""


def schreiben(ausgabe: Path, titel: str, einleitung: str, faelle: list[dict], komponenten: list[str],
              extra_links: str = "") -> Path:
    """Schreibt Fallseiten und Übersicht nach ausgabe.

    Ein Fall ist ein dict mit name, beschreibung, inhalt (HTML im Raster), widget_daten, bloecke.
    """
    ausgabe.mkdir(parents=True, exist_ok=True)
    abschnitte = []
    for f in faelle:
        for thema in ("light", "dark"):
            (ausgabe / f"{f['name']}-{thema}.html").write_text(
                fallseite(f"{titel}: {f['name']}", f["inhalt"], f["widget_daten"], f["bloecke"], komponenten, thema),
                encoding="utf-8")
        ansichten = []
        for name, breite, hoehe in BREITEN:
            ansichten.append(f'<div class="ansicht"><h3>{name} ({breite} px)</h3><div class="rahmen">'
                             f'<iframe loading="lazy" title="{name}" width="{breite}" height="{hoehe}" '
                             f'data-basis="{f["name"]}" src="{f["name"]}-light.html"></iframe></div></div>')
        breite, hoehe = BREITEN[1][1], BREITEN[1][2]
        ansichten.append(f'<div class="ansicht"><h3>Ohne JavaScript ({breite} px)</h3><div class="rahmen">'
                         f'<iframe loading="lazy" title="Ohne JavaScript" sandbox="allow-same-origin" width="{breite}" '
                         f'height="{hoehe}" data-basis="{f["name"]}" src="{f["name"]}-light.html"></iframe></div></div>')
        abschnitte.append(
            f'<section><h2>{html.escape(f["name"])}</h2><p>{html.escape(f["beschreibung"])} · '
            f'<a data-basis="{f["name"]}" href="{f["name"]}-light.html">einzeln öffnen</a></p>'
            f'<div class="ansichten">{"".join(ansichten)}</div></section>')
    index = ausgabe / "index.html"
    index.write_text(f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(titel)}</title>
<style>{INDEX_CSS}</style>
</head>
<body>
<h1>{html.escape(titel)}</h1>
<p>{einleitung}</p>
{extra_links}
<div class="leiste"><button type="button" data-thema="light" aria-pressed="true">Hell</button><button type="button" data-thema="dark" aria-pressed="false">Dunkel</button></div>
{"".join(abschnitte)}
<script>{INDEX_JS}</script>
</body>
</html>
""", encoding="utf-8")
    return index
