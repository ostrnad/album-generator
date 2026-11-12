#!/usr/bin/env python3
"""
fotoalbum.py – erzeugt aus einem Ordner mit Fotos ein Album als eine einzige HTML-Datei.

Schritt 1:  python fotoalbum.py init  <Bilderordner>
            -> schreibt <Bilderordner>/album.toml (Liste aller Bilder, zum Bearbeiten)

Schritt 2:  python fotoalbum.py build <Bilderordner>/album.toml
            -> schreibt die HTML-Datei (alles eingebettet, keine Zusatzdateien)

Voraussetzungen:  Python 3.11+,  pip install pillow pillow-heif
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import html
import io
import math
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    try:
        import tomli as tomllib  # type: ignore
    except ModuleNotFoundError:
        sys.exit("Python 3.11 oder neuer wird benötigt (oder: pip install tomli).")

try:
    from PIL import Image, ImageOps
except ModuleNotFoundError:
    sys.exit("Pillow fehlt. Bitte installieren:  pip install pillow pillow-heif")

HEIF_OK = True
try:
    from pillow_heif import register_heif_opener

    register_heif_opener()
except ModuleNotFoundError:
    HEIF_OK = False

VERSION = "1.3.1-poc"
CONFIG_NAME = "album.toml"
JPEG_EXT = {".jpg", ".jpeg"}
HEIC_EXT = {".heic", ".heif"}
MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli",
          "August", "September", "Oktober", "November", "Dezember"]
DEFAULTS = {
    "vorschau_klein": 480,     # lange Kante in Pixeln, für das Raster
    "vorschau_gross": 1280,    # lange Kante, für hochauflösende Displays und als Sofortbild in der Großansicht
    "vollbild": 4000,          # lange Kante des großen Bildes (Großansicht und Speichern)
    "qualitaet_vorschau": 80,  # JPEG-Qualität der Vorschaubilder
    "qualitaet_vollbild": 88,  # JPEG-Qualität des großen Bildes
    "bilddatum_anzeigen": True,
    "panorama_breite": 8192,       # maximale Breite eines Panoramas in Pixeln
    "panorama_bildwinkel": 54.0,   # angenommener senkrechter Bildwinkel eines Panoramas in Grad
}
PANO_BESCHNITT = 0.77  # Anteil der Sensorhöhe, der im fertigen Panorama übrig bleibt (Schätzung, ergibt 54° bei 26 mm)
PANORAMA_AB = 2.2  # init: Bilder, die mindestens so viel breiter als hoch sind, werden als Panorama vorgeschlagen
KARTE_DEFAULTS = {
    "anzeigen": True,
    "art": "route",            # "route" = Wegpunkte mit Linie verbunden, "punkte" = einzelne Wegpunkte
    "zoom": 0,                 # 0 = automatisch, sonst feste Zoomstufe 2–18
    "kacheln": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    "quelle": "© OpenStreetMap-Mitwirkende",
}
KARTE_W, KARTE_H = 1500, 1000  # Größe des eingebetteten Kartenbildes in Pixeln
WEGPUNKT_RADIUS_KM = 1.0       # init: aufeinanderfolgende Fotos in diesem Umkreis werden ein Wegpunkt


# ───────────────────────────── Hilfsfunktionen ─────────────────────────────

def fehler(msg: str) -> "None":
    sys.exit(f"Fehler: {msg}")


def exif_lesen(pfad: Path) -> tuple[str, dt.date | None, tuple[float, float] | None]:
    """Aufnahmezeit (sortierbarer Text), Aufnahmedatum und GPS-Position aus den EXIF-Daten, soweit vorhanden."""
    zeit, datum, gps = "", None, None
    try:
        with Image.open(pfad) as im:
            exif = im.getexif()
            sub = exif.get_ifd(0x8769)
            zeit = str(sub.get(36867) or sub.get(36868) or exif.get(306) or "")
            try:
                datum = dt.datetime.strptime(zeit[:10], "%Y:%m:%d").date()
            except ValueError:
                zeit = ""
            g = exif.get_ifd(0x8825)
            if g.get(2) and g.get(4):
                def grad(wert, ref, negativ):
                    d, m, sek = (float(x) for x in wert)
                    v = d + m / 60 + sek / 3600
                    return -v if str(ref).upper().startswith(negativ) else v
                lat, lon = grad(g[2], g.get(1, "N"), "S"), grad(g[4], g.get(3, "E"), "W")
                if -90 <= lat <= 90 and -180 <= lon <= 180 and (lat, lon) != (0.0, 0.0):
                    gps = (lat, lon)
    except Exception:
        pass
    return zeit, datum, gps


def ist_panorama(pfad: Path) -> bool:
    try:
        with Image.open(pfad) as im:
            return im.size[0] >= PANORAMA_AB * im.size[1]
    except Exception:
        return False


def pano_bildwinkel_exif(pfad: Path) -> tuple[float, float] | None:
    """Senkrechter Bildwinkel eines Panoramas, geschätzt aus der Kleinbild-Brennweite in den EXIF-Daten.

    Annahmen: Das Handy wurde hochkant geschwenkt (die lange Sensorseite steht senkrecht, 4:3-Sensor) und die
    Panorama-Funktion beschneidet das Bild oben und unten (Faktor PANO_BESCHNITT, eine Schätzung).
    Rückgabe: (Bildwinkel in Grad, Brennweite in mm) oder None, wenn die Angabe fehlt.
    """
    try:
        with Image.open(pfad) as im:
            f35 = float(im.getexif().get_ifd(0x8769).get(41989) or 0)
    except Exception:
        return None
    if not f35 > 0:
        return None
    halbe_lange_seite = 43.27 / 2 * 0.8  # Kleinbild-Diagonale 43,27 mm, lange Seite eines 4:3-Bildes = 0,8 × Diagonale
    winkel = 2 * math.degrees(math.atan(PANO_BESCHNITT * halbe_lange_seite / f35))
    return (round(winkel, 1), f35) if 10 <= winkel <= 150 else None


def entfernung_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


def toml_str(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def als_datum(wert, wo: str) -> dt.date | None:
    if wert in (None, ""):
        return None
    if isinstance(wert, dt.datetime):
        return wert.date()
    if isinstance(wert, dt.date):
        return wert
    if isinstance(wert, str):
        for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
            try:
                return dt.datetime.strptime(wert.strip(), fmt).date()
            except ValueError:
                pass
    fehler(f"Datum bei {wo} nicht lesbar: {wert!r}  (erwartet: 2026-07-12 oder 12.07.2026)")


def datum_text(d: dt.date) -> str:
    return f"{d.day}. {MONATE[d.month - 1]} {d.year}"


def zeitraum_text(von: dt.date, bis: dt.date) -> str:
    if von > bis:
        von, bis = bis, von
    if von == bis:
        return datum_text(von)
    if (von.year, von.month) == (bis.year, bis.month):
        return f"{von.day}. – {datum_text(bis)}"
    if von.year == bis.year:
        return f"{von.day}. {MONATE[von.month - 1]} – {datum_text(bis)}"
    return f"{datum_text(von)} – {datum_text(bis)}"


def mb(n: int) -> str:
    return f"{n / 1_000_000:.1f} MB"


# ───────────────────────────── Schritt 1: init ─────────────────────────────

def cmd_init(args) -> None:
    ordner = Path(args.ordner).expanduser()
    if not ordner.is_dir():
        fehler(f"Ordner nicht gefunden: {ordner}")
    ziel = ordner / CONFIG_NAME
    if ziel.exists() and not args.force:
        fehler(f"{ziel} gibt es schon. Mit --force überschreiben (deine Einträge gehen dann verloren).")

    dateien = [p for p in ordner.iterdir()
               if p.is_file() and not p.name.startswith(".") and p.suffix.lower() in JPEG_EXT | HEIC_EXT]
    if not dateien:
        fehler(f"Keine JPEG- oder HEIC-Bilder in {ordner} gefunden.")
    if not HEIF_OK and any(p.suffix.lower() in HEIC_EXT for p in dateien):
        print("Hinweis: HEIC-Bilder gefunden, aber pillow-heif fehlt (pip install pillow-heif).\n"
              "         Ohne das Paket fehlen die Aufnahmedaten und 'build' schlägt fehl.", file=sys.stderr)

    infos = [(p, *exif_lesen(p)) for p in dateien]
    # Reihenfolge: nach Aufnahmezeit, Bilder ohne Zeit ans Ende, jeweils nach Dateiname
    infos.sort(key=lambda t: (t[1] == "", t[1], t[0].name.lower()))
    daten = sorted(d for _, _, d, _ in infos if d)

    # Wegpunkte aus den GPS-Daten: aufeinanderfolgende Fotos am selben Ort werden zusammengefasst
    gruppen: list[dict] = []
    for p, _, d, gps in infos:
        if not gps:
            continue
        if gruppen and entfernung_km(gruppen[-1]["start"], gps) <= WEGPUNKT_RADIUS_KM:
            gruppen[-1]["punkte"].append(gps)
            gruppen[-1]["namen"].append(p.name)
        else:
            gruppen.append({"start": gps, "punkte": [gps], "namen": [p.name], "datum": d})

    z = []
    z.append("# Fotoalbum – Konfiguration. Bearbeiten, dann:  python fotoalbum.py build " + CONFIG_NAME)
    z.append("")
    z.append(f"titel = {toml_str(ordner.resolve().name)}")
    z.append('untertitel = ""              # optional, leer lassen = keine Unterzeile; Zeilenumbruch mit \\n')
    z.append("")
    z.append("# Datum (optional): entweder ein einzelnes Datum ODER ein Zeitraum. Nicht Gewünschtes löschen")
    z.append("# oder mit # auskommentieren. Format: 2026-07-12")
    if daten and daten[0] != daten[-1]:
        z.append(f"# datum = {daten[0].isoformat()}")
        z.append(f"datum_von = {daten[0].isoformat()}")
        z.append(f"datum_bis = {daten[-1].isoformat()}")
    elif daten:
        z.append(f"datum = {daten[0].isoformat()}")
        z.append(f"# datum_von = {daten[0].isoformat()}")
        z.append(f"# datum_bis = {daten[0].isoformat()}")
    else:
        z.append("# datum = 2026-07-12")
        z.append("# datum_von = 2026-07-12")
        z.append("# datum_bis = 2026-07-26")
    z.append("")
    z.append('ausgabe = "album.html"       # Name der erzeugten HTML-Datei (relativ zu dieser Datei)')
    z.append("")
    z.append("[einstellungen]")
    z.append(f"vorschau_klein = {DEFAULTS['vorschau_klein']}         # lange Kante in Pixeln: Bilder im Raster")
    z.append(f"vorschau_gross = {DEFAULTS['vorschau_gross']}        # lange Kante: scharfe Displays und Sofortbild der Großansicht")
    z.append(f"vollbild = {DEFAULTS['vollbild']}              # lange Kante des großen Bildes (Großansicht, Speichern)")
    z.append(f"qualitaet_vorschau = {DEFAULTS['qualitaet_vorschau']}      # JPEG-Qualität 1–95")
    z.append(f"qualitaet_vollbild = {DEFAULTS['qualitaet_vollbild']}")
    z.append("bilddatum_anzeigen = true    # Datum des einzelnen Bildes in der Großansicht zeigen")
    z.append(f"panorama_breite = {DEFAULTS['panorama_breite']}       # maximale Breite eines Panoramas in Pixeln")
    z.append(f"panorama_bildwinkel = {DEFAULTS['panorama_bildwinkel']}   # senkrechter Bildwinkel der Panoramen in Grad (iPhone-Hauptkamera: ca. 54)")
    z.append("")
    z.append("# Ein Block pro Bild. Die Reihenfolge hier ist die Reihenfolge im Album.")
    z.append("# Bild weglassen: Block löschen. 'unterschrift' und 'datum' sind optional.")
    for p, _, d, _ in infos:
        z.append("")
        z.append("[[bild]]")
        z.append(f"datei = {toml_str(p.name)}")
        z.append('unterschrift = ""')
        if d:
            z.append(f"datum = {d.isoformat()}")
        if ist_panorama(p):
            z.append("panorama = true              # als schwenkbares, entzerrtes Panorama über die volle Breite zeigen")
            bw = pano_bildwinkel_exif(p)
            if bw:
                z.append(f"# Bildwinkel laut EXIF (Brennweite {bw[1]:g} mm Kleinbild): ca. {bw[0]:g} Grad. Nur bei Bedarf überschreiben:")
            else:
                z.append(f"# Keine Brennweite in den EXIF-Daten; es gilt panorama_bildwinkel aus [einstellungen]. Bei Bedarf überschreiben:")
            z.append(f"# panorama_bildwinkel = {bw[0] if bw else DEFAULTS['panorama_bildwinkel']:g}")
    z.append("")
    z.append("# ── Karte (optional) ──")
    z.append("# Die Karte erscheint, sobald es mindestens einen [[wegpunkt]] gibt und 'anzeigen = true' ist.")
    z.append("# Das Kartenbild wird beim 'build' einmalig aus dem Internet geladen und in die HTML-Datei eingebettet.")
    z.append("[karte]")
    z.append("anzeigen = true")
    z.append('art = "route"                # "route" = Wegpunkte in dieser Reihenfolge verbunden, "punkte" = einzelne Wegpunkte')
    z.append("zoom = 0                     # 0 = automatisch; sonst feste Zoomstufe 2 (Welt) bis 18 (Straße)")
    z.append("")
    z.append("# Ein Block pro Wegpunkt: 'lat'/'lon' sind Pflicht, 'datum' und 'text' optional.")
    if gruppen:
        z.append(f"# Vorbelegt aus den GPS-Daten der Fotos (Fotos im Umkreis von {WEGPUNKT_RADIUS_KM:g} km zusammengefasst).")
        for g in gruppen:
            lat = sum(q[0] for q in g["punkte"]) / len(g["punkte"])
            lon = sum(q[1] for q in g["punkte"]) / len(g["punkte"])
            n = len(g["namen"])
            herkunft = g["namen"][0] if n == 1 else f'{n} Fotos, {g["namen"][0]} bis {g["namen"][-1]}'
            z.append("")
            z.append(f"[[wegpunkt]]                 # aus: {herkunft}")
            z.append('text = ""')
            if g["datum"]:
                z.append(f"datum = {g['datum'].isoformat()}")
            z.append(f"lat = {lat:.5f}")
            z.append(f"lon = {lon:.5f}")
    else:
        z.append("# Die Fotos enthalten keine GPS-Daten; Beispiel zum Ausfüllen (Koordinaten z. B. aus einer Karten-App):")
        z.append("")
        z.append("# [[wegpunkt]]")
        z.append('# text = "Wyk auf Föhr"')
        z.append("# datum = 2026-07-12")
        z.append("# lat = 54.69260")
        z.append("# lon = 8.56730")
    ziel.write_text("\n".join(z) + "\n", encoding="utf-8")

    print(f"{len(infos)} Bilder gefunden, Konfiguration geschrieben: {ziel}")
    if gruppen:
        print(f"{len(gruppen)} Wegpunkt(e) aus den GPS-Daten der Fotos vorbelegt.")
    if len(infos) > 60:
        print(f"Hinweis: Das Album ist auf etwa 30–40 Bilder ausgelegt. Mit {len(infos)} Bildern wird die HTML-Datei sehr groß.")
    print(f"Nächster Schritt: Datei bearbeiten, dann  python {Path(sys.argv[0]).name} build {ziel}")


# ───────────────────────────── Schritt 2: build ─────────────────────────────

def jpeg_bytes(im: Image.Image, kante: int, qualitaet: int, icc) -> tuple[bytes, int, int]:
    bild = im
    if max(im.size) > kante:
        bild = im.copy()
        bild.thumbnail((kante, kante), Image.LANCZOS)
    buf = io.BytesIO()
    extra = {"icc_profile": icc} if icc else {}
    bild.save(buf, "JPEG", quality=qualitaet, optimize=True, progressive=True, **extra)
    return buf.getvalue(), bild.size[0], bild.size[1]


def bild_verarbeiten(pfad: Path, cfg: dict, pano: bool = False) -> dict:
    """Erzeugt die drei Größen. EXIF-Daten (auch GPS) werden dabei nicht übernommen."""
    with Image.open(pfad) as roh:
        icc = roh.info.get("icc_profile")
        im = ImageOps.exif_transpose(roh)  # Drehung laut EXIF anwenden
        if im.mode != "RGB":
            im = im.convert("RGB")
        if pano:
            if im.size[0] > cfg["panorama_breite"]:
                im = im.resize((cfg["panorama_breite"], round(im.size[1] * cfg["panorama_breite"] / im.size[0])), Image.LANCZOS)
            buf = io.BytesIO()
            im.save(buf, "JPEG", quality=cfg["qualitaet_vollbild"], optimize=True, progressive=True,
                    **({"icc_profile": icc} if icc else {}))
            return {"w": im.size[0], "h": im.size[1], "pano": base64.b64encode(buf.getvalue()).decode("ascii")}
        voll, w, h = jpeg_bytes(im, cfg["vollbild"], cfg["qualitaet_vollbild"], icc)
        gross, gw, _ = jpeg_bytes(im, cfg["vorschau_gross"], cfg["qualitaet_vorschau"], icc)
        klein, kw, _ = jpeg_bytes(im, cfg["vorschau_klein"], cfg["qualitaet_vorschau"], icc)
    b64 = lambda b: base64.b64encode(b).decode("ascii")
    return {"w": w, "h": h, "kw": kw, "gw": gw, "klein": b64(klein), "gross": b64(gross), "voll": b64(voll)}


def kachel_laden(url: str) -> bytes:
    """Lädt eine Kartenkachel; einmal geladene Kacheln bleiben im Zwischenspeicher (~/.cache/fotoalbum)."""
    import hashlib
    cache = Path.home() / ".cache" / "fotoalbum" / "kacheln"
    datei = cache / (hashlib.sha1(url.encode()).hexdigest() + ".png")
    if datei.is_file():
        return datei.read_bytes()
    anfrage = urllib.request.Request(url, headers={"User-Agent": f"fotoalbum.py/{VERSION} (privates Fotoalbum-Werkzeug)"})
    with urllib.request.urlopen(anfrage, timeout=20) as antwort:
        daten = antwort.read()
    try:
        cache.mkdir(parents=True, exist_ok=True)
        datei.write_bytes(daten)
    except OSError:
        pass
    return daten


def karte_rendern(punkte: list[tuple[float, float]], kcfg: dict) -> tuple[str, list[tuple[float, float]]]:
    """Baut ein Kartenbild um die Wegpunkte. Rückgabe: JPEG (Base64) und Pixelposition jedes Wegpunkts im Bild."""
    def proj(lat: float, lon: float, z: int) -> tuple[float, float]:  # Web-Mercator in Pixeln
        n = 256 * 2 ** z
        lat = max(-85.0, min(85.0, lat))
        return (lon + 180) / 360 * n, (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n

    def rahmen(z: int):
        xy = [proj(la, lo, z) for la, lo in punkte]
        xs, ys = [p[0] for p in xy], [p[1] for p in xy]
        return xy, min(xs), max(xs), min(ys), max(ys)

    if kcfg["zoom"]:
        z = kcfg["zoom"]
    elif len(punkte) == 1:
        z = 12
    else:
        for z in range(15, 1, -1):  # größte Zoomstufe, bei der alle Wegpunkte mit Rand ins Bild passen
            _, x1, x2, y1, y2 = rahmen(z)
            if x2 - x1 <= KARTE_W * 0.76 and y2 - y1 <= KARTE_H * 0.70:
                break
    xy, x1, x2, y1, y2 = rahmen(z)
    x0, y0 = round((x1 + x2) / 2 - KARTE_W / 2), round((y1 + y2) / 2 - KARTE_H / 2)
    bild = Image.new("RGB", (KARTE_W, KARTE_H), (221, 221, 221))
    n = 2 ** z
    kacheln = [(tx, ty) for tx in range(x0 // 256, (x0 + KARTE_W - 1) // 256 + 1)
               for ty in range(y0 // 256, (y0 + KARTE_H - 1) // 256 + 1) if 0 <= ty < n]
    print(f"Lade Karte ({len(kacheln)} Kacheln, Zoomstufe {z}) …")

    def holen(t):
        url = kcfg["kacheln"].replace("{z}", str(z)).replace("{x}", str(t[0] % n)).replace("{y}", str(t[1]))
        with Image.open(io.BytesIO(kachel_laden(url))) as k:
            return t, k.convert("RGB")

    with ThreadPoolExecutor(max_workers=2) as pool:
        for (tx, ty), k in pool.map(holen, kacheln):
            bild.paste(k, (tx * 256 - x0, ty * 256 - y0))
    buf = io.BytesIO()
    bild.save(buf, "JPEG", quality=82, optimize=True, progressive=True)
    return base64.b64encode(buf.getvalue()).decode("ascii"), [(x - x0, y - y0) for x, y in xy]


def wp_titel(w: dict, i: int) -> str:
    return " – ".join(t for t in (w["text"], datum_text(w["datum"]) if w["datum"] else "") if t) or f"Wegpunkt {i}"


def karte_html(cfg: dict) -> str:
    """Liest [karte] und [[wegpunkt]] und liefert den HTML-Abschnitt (leer, wenn keine Karte gewünscht)."""
    esc = html.escape
    kcfg = dict(KARTE_DEFAULTS)
    for k, v in (cfg.get("karte") or {}).items():
        if k not in KARTE_DEFAULTS:
            fehler(f"Unbekannte Einstellung in [karte]: {k}")
        if type(v) is not type(KARTE_DEFAULTS[k]):
            fehler(f"[karte] {k}: unerwarteter Wert {v!r}")
        kcfg[k] = v
    roh = cfg.get("wegpunkt") or []
    if not kcfg["anzeigen"] or not roh:
        return ""
    if kcfg["art"] not in ("route", "punkte"):
        fehler('[karte] art muss "route" oder "punkte" sein.')
    if kcfg["zoom"] and not 2 <= kcfg["zoom"] <= 18:
        fehler("[karte] zoom muss 0 (automatisch) oder 2 bis 18 sein.")
    wps = []
    for i, w in enumerate(roh, 1):
        lat, lon = w.get("lat"), w.get("lon")
        if isinstance(lat, bool) or isinstance(lon, bool) or not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
            fehler(f"Wegpunkt {i}: 'lat' und 'lon' müssen Zahlen sein (z. B. lat = 54.69260).")
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            fehler(f"Wegpunkt {i}: Koordinaten außerhalb des gültigen Bereichs (lat {lat}, lon {lon}).")
        wps.append({"lat": float(lat), "lon": float(lon), "text": str(w.get("text", "")).strip(),
                    "datum": als_datum(w.get("datum"), f"Wegpunkt {i}")})
    try:
        b64, pos = karte_rendern([(w["lat"], w["lon"]) for w in wps], kcfg)
    except Exception as ex:
        fehler(f"Die Karte konnte nicht geladen werden ({ex}).\n"
               "        Internetverbindung prüfen oder die Karte mit 'anzeigen = false' unter [karte] abschalten.")

    route = kcfg["art"] == "route" and len(wps) > 1
    linie = ""
    if route:
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in pos)
        linie = (f'<svg viewBox="0 0 {KARTE_W} {KARTE_H}" preserveAspectRatio="none" aria-hidden="true">'
                 f'<polyline class="route-rand" points="{pts}"/><polyline class="route" points="{pts}"/></svg>')
    hat_liste = any(w["text"] or w["datum"] for w in wps)
    # Wegpunkte, die auf der Karte (fast) aufeinanderliegen, teilen sich eine Markierung: „2 · 4“
    gruppen: list[dict] = []
    for i, (w, (x, y)) in enumerate(zip(wps, pos), 1):
        for g in gruppen:
            if math.hypot(g["x"] - x, g["y"] - y) < 40:
                g["nr"].append(i)
                g["titel"].append(wp_titel(w, i))
                break
        else:
            gruppen.append({"x": x, "y": y, "nr": [i], "titel": [wp_titel(w, i)]})
    pins, liste = [], []
    for g in gruppen:
        stil = f'style="left:{g["x"] / KARTE_W * 100:.2f}%;top:{g["y"] / KARTE_H * 100:.2f}%"'
        nr = " · ".join(str(k) for k in g["nr"])
        titel = "; ".join(f"{k}: {t}" for k, t in zip(g["nr"], g["titel"]))
        if hat_liste:
            pins.append(f'<a class="pin" href="#wegpunkt-{g["nr"][0]}" {stil} title="{esc(titel, quote=True)}" '
                        f'aria-label="Wegpunkt {esc(titel, quote=True)}">{nr}</a>')
        else:
            pins.append(f'<span class="pin" {stil}>{nr}</span>')
    for i, w in enumerate(wps, 1):
        text = f'<span class="wp-text">{esc(w["text"])}</span>' if w["text"] else ""
        datum = f'<span class="wp-datum">{esc(datum_text(w["datum"]))}</span>' if w["datum"] else ""
        liste.append(f'<li id="wegpunkt-{i}"><span class="wp-nr" aria-hidden="true">{i}</span><span class="wp-info">{text}{datum}</span></li>')
    name = "Karte mit Route" if route else "Karte mit Wegpunkten"
    out = (f'<section class="karte" aria-label="{name}"><div class="karte-bild">'
           f'<img alt="{name}" width="{KARTE_W}" height="{KARTE_H}" src="data:image/jpeg;base64,{b64}">'
           f'{linie}{"".join(pins)}<span class="quelle">{esc(kcfg["quelle"])}</span></div>')
    if hat_liste:
        out += f'<ol class="wegpunkte">{"".join(liste)}</ol>'
    return out + "</section>"


def cmd_build(args) -> None:
    cfg_pfad = Path(args.konfiguration).expanduser()
    if cfg_pfad.is_dir():
        cfg_pfad = cfg_pfad / CONFIG_NAME
    if not cfg_pfad.is_file():
        fehler(f"Konfigurationsdatei nicht gefunden: {cfg_pfad}")
    try:
        with open(cfg_pfad, "rb") as f:
            cfg = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        fehler(f"{cfg_pfad.name} ist kein gültiges TOML: {e}")
    basis = cfg_pfad.parent

    titel = str(cfg.get("titel", "")).strip()
    if not titel:
        fehler("'titel' fehlt oder ist leer.")
    untertitel = str(cfg.get("untertitel", "")).strip()

    einzel = als_datum(cfg.get("datum"), "'datum'")
    von = als_datum(cfg.get("datum_von"), "'datum_von'")
    bis = als_datum(cfg.get("datum_bis"), "'datum_bis'")
    if einzel and (von or bis):
        fehler("Bitte entweder 'datum' ODER 'datum_von'/'datum_bis' angeben, nicht beides.")
    if bool(von) != bool(bis):
        fehler("Für einen Zeitraum werden 'datum_von' und 'datum_bis' gebraucht.")
    album_datum = datum_text(einzel) if einzel else zeitraum_text(von, bis) if von else ""

    ein = dict(DEFAULTS)
    for k, v in (cfg.get("einstellungen") or {}).items():
        if k not in DEFAULTS:
            fehler(f"Unbekannte Einstellung: {k}")
        if isinstance(DEFAULTS[k], float) and type(v) is int:
            v = float(v)
        if type(v) is not type(DEFAULTS[k]):
            fehler(f"Einstellung {k}: unerwarteter Wert {v!r}")
        ein[k] = v
    if not (ein["vorschau_klein"] < ein["vorschau_gross"] <= ein["vollbild"]):
        fehler("Es muss gelten: vorschau_klein < vorschau_gross <= vollbild")

    bilder = cfg.get("bild") or []
    if not bilder:
        fehler("Keine [[bild]]-Einträge in der Konfiguration.")
    eintraege = []
    for i, b in enumerate(bilder, 1):
        name = str(b.get("datei", "")).strip()
        if not name:
            fehler(f"Bild {i}: 'datei' fehlt.")
        pfad = (basis / name)
        if not pfad.is_file():
            fehler(f"Bild {i}: Datei nicht gefunden: {pfad}")
        if pfad.suffix.lower() in HEIC_EXT and not HEIF_OK:
            fehler("Für HEIC-Bilder wird pillow-heif gebraucht:  pip install pillow-heif")
        eintraege.append({
            "pfad": pfad,
            "unterschrift": str(b.get("unterschrift", "")).strip(),
            "datum": als_datum(b.get("datum"), f"Bild {i} ({name})"),
            "panorama": b.get("panorama") is True,
            "bildwinkel": b.get("panorama_bildwinkel"),
        })
        e = eintraege[-1]
        if e["panorama"] and e["bildwinkel"] is None:  # Reihenfolge: Angabe am Bild, dann EXIF, dann [einstellungen]
            aus_exif = pano_bildwinkel_exif(pfad)
            e["bildwinkel"] = aus_exif[0] if aus_exif else ein["panorama_bildwinkel"]
            quelle = f"aus EXIF, Brennweite {aus_exif[1]:g} mm" if aus_exif else "Standardwert, keine Brennweite in den EXIF-Daten"
            print(f"Panorama {name}: senkrechter Bildwinkel {e['bildwinkel']:g}° ({quelle})")
        elif not e["panorama"]:
            e["bildwinkel"] = ein["panorama_bildwinkel"]
        bw = eintraege[-1]["bildwinkel"]
        if isinstance(bw, bool) or not isinstance(bw, (int, float)) or not 10 <= bw <= 150:
            fehler(f"Bild {i} ({name}): panorama_bildwinkel muss zwischen 10 und 150 Grad liegen.")

    karte = karte_html(cfg)

    ausgabe = Path(args.ausgabe).expanduser() if args.ausgabe else basis / str(cfg.get("ausgabe") or "album.html")

    print(f"Verarbeite {len(eintraege)} Bilder …")
    fertig = 0

    def arbeit(e):
        nonlocal fertig
        try:
            e.update(bild_verarbeiten(e["pfad"], ein, e["panorama"]))
        except Exception as ex:
            raise RuntimeError(f"{e['pfad'].name}: {ex}") from ex
        fertig += 1
        print(f"  [{fertig}/{len(eintraege)}] {e['pfad'].name}")

    try:
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(arbeit, eintraege))
    except RuntimeError as ex:
        fehler(f"Bild konnte nicht verarbeitet werden – {ex}")

    # ── HTML zusammensetzen ──
    esc = html.escape
    figuren, daten = [], []
    i = -1
    for nr, e in enumerate(eintraege):
        w, h = e["w"], e["h"]
        if e["panorama"]:
            alt = e["unterschrift"] or f"Panorama {nr + 1}"
            cap = f'<figcaption>{esc(e["unterschrift"])}</figcaption>' if e["unterschrift"] else ""
            figuren.append(
                f'<figure class="pano"><div class="pano-mat"><div class="pano-view" data-bildwinkel="{float(e["bildwinkel"]):g}">'
                f'<img alt="{esc(alt, quote=True)}" width="{w}" height="{h}" decoding="async" '
                f'src="data:image/jpeg;base64,{e["pano"]}"></div></div>{cap}</figure>')
            continue
        i += 1
        breite = 100 if w >= h else round(100 * w / h, 2)   # Bild sitzt mittig im quadratischen Passepartout
        dateiname = e["pfad"].stem + ".jpg"
        bdatum = datum_text(e["datum"]) if (e["datum"] and ein["bilddatum_anzeigen"]) else ""
        alt = e["unterschrift"] or f"Foto {nr + 1}"
        cap = f'<figcaption>{esc(e["unterschrift"])}</figcaption>' if e["unterschrift"] else ""
        figuren.append(
            f'<figure class="foto" data-i="{i}" data-w="{w}" data-h="{h}" '
            f'data-name="{esc(dateiname, quote=True)}" data-date="{esc(bdatum, quote=True)}">'
            f'<div class="mat"><img style="width:{breite}%;aspect-ratio:{w}/{h}" alt="{esc(alt, quote=True)}" '
            f'loading="lazy" decoding="async" '
            f'sizes="(max-width: 700px) 42vw, 300px" '
            f'srcset="data:image/jpeg;base64,{e["klein"]} {e["kw"]}w, data:image/jpeg;base64,{e["gross"]} {e["gw"]}w" '
            f'src="data:image/jpeg;base64,{e["klein"]}"></div>{cap}</figure>'
        )
        daten.append(f'<script type="text/plain" id="voll-{i}">{e["voll"]}</script>')

    kopf = f"<h1>{esc(titel)}</h1>"
    if untertitel:
        kopf += f'<p class="sub">{esc(untertitel)}</p>'
    if album_datum:
        kopf += f'<p class="datum"><span>{esc(album_datum)}</span></p>'
    n = len(eintraege)
    anzahl = f"{n} Foto" + ("" if n == 1 else "s")

    seite = (TEMPLATE
             .replace("%%CSS%%", CSS.replace("%%FONT400%%", FONT_400).replace("%%FONT600%%", FONT_600)
                      .replace("%%DARK_AUTO%%", dark_css(":root:not([data-theme=light])"))
                      .replace("%%DARK_SET%%", dark_css(":root[data-theme=dark]")))
             .replace("%%JS%%", JS + (JS_PANO if any(e["panorama"] for e in eintraege) else ""))
             .replace("%%TITEL%%", esc(titel))
             .replace("%%KOPF%%", kopf)
             .replace("%%KARTE%%", karte)
             .replace("%%ANZAHL%%", anzahl))
    vor, nach = seite.split("%%FOTOS%%")
    mitte, ende = nach.split("%%DATEN%%")

    with open(ausgabe, "w", encoding="utf-8", newline="\n") as f:
        f.write(vor)
        f.write("\n".join(figuren))
        f.write(mitte)
        f.write("\n".join(daten))
        f.write(ende)

    groesse = ausgabe.stat().st_size
    print(f"Fertig: {ausgabe}  ({mb(groesse)}, {n} Bilder)")
    if groesse > 250_000_000:
        print("Hinweis: Die Datei ist sehr groß; auf Handys kann das Öffnen dauern oder scheitern.\n"
              "         Kleiner wird sie mit einem niedrigeren Wert für 'vollbild' oder 'qualitaet_vollbild'.")


# ───────────────────────────── Vorlage ─────────────────────────────

DARK_VARS = ("--bg:#161C18;--fg:#E6ECE7;--muted:#A9B5AC;--mat:#242C27;--mat-shadow:0 0 0 1px #36413A;"
             "--lb-bg:#0F1411;--lb-muted:#A9B5AC;--btn-bg:#E6ECE7;--btn-fg:#161C18;--nav-bg:#242C27;"
             "--nav-shadow:0 0 0 1px #36413A;color-scheme:dark")


def dark_css(sel: str) -> str:
    return (f"{sel}{{{DARK_VARS}}}{sel} .i-sun{{display:block}}{sel} .i-moon{{display:none}}"
            f"{sel} .karte-bild>img{{filter:invert(1) hue-rotate(180deg) brightness(.95) contrast(.88)}}")


CSS = r"""
@font-face{font-family:"Bricolage Grotesque";font-style:normal;font-weight:400;font-display:swap;src:url(data:font/woff2;base64,%%FONT400%%) format("woff2")}
@font-face{font-family:"Bricolage Grotesque";font-style:normal;font-weight:600;font-display:swap;src:url(data:font/woff2;base64,%%FONT600%%) format("woff2")}
:root{--bg:#DCE3DD;--fg:#1F2A24;--muted:#4A584F;--mat:#FFFFFF;--mat-shadow:0 1px 2px rgba(31,42,36,.12),0 8px 24px rgba(31,42,36,.08);
--lb-bg:#CFD8D1;--lb-muted:#3F4D44;--btn-bg:#1F2A24;--btn-fg:#FFFFFF;--nav-bg:#FFFFFF;--nav-shadow:0 1px 2px rgba(31,42,36,.16);color-scheme:light}
.i-sun{display:none}
@media (prefers-color-scheme:dark){%%DARK_AUTO%%}
%%DARK_SET%%
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--fg);font-family:"Bricolage Grotesque",system-ui,-apple-system,"Segoe UI",sans-serif;line-height:1.35}
button{font:inherit;color:inherit;cursor:pointer;-webkit-tap-highlight-color:transparent}
:focus-visible{outline:2px solid var(--fg);outline-offset:3px}
.seite{position:relative;padding:88px 40px}
.inhalt{max-width:1120px;margin:0 auto;display:flex;flex-direction:column;gap:64px}
header{display:flex;flex-direction:column;align-items:center;gap:14px;text-align:center}
h1{margin:0;font-size:60px;line-height:1.05;font-weight:600;letter-spacing:-.02em;text-wrap:balance;overflow-wrap:anywhere}
.sub{margin:0;font-size:20px;color:var(--muted);text-wrap:balance;white-space:pre-line}
.datum{margin:6px 0 0}
.datum span{display:inline-block;font-size:15px;color:var(--muted);border:1px solid var(--muted);border-radius:999px;padding:6px 16px}
.rund{width:44px;height:44px;flex:none;display:flex;align-items:center;justify-content:center;background:transparent;border:1px solid var(--muted);border-radius:999px;padding:0}
.thema{display:none}
.js .thema{display:flex}
.seite>.thema{position:absolute;top:24px;right:28px}
.raster{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(300px,44%),1fr));gap:40px 24px}
.foto{margin:0;display:flex;flex-direction:column;gap:12px;min-width:0}
.mat{aspect-ratio:1;background:var(--mat);box-shadow:var(--mat-shadow);display:flex;align-items:center;justify-content:center;padding:9%}
.mat img{display:block;height:auto;max-width:100%;background:rgba(127,127,127,.18)}
.js .mat{cursor:zoom-in}
.pano{grid-column:1/-1;margin:0;display:flex;flex-direction:column;gap:12px;min-width:0}
.pano-mat{background:var(--mat);box-shadow:var(--mat-shadow);padding:28px}
.pano-view{position:relative;overflow:hidden;background:rgba(127,127,127,.18)}
.pano-view>img{display:block;width:100%;height:auto}
.pano-view.aktiv{aspect-ratio:2.2}
.pano-view.aktiv>img{position:absolute;width:1px;height:1px;opacity:0;pointer-events:none}
.pano-view>canvas{position:absolute;inset:0;width:100%;height:100%;display:block;touch-action:pan-y;cursor:grab;-webkit-user-select:none;user-select:none}
.pano-view>canvas.zieht{cursor:grabbing}
.pano-zoom{position:absolute;right:12px;bottom:12px;display:flex;gap:8px}
.pano-zoom button{width:44px;height:44px;display:flex;align-items:center;justify-content:center;background:var(--nav-bg);box-shadow:var(--nav-shadow);border:none;border-radius:999px;padding:0}
.pano-zoom button[disabled]{opacity:.35;cursor:default}
.pano-hinweis{position:absolute;left:12px;bottom:12px;height:44px;display:flex;align-items:center;gap:8px;font-size:14px;background:var(--nav-bg);box-shadow:var(--nav-shadow);padding:0 16px;border-radius:999px;pointer-events:none;transition:opacity .4s}
.pano-hinweis.weg{opacity:0}
figcaption{font-size:15px;color:var(--muted);text-align:center;text-wrap:balance;overflow-wrap:anywhere}
footer{font-size:15px;color:var(--muted);text-align:center}
.karte{background:var(--mat);box-shadow:var(--mat-shadow);padding:28px}
.karte-bild{position:relative;aspect-ratio:3/2;overflow:hidden;background:rgba(127,127,127,.18)}
.karte-bild>img{position:absolute;inset:0;width:100%;height:100%;display:block}
.karte-bild>svg{position:absolute;inset:0;width:100%;height:100%}
.route,.route-rand{fill:none;stroke-linejoin:round;stroke-linecap:round;vector-effect:non-scaling-stroke}
.route-rand{stroke:var(--btn-fg);stroke-width:7}
.route{stroke:var(--btn-bg);stroke-width:3}
.pin,.wp-nr{min-width:28px;height:28px;padding:0 6px;border-radius:999px;background:var(--btn-bg);color:var(--btn-fg);font-size:14px;font-weight:600;line-height:1;display:flex;align-items:center;justify-content:center;flex:none}
.pin{position:absolute;transform:translate(-50%,-50%);text-decoration:none;box-shadow:0 0 0 2px var(--btn-fg)}
a.pin::after{content:"";position:absolute;inset:-8px}
.quelle{position:absolute;right:0;bottom:0;font-size:11px;line-height:1.3;background:rgba(255,255,255,.82);color:#1F2A24;padding:2px 6px}
.wegpunkte{list-style:none;margin:24px 0 0;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(min(240px,100%),1fr));gap:14px 24px}
.wegpunkte li{display:flex;gap:10px;align-items:flex-start;scroll-margin:24px;border-radius:999px}
.wegpunkte li:target .wp-nr{box-shadow:0 0 0 3px var(--mat),0 0 0 5px var(--fg)}
.wp-info{display:flex;flex-direction:column;gap:1px;padding-top:4px;min-width:0}
.wp-text{font-size:15px;overflow-wrap:anywhere}
.wp-datum{font-size:13px;color:var(--muted)}
@media (max-width:700px){
.seite{padding:68px 16px 48px}
.inhalt{gap:36px}
header{gap:12px}
h1{font-size:36px;line-height:1.08}
.sub{font-size:16px}
.datum span{font-size:13px;padding:5px 14px}
.seite>.thema{top:12px;right:12px}
.raster{gap:24px 14px}
.foto{gap:8px}
figcaption,footer{font-size:13px}
.karte{padding:12px}
.pano-mat{padding:12px}
.pano-view.aktiv{aspect-ratio:1.4}
.pano-hinweis{font-size:13px;padding:0 12px}
.wegpunkte{margin-top:16px;gap:12px}
}
.lb{position:fixed;inset:0;z-index:10;background:var(--lb-bg);display:grid;grid-template-columns:48px minmax(0,1fr) 48px;grid-template-rows:auto minmax(0,1fr) auto;
grid-template-areas:"top top top" "prev stage next" "cap cap cap";gap:12px 24px;padding:20px 28px 28px;--pad:28px}
.lb[hidden]{display:none}
.lb-top{grid-area:top;display:flex;justify-content:space-between;align-items:center;gap:16px}
.lb-zahl{font-size:15px;color:var(--lb-muted)}
.lb-aktionen{display:flex;align-items:center;gap:8px}
.lb .rund{border-color:var(--lb-muted)}
.speichern{height:44px;padding:0 18px;display:flex;align-items:center;gap:8px;background:var(--btn-bg);color:var(--btn-fg);border:none;border-radius:999px;font-size:15px}
.nav{width:48px;height:48px;align-self:center;display:flex;align-items:center;justify-content:center;background:var(--nav-bg);box-shadow:var(--nav-shadow);border:none;border-radius:999px;padding:0}
.nav[disabled]{opacity:.35;cursor:default}
.zurueck{grid-area:prev}
.weiter{grid-area:next}
.lb-buehne{grid-area:stage;display:flex;align-items:center;justify-content:center;min-width:0;min-height:0;touch-action:pan-y pinch-zoom}
.lb-mat{background:var(--mat);box-shadow:var(--mat-shadow),0 16px 48px rgba(0,0,0,.14);padding:var(--pad);line-height:0}
.lb-mat img{display:block;background:rgba(127,127,127,.18)}
.lb-text{grid-area:cap;display:flex;flex-direction:column;align-items:center;gap:2px;text-align:center;min-height:46px;justify-content:center}
.lb-unterschrift{font-size:18px;text-wrap:balance;overflow-wrap:anywhere}
.lb-datum{font-size:14px;color:var(--lb-muted)}
@media (max-width:700px){
.lb{grid-template-columns:1fr 1fr;grid-template-rows:auto minmax(0,1fr) auto auto;grid-template-areas:"top top" "stage stage" "cap cap" "prev next";gap:14px;padding:16px;--pad:14px}
.zurueck{justify-self:start}
.weiter{justify-self:end}
.lb-unterschrift{font-size:17px}
}
"""

ICON = ('<svg aria-hidden="true" class="%s" width="%d" height="%d" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">%s</svg>')
I_MOON = ICON % ("i-moon", 18, 18, '<path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z"/>')
I_SUN = ICON % ("i-sun", 18, 18, '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>')
I_SAVE = ICON % ("", 18, 18, '<path d="M12 4v12M7 11l5 5 5-5M5 20h14"/>')
I_X = ICON % ("", 18, 18, '<path d="M6 6l12 12M18 6L6 18"/>')
I_PREV = ICON % ("", 20, 20, '<path d="M15 5l-7 7 7 7"/>')
I_NEXT = ICON % ("", 20, 20, '<path d="M9 5l7 7-7 7"/>')
THEMA_BTN = f'<button type="button" class="rund thema" aria-label="Helles oder dunkles Design umschalten">{I_MOON}{I_SUN}</button>'

TEMPLATE = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="generator" content="fotoalbum.py {VERSION}">
<title>%%TITEL%%</title>
<script>(function(){{var d=document.documentElement;d.classList.add("js");try{{var t=localStorage.getItem("fotoalbum-theme");if(t==="dark"||t==="light")d.setAttribute("data-theme",t)}}catch(e){{}}}})()</script>
<style>%%CSS%%</style>
</head>
<body>
<div class="seite">
{THEMA_BTN}
<div class="inhalt">
<header>%%KOPF%%</header>
%%KARTE%%
<main class="raster">
%%FOTOS%%
</main>
<footer>%%ANZAHL%%</footer>
</div>
</div>
<div class="lb" id="lb" hidden role="dialog" aria-modal="true" aria-label="Großansicht">
<div class="lb-top">
<span class="lb-zahl" id="lbZahl"></span>
<div class="lb-aktionen">
{THEMA_BTN}
<button type="button" class="speichern" id="lbSpeichern">{I_SAVE}<span>Speichern</span></button>
<button type="button" class="rund" id="lbZu" aria-label="Schließen">{I_X}</button>
</div>
</div>
<button type="button" class="nav zurueck" id="lbZurueck" aria-label="Vorheriges Bild">{I_PREV}</button>
<div class="lb-buehne" id="lbBuehne"><div class="lb-mat"><img id="lbBild" alt=""></div></div>
<button type="button" class="nav weiter" id="lbWeiter" aria-label="Nächstes Bild">{I_NEXT}</button>
<div class="lb-text"><span class="lb-unterschrift" id="lbUnterschrift"></span><span class="lb-datum" id="lbDatum"></span></div>
</div>
%%DATEN%%
<script>%%JS%%</script>
</body>
</html>
"""

