# AGENTS.md – Arbeitsanweisungen für Coding-Agenten

Dieses Repository enthält ein einzelnes Python-Tool, `fotoalbum.py`. Was es tut und tun soll, steht in
[SPEC.md](SPEC.md); die Benutzung in [README.md](README.md); das gemeinsame Grunddesign, auf dem alle Teile
der Seite aufbauen, in [DESIGN.md](DESIGN.md). Die geplante Architektur aus Rumpfseite und Web Components steht in
[ARCHITEKTUR.md](ARCHITEKTUR.md); die Widgets haben eigene Beschreibungen ([PANORAMA.md](PANORAMA.md),
[WANDERUNG.md](WANDERUNG.md)). Lies SPEC.md, bevor du etwas änderst, und DESIGN.md, bevor du
etwas am Aussehen änderst.

## Wichtig zuerst

- **`fotoalbum.py` nie komplett lesen.** Die Zeilen ab `FONT_400 = (` bis vor `def main()` sind rund 550
  Zeilen Base64 der eingebetteten Schrift (ca. 60 KB). Lies gezielt mit Zeilenbereich oder suche mit `grep`.
  Diesen Block nicht anfassen.
- **Offene Entscheidungen nicht selbst treffen.** SPEC.md Abschnitt 9.1 listet fünf Fragen zum verlinkten
  Modus, die der Nutzer beantworten muss. Erst fragen, dann umsetzen.
  Ebenso WANDERUNG.md Abschnitt 14 für das Wanderungs-Widget.
  Für den Umbau auf Web Components gilt ARCHITEKTUR.md; Einzelheiten nach deren Abschnitt 8.10 mit dem
  Nutzer klären.
- **Wanderungs-Widget erst umsetzen, wenn die Architektur steht.** Die Bergfex-Beispieldatei liegt in
  `tests/widgets/wanderung/Natz_-_Schabs_Apfelweg.gpx` (WANDERUNG.md Entscheidung 15). Die Wanderung wird eine Web Component;
  begonnen wird laut ARCHITEKTUR.md mit dem Panorama. An der Spec weiterarbeiten ist erlaubt.
- **Die `album.toml` bleibt rückwärtskompatibel (SPEC G6).** Würde eine Änderung eine bisher gültige
  Konfiguration brechen oder anders auswerten: nicht umsetzen, sondern zuerst ausdrücklich darauf hinweisen
  und auf die Entscheidung des Nutzers warten.
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
| Einbettung | `eingebettet`, `panorama_figur`, `widget_daten_json`, `komponenten_js`, `UEBERGABE_JS` |
| Vorlage | `DARK_VARS`, `dark_css`, `CSS`, Icons, `TEMPLATE`, `JS` |
| Schrift | `FONT_400`, `FONT_600` (Base64, nicht lesen) |
| Einstieg | `main` mit `argparse` |

Wie die Vorlage zusammengesetzt wird:

- `CSS` und `JS` sind rohe Strings. `TEMPLATE` ist ein f-String: geschweifte Klammern darin
  müssen verdoppelt werden.
- Platzhalter der Form `%%NAME%%` werden in `cmd_build` per `str.replace` gefüllt. `%%FOTOS%%` und
  `%%DATEN%%` teilen die Seite, damit die großen Base64-Blöcke direkt in die Datei gestreamt werden.
- Web Components liegen in `widgets/<name>/<name>.js` (ARCHITEKTUR.md 5.1), gemeinsame Hilfen in
  `widgets/gemeinsam/`. `komponenten_js` hängt nur die benutzten an, dazu `UEBERGABE_JS`, das den JSON-Block
  `album-daten` (`%%WIDGETDATEN%%`) per Eigenschaft `daten` an die Elemente mit `data-daten` verteilt.
  Bisher umgesetzt: `panorama`. Die übrigen Teile stecken noch in `CSS`/`JS`.
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
   kommentierte Zeile in `cmd_init` und einen Eintrag in README.md und SPEC.md. Der Default erhält das
   bisherige Verhalten; bestehende `album.toml` müssen unverändert weiter funktionieren (SPEC G6).
   Was nur ein Widget betrifft, kommt an den Verweis im Widget, nicht an `[[bild]]` (SPEC 9.6).
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

Testseiten der Web Components (ARCHITEKTUR.md 7): `python widgets/testseiten.py <Ordner>` erzeugt je
Widget eine Testseite aus synthetischen Testdaten (`widgets/<name>/testseite.py`, `widgets/<name>/testdaten/`)
und ein Beispielalbum. Ein Workflow veröffentlicht sie bei jedem Push auf GitHub Pages
(`<branch>/<widget>/`). Bei Änderungen an einer Component ihre Testseite ansehen.

Weitere bewährte Testdaten (bisher von Hand erzeugt, noch nicht im Repository):

- Fotos: mit Pillow erzeugte JPEG- und HEIC-Bilder in Hoch-, Quer- und Quadratformat, eines mit
  EXIF-Drehung, einige mit GPS und Aufnahmedatum, eines ohne EXIF.
- Karte: lokaler HTTP-Server, der beliebige Kacheln `/{z}/{x}/{y}.png` liefert; in `[karte]` als `kacheln`
  eintragen. So läuft der Test ohne Internet und ohne den OSM-Server zu belasten.
- Panorama: liegt jetzt als Erzeuger in `widgets/panorama/testdaten/erzeugen.py`.
- Browser-Automatisierung: Playwright mit Chrome hat funktioniert, für WebGL mit Software-Rendering.

Die übrigen Testdaten kommen mit der Umstellung der jeweiligen Teile auf Web Components in deren
Verzeichnis.

## Was als ungeprüft gilt

SPEC.md Abschnitt 8 führt auf, was nie mit echten Daten oder Geräten getestet wurde. Behaupte in Commits
und Antworten nichts davon als funktionierend, solange es niemand geprüft hat.

## Git

- Kleine, thematisch saubere Commits; Nachricht auf Deutsch im Imperativ („Ergänze …", „Behebe …").
- Erzeugte Alben, Testseiten und `album.toml` aus Testordnern nicht einchecken. Synthetische Testdaten einer
  Component (bzw. ihr deterministischer Erzeuger) gehören in deren Verzeichnis und werden eingecheckt.