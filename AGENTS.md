# AGENTS.md – Arbeitsanweisungen für Coding-Agenten

Dieses Repository enthält ein einzelnes Python-Tool, `fotoalbum.py`. Was es tut und tun soll, steht in
[SPEC.md](SPEC.md); die Benutzung in [README.md](README.md). Lies SPEC.md, bevor du etwas änderst.

## Wichtig zuerst

- **`fotoalbum.py` nie komplett lesen.** Die Zeilen ab `FONT_400 = (` bis vor `def main()` sind rund 550
  Zeilen Base64 der eingebetteten Schrift (ca. 60 KB). Lies gezielt mit Zeilenbereich oder suche mit `grep`.
  Diesen Block nicht anfassen.
- **Offene Entscheidungen nicht selbst treffen.** SPEC.md Abschnitt 9.1 listet fünf Fragen zum verlinkten
  Modus, die der Nutzer beantworten muss. Erst fragen, dann umsetzen.
- **Sprache:** Bezeichner, Kommentare, Meldungen, Konfigurationsschlüssel und Oberfläche sind deutsch. So
  weiterführen.

## Aufbau von `fotoalbum.py`

Reihenfolge in der Datei (Zeilennummern verschieben sich, per `grep -n` suchen):

| Abschnitt | Inhalt |
|---|---|
| Kopf | Imports, `VERSION`, `DEFAULTS`, `KARTE_DEFAULTS`, `SYMBOLE`, Konstanten |
| Hilfsfunktionen | `exif_lesen`, `ist_panorama`, `pano_bildwinkel_exif`, `entfernung_km`, `als_datum`, `datum_text`, `zeitraum_text` |
| Schritt 1 | `cmd_init` – schreibt die `album.toml` zeilenweise |
| Schritt 2 | `jpeg_bytes`, `bild_verarbeiten`, `kachel_laden`, `karte_rendern`, `karte_html`, `klappbar`, `stationen_html`, `cmd_build` |
| Vorlage | `DARK_VARS`, `dark_css`, `CSS`, Icons, `TEMPLATE`, `JS`, `JS_PANO` |
| Schrift | `FONT_400`, `FONT_600` (Base64, nicht lesen) |
| Einstieg | `main` mit `argparse` |

Wie die Vorlage zusammengesetzt wird:

- `CSS`, `JS` und `JS_PANO` sind rohe Strings. `TEMPLATE` ist ein f-String: geschweifte Klammern darin
  müssen verdoppelt werden.
- Platzhalter der Form `%%NAME%%` werden in `cmd_build` per `str.replace` gefüllt. `%%FOTOS%%` und
  `%%DATEN%%` teilen die Seite, damit die großen Base64-Blöcke direkt in die Datei gestreamt werden.
- `JS_PANO` wird nur angehängt, wenn das Album ein Panorama enthält.
- Alles, was aus der Konfiguration ins HTML geht, läuft durch `html.escape`.

## Regeln für Änderungen

1. **G1 – Eine Datei.** Die erzeugte HTML-Datei lädt nichts nach: keine CDN-Skripte, keine Webfonts, keine
   externen Bilder. Ausnahme wird erst der verlinkte Modus (SPEC 9.1).
2. **G2 – Ohne JavaScript nutzbar.** Neue Inhalte müssen als HTML/CSS sinnvoll dastehen; JavaScript wertet
   nur auf. Elemente, die nur mit JavaScript funktionieren, per `.js`-Klasse einblenden.
3. **G3 – Keine Foto-Metadaten in der Ausgabe.** Kein EXIF durchreichen.
4. **Hell und Dunkel gemeinsam pflegen.** Farben nur über CSS-Variablen; dunkle Werte in `DARK_VARS`,
   zusätzliche dunkle Regeln in `dark_css()`.
5. **Handy mitdenken.** Der Umbruch liegt bei 700 px; Bedienelemente mindestens 44 px groß.
6. **Screenreader und Tastaturbedienung sind keine Anforderung** (SPEC G5). Dafür keinen Aufwand treiben
   und keine Lösung deswegen verwerfen; Vorhandenes muss nicht ausgebaut werden.
7. **Abhängigkeiten:** nur Pillow und pillow-heif plus Standardbibliothek. Neue Abhängigkeiten vorher mit
   dem Nutzer klären.
8. **Konfiguration:** Neue Schlüssel bekommen einen Default, eine Validierung in `cmd_build`, eine
   kommentierte Zeile in `cmd_init` und einen Eintrag in README.md und SPEC.md. Bestehende `album.toml`
   müssen weiter funktionieren.
9. **Fehlermeldungen** über `fehler()`: deutsch, mit Hinweis, was zu tun ist.
10. **`VERSION` erhöhen** bei jeder Änderung am Verhalten; SPEC.md und README.md im selben Commit anpassen.

## Prüfen

Es gibt noch keine automatisierten Tests. Bis dahin jede Änderung so prüfen:

```
python -c "import ast; ast.parse(open('fotoalbum.py', encoding='utf-8').read())"
python fotoalbum.py init  <Testordner> --force
python fotoalbum.py build <Testordner>
```

Danach die erzeugte Seite im Browser ansehen, mindestens:

- Desktop- und Handybreite, hell und dunkel
- Großansicht: öffnen, blättern, speichern, schließen
- mit abgeschaltetem JavaScript
- Stationen und Karte ein- und ausklappen; Startzustand an Desktop (offen) und Handy (zu) prüfen
- bei Kartenänderungen: `art = "route"` und `art = "punkte"`
- bei Panoramaänderungen: gerade Linien bleiben gerade (siehe unten)

Bewährte Testdaten (bisher von Hand erzeugt, noch nicht im Repository):

- Fotos: mit Pillow erzeugte JPEG- und HEIC-Bilder in Hoch-, Quer- und Quadratformat, eines mit
  EXIF-Drehung, einige mit GPS und Aufnahmedatum, eines ohne EXIF.
- Karte: lokaler HTTP-Server, der beliebige Kacheln `/{z}/{x}/{y}.png` liefert; in `[karte]` als `kacheln`
  eintragen. So läuft der Test ohne Internet und ohne den OSM-Server zu belasten.
- Panorama: synthetisches Zylinder-Panorama eines Quaders mit Gitterlinien (Strahl pro Pixel aus
  Zylinderkoordinaten, Schnitt mit den Wänden). Im Widget müssen die Gitterlinien gerade sein.
- Browser-Automatisierung: Playwright mit Chrome hat funktioniert, für WebGL mit Software-Rendering.

Ein sinnvoller erster Auftrag wäre, diese Testdaten-Erzeugung und einen Rauchtest als `tests/` ins
Repository zu holen.

## Was als ungeprüft gilt

SPEC.md Abschnitt 8 führt auf, was nie mit echten Daten oder Geräten getestet wurde. Behaupte in Commits
und Antworten nichts davon als funktionierend, solange es niemand geprüft hat.

## Git

- Kleine, thematisch saubere Commits; Nachricht auf Deutsch im Imperativ („Ergänze …", „Behebe …").
- Erzeugte Alben, Testbilder und `album.toml` aus Testordnern nicht einchecken.