JS = r"""
(function(){
"use strict";
var root=document.documentElement,KEY="fotoalbum-theme";
function $(id){return document.getElementById(id)}

/* ── Hell/Dunkel: folgt dem System, bis man umschaltet; die Wahl gilt für alle Alben derselben Herkunft ── */
function istDunkel(){var t=root.getAttribute("data-theme");if(t)return t==="dark";return !!(window.matchMedia&&matchMedia("(prefers-color-scheme: dark)").matches)}
[].forEach.call(document.querySelectorAll(".thema"),function(b){b.addEventListener("click",function(){
  var neu=istDunkel()?"light":"dark";root.setAttribute("data-theme",neu);
  try{localStorage.setItem(KEY,neu)}catch(e){}
})});
window.addEventListener("storage",function(e){if(e.key===KEY&&(e.newValue==="dark"||e.newValue==="light"))root.setAttribute("data-theme",e.newValue)});

/* ── Großansicht ── */
var figs=[].slice.call(document.querySelectorAll(".foto")),lb=$("lb"),bild=$("lbBild"),buehne=$("lbBuehne");
var akt=-1,ausloeser=null,urls={},reihenfolge=[],imVerlauf=false;

function vorschau(f){var t=f.querySelector("img").getAttribute("srcset").split(/\s+/);return t[2]||t[0]}
function vollUrl(i){
  if(urls[i])return urls[i];
  var el=$("voll-"+i),bin=atob(el.textContent.trim()),n=bin.length,a=new Uint8Array(n);
  for(var k=0;k<n;k++)a[k]=bin.charCodeAt(k);
  urls[i]=URL.createObjectURL(new Blob([a],{type:"image/jpeg"}));
  reihenfolge.push(i);
  while(reihenfolge.length>4){var alt=reihenfolge.shift();if(alt===akt){reihenfolge.push(alt);continue}URL.revokeObjectURL(urls[alt]);delete urls[alt]}
  return urls[i];
}
function einpassen(){
  if(akt<0)return;
  var f=figs[akt],w=+f.getAttribute("data-w"),h=+f.getAttribute("data-h");
  var pad=parseFloat(getComputedStyle(lb).getPropertyValue("--pad"))||0,r=buehne.getBoundingClientRect();
  var s=Math.min((r.width-2*pad)/w,(r.height-2*pad)/h,1);if(!(s>0))s=.01;
  bild.style.width=Math.round(w*s)+"px";bild.style.height=Math.round(h*s)+"px";
}
function zeige(i){
  if(i<0||i>=figs.length)return;
  akt=i;var f=figs[i],img=f.querySelector("img"),cap=f.querySelector("figcaption");
  bild.src=vorschau(f);bild.alt=img.alt;
  $("lbZahl").textContent=(i+1)+" / "+figs.length;
  $("lbUnterschrift").textContent=cap?cap.textContent:"";
  $("lbDatum").textContent=f.getAttribute("data-date")||"";
  $("lbZurueck").disabled=i===0;$("lbWeiter").disabled=i===figs.length-1;
  einpassen();
  /* großes Bild erst auf Anfrage aus den eingebetteten Daten holen */
  setTimeout(function(){if(akt!==i)return;try{var u=vollUrl(i),p=new Image();p.onload=function(){if(akt===i)bild.src=u};p.src=u}catch(e){}},30);
}
function auf(i,von){
  ausloeser=von||null;lb.hidden=false;root.style.overflow="hidden";zeige(i);$("lbZu").focus();
  try{history.pushState({fotoalbum:1},"");imVerlauf=true}catch(e){imVerlauf=false}
}
function zu(ausVerlauf){
  if(lb.hidden)return;
  lb.hidden=true;root.style.overflow="";akt=-1;bild.removeAttribute("src");
  if(ausloeser&&ausloeser.focus)ausloeser.focus();
  if(imVerlauf&&!ausVerlauf){imVerlauf=false;try{history.back()}catch(e){}}
  imVerlauf=false;
}
window.addEventListener("popstate",function(){zu(true)});

figs.forEach(function(f,i){
  var m=f.querySelector(".mat");m.setAttribute("role","button");m.setAttribute("tabindex","0");
  m.setAttribute("aria-label",f.querySelector("img").alt+" – groß anzeigen");
  m.addEventListener("click",function(){auf(i,m)});
  m.addEventListener("keydown",function(e){if(e.key==="Enter"||e.key===" "){e.preventDefault();auf(i,m)}});
});
$("lbZu").addEventListener("click",function(){zu(false)});
$("lbZurueck").addEventListener("click",function(){zeige(akt-1)});
$("lbWeiter").addEventListener("click",function(){zeige(akt+1)});
buehne.addEventListener("click",function(e){if(e.target===buehne)zu(false)});
$("lbSpeichern").addEventListener("click",function(){
  if(akt<0)return;
  try{var a=document.createElement("a");a.href=vollUrl(akt);a.download=figs[akt].getAttribute("data-name");document.body.appendChild(a);a.click();a.remove()}catch(e){}
});
document.addEventListener("keydown",function(e){
  if(lb.hidden)return;
  if(e.key==="Escape"){e.preventDefault();zu(false)}
  else if(e.key==="ArrowLeft")zeige(akt-1);
  else if(e.key==="ArrowRight")zeige(akt+1);
  else if(e.key==="Tab"){
    var fok=[].filter.call(lb.querySelectorAll("button"),function(b){return !b.disabled&&b.offsetParent!==null});
    if(!fok.length)return;var erst=fok[0],letzt=fok[fok.length-1];
    if(e.shiftKey&&document.activeElement===erst){e.preventDefault();letzt.focus()}
    else if(!e.shiftKey&&document.activeElement===letzt){e.preventDefault();erst.focus()}
    else if(!lb.contains(document.activeElement)){e.preventDefault();erst.focus()}
  }
});
/* Wischen zum Blättern (nicht, solange gezoomt ist) */
var tx=0,ty=0,einFinger=false;
buehne.addEventListener("touchstart",function(e){einFinger=e.touches.length===1;if(einFinger){tx=e.touches[0].clientX;ty=e.touches[0].clientY}},{passive:true});
buehne.addEventListener("touchend",function(e){
  if(!einFinger||e.changedTouches.length!==1)return;
  if(window.visualViewport&&visualViewport.scale>1.01)return;
  var dx=e.changedTouches[0].clientX-tx,dy=e.changedTouches[0].clientY-ty;
  if(Math.abs(dx)>50&&Math.abs(dx)>1.5*Math.abs(dy))zeige(dx<0?akt+1:akt-1);
},{passive:true});
window.addEventListener("resize",einpassen);
})();
"""

JS_PANO = r"""
/* ── Panorama: zylindrisches Bild per WebGL entzerrt (geradlinig) anzeigen, schwenkbar ── */
(function(){
"use strict";
var VS="attribute vec2 a;void main(){gl_Position=vec4(a,0.,1.);}";
var FS="precision highp float;uniform sampler2D t;uniform vec2 res;uniform float yaw,pitch,tanv,theta,tanp,rund;"+
"void main(){vec2 p=gl_FragCoord.xy/res*2.-1.;vec3 d=vec3(p.x*tanv*res.x/res.y,p.y*tanv,1.);"+
"float c=cos(pitch),s=sin(pitch);d=vec3(d.x,d.y*c+d.z*s,d.z*c-d.y*s);"+
"float u=(atan(d.x,d.z)+yaw)/theta+.5;if(rund>.5)u=fract(u);"+
"gl_FragColor=texture2D(t,vec2(u,.5-d.y/length(d.xz)/(2.*tanp)));}";
var SVG='<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">';

function start(view){
  var img=view.querySelector("img"),W=img.naturalWidth,H=img.naturalHeight;if(!W||!H)return;
  var cv=document.createElement("canvas"),gl=null,zwei=false;
  try{gl=cv.getContext("webgl2");zwei=!!gl;if(!gl)gl=cv.getContext("webgl")||cv.getContext("experimental-webgl")}catch(e){}
  if(!gl)return; /* ohne WebGL bleibt das flache Bild stehen */
  function shader(typ,src){var s=gl.createShader(typ);gl.shaderSource(s,src);gl.compileShader(s);return s}
  var pr=gl.createProgram();gl.attachShader(pr,shader(gl.VERTEX_SHADER,VS));gl.attachShader(pr,shader(gl.FRAGMENT_SHADER,FS));gl.linkProgram(pr);
  if(!gl.getProgramParameter(pr,gl.LINK_STATUS))return;
  gl.useProgram(pr);
  gl.bindBuffer(gl.ARRAY_BUFFER,gl.createBuffer());gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,3,-1,-1,3]),gl.STATIC_DRAW);
  var a=gl.getAttribLocation(pr,"a");gl.enableVertexAttribArray(a);gl.vertexAttribPointer(a,2,gl.FLOAT,false,0,0);
  /* Textur: bei Bedarf auf die Grenze der Grafikkarte verkleinern */
  var max=gl.getParameter(gl.MAX_TEXTURE_SIZE),quelle=img;
  if(W>max){var k=document.createElement("canvas");k.width=max;k.height=Math.max(1,Math.round(H*max/W));k.getContext("2d").drawImage(img,0,0,k.width,k.height);quelle=k}
  gl.bindTexture(gl.TEXTURE_2D,gl.createTexture());
  try{gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,quelle)}catch(e){return}
  gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);
  if(zwei){gl.generateMipmap(gl.TEXTURE_2D);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR_MIPMAP_LINEAR)}
  else gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);
  var U={};["res","yaw","pitch","tanv","theta","tanp","rund"].forEach(function(n){U[n]=gl.getUniformLocation(pr,n)});

  /* Geometrie: Zylinderprojektion, Breite = f*theta, Höhe = 2*f*tan(Bildwinkel/2) */
  var pv=(parseFloat(view.getAttribute("data-bildwinkel"))||54)*Math.PI/180,tanp=Math.tan(pv/2);
  var theta=W/H*2*tanp,rund=theta>=2*Math.PI-.02;if(theta>2*Math.PI)theta=2*Math.PI;
  var yaw=0,pitch=0,zoom=1,zoomMin=1,ZOOM_MAX=4,bw=1,bh=1;

  view.appendChild(cv);cv.tabIndex=0;cv.setAttribute("role","img");
  cv.setAttribute("aria-label",img.alt+" – Panorama, mit Ziehen oder den Pfeiltasten umsehen");
  var zb=document.createElement("div");zb.className="pano-zoom";
  zb.innerHTML='<button type="button" aria-label="Verkleinern">'+SVG+'<path d="M5 12h14"/></svg></button><button type="button" aria-label="Vergrößern">'+SVG+'<path d="M5 12h14M12 5v14"/></svg></button>';
  var hinweis=document.createElement("div");hinweis.className="pano-hinweis";
  hinweis.innerHTML=SVG+'<path d="M8 7l-5 5 5 5M16 7l5 5-5 5M3 12h18"/></svg><span>Ziehen zum Umsehen</span>';
  view.appendChild(hinweis);view.appendChild(zb);view.classList.add("aktiv");
  var minus=zb.children[0],plus=zb.children[1];

  function grenzen(){
    var asp=bw/bh;
    zoomMin=1;if(!rund&&theta<Math.PI){zoomMin=Math.max(1,asp*tanp/Math.tan(theta/2))}
    zoom=Math.min(ZOOM_MAX,Math.max(zoomMin,zoom));
    var tv=tanp/zoom,pl=Math.max(0,pv/2-Math.atan(tv));pitch=Math.min(pl,Math.max(-pl,pitch));
    if(!rund){
      var x=tv*asp,c=Math.cos(pitch),s=Math.abs(Math.sin(pitch)),n=c-tv*s;
      var halb=n>1e-3?Math.atan(x/n):Math.PI/2,yl=Math.max(0,theta/2-halb);
      yaw=Math.min(yl,Math.max(-yl,yaw));
    }
    minus.disabled=zoom<=zoomMin+1e-6;plus.disabled=zoom>=ZOOM_MAX-1e-6;
    return tv;
  }
  function zeichne(){
    var r=view.getBoundingClientRect(),dpr=Math.min(window.devicePixelRatio||1,2);
    bw=Math.max(1,r.width);bh=Math.max(1,r.height);
    var w=Math.round(bw*dpr),h=Math.round(bh*dpr);
    if(cv.width!==w||cv.height!==h){cv.width=w;cv.height=h}
    var tv=grenzen();
    gl.viewport(0,0,w,h);
    gl.uniform2f(U.res,w,h);gl.uniform1f(U.yaw,yaw);gl.uniform1f(U.pitch,pitch);gl.uniform1f(U.tanv,tv);
    gl.uniform1f(U.theta,theta);gl.uniform1f(U.tanp,tanp);gl.uniform1f(U.rund,rund?1:0);
    gl.drawArrays(gl.TRIANGLES,0,3);
  }
  var wartet=false;function neu(){if(wartet)return;wartet=true;requestAnimationFrame(function(){wartet=false;zeichne()})}

  var zieht=false,lx=0,ly=0;
  cv.addEventListener("pointerdown",function(e){zieht=true;lx=e.clientX;ly=e.clientY;cv.classList.add("zieht");hinweis.classList.add("weg");try{cv.setPointerCapture(e.pointerId)}catch(x){}});
  cv.addEventListener("pointermove",function(e){
    if(!zieht)return;var tv=tanp/zoom;
    yaw-=(e.clientX-lx)*2*tv*(bw/bh)/bw;
    if(e.pointerType!=="touch")pitch+=(e.clientY-ly)*2*tv/bh; /* am Handy bleibt senkrechtes Wischen das Scrollen der Seite */
    lx=e.clientX;ly=e.clientY;neu();
  });
  function ende(){zieht=false;cv.classList.remove("zieht")}
  cv.addEventListener("pointerup",ende);cv.addEventListener("pointercancel",ende);
  cv.addEventListener("keydown",function(e){
    var st=.12/zoom;
    if(e.key==="ArrowLeft")yaw-=st;else if(e.key==="ArrowRight")yaw+=st;
    else if(e.key==="+"||e.key==="=")zoom*=1.5;else if(e.key==="-")zoom/=1.5;else return;
    e.preventDefault();hinweis.classList.add("weg");neu();
  });
  cv.addEventListener("dblclick",function(){zoom=zoom>zoomMin*1.2?zoomMin:zoomMin*2;neu()});
  plus.addEventListener("click",function(){zoom*=1.5;neu()});
  minus.addEventListener("click",function(){zoom/=1.5;neu()});
  cv.addEventListener("webglcontextlost",function(e){e.preventDefault()});
  if(window.ResizeObserver)new ResizeObserver(neu).observe(view);else window.addEventListener("resize",neu);
  zeichne();
}
[].forEach.call(document.querySelectorAll(".pano-view"),function(v){
  var img=v.querySelector("img");
  function los(){try{start(v)}catch(e){}}
  if(img.complete&&img.naturalWidth)los();else img.addEventListener("load",los);
});
})();
"""

# Schrift „Bricolage Grotesque“ (SIL Open Font License 1.1, © The Bricolage Grotesque Project Authors),
# lateinischer Zeichensatz, als WOFF2 in Base64 – wird in jede HTML-Datei eingebettet.
FONT_400 = (
    "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"
    "t82fBnBwA="
)
FONT_600 = (
    "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"
    "PPMOwbxbnf943v/v8YXbAQ=="
)


def main() -> None:
    ap = argparse.ArgumentParser(prog="fotoalbum.py", description="Fotoalbum als einzelne HTML-Datei erzeugen.")
    sub = ap.add_subparsers(dest="befehl", required=True)
    p1 = sub.add_parser("init", help="Schritt 1: Bilderliste (album.toml) für einen Ordner anlegen")
    p1.add_argument("ordner", help="Ordner mit den Bildern (JPEG, HEIC)")
    p1.add_argument("--force", action="store_true", help="vorhandene album.toml überschreiben")
    p1.set_defaults(func=cmd_init)
    p2 = sub.add_parser("build", help="Schritt 2: HTML-Datei aus der Konfiguration erzeugen")
    p2.add_argument("konfiguration", help="Pfad zur album.toml (oder zum Ordner, in dem sie liegt)")
    p2.add_argument("-o", "--ausgabe", help="Pfad der HTML-Datei (überschreibt 'ausgabe' aus der Konfiguration)")
    p2.set_defaults(func=cmd_build)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()