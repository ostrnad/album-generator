# fotoalbum.py

Erzeugt aus einem Ordner mit Fotos ein Familien-Fotoalbum als **eine einzige HTML-Datei**. Bilder, Schrift,
CSS und JavaScript sind eingebettet; neben der HTML-Datei gibt es keine weiteren Dateien.

Ausgelegt auf etwa 30–40 Bilder pro Album, für Desktop und Handy, mit hellem und dunklem Design.

Stand: Version `1.6`.

## Voraussetzungen

- Python 3.11 oder neuer
- `pip install pillow pillow-heif`
- das ganze Repository: `fotoalbum.py` braucht das Verzeichnis `widgets/` daneben (dort liegen die Web
  Components, die der Bau in die HTML-Datei einbettet; siehe [ARCHITEKTUR.md](ARCHITEKTUR.md))
- Internetzugang beim Bauen, falls das Album eine Karte enthält (einmalig, für die Kartenkacheln)

## Benutzung

```
python fotoalbum.py init  <Bilderordner>
python fotoalbum.py build <Bilderordner>/album.toml
```

**Schritt 1 – `init`** liest alle JPEG- und HEIC-Bilder im Ordner und schreibt `album.toml` hinein:

- Titel (vorbelegt mit dem Ordnernamen), Untertitel, Datum oder Zeitraum (vorbelegt aus den Aufnahmedaten)
- ein `[[bild]]`-Block pro Bild, sortiert nach Aufnahmezeit
- `[[wegpunkt]]`-Blöcke aus den GPS-Daten der Fotos, falls vorhanden
- ein auskommentiertes Beispiel für `[[station]]`
- `panorama = true` bei sehr breiten Bildern, dazu `panorama_bildwinkel` mit dem aus den EXIF-Daten
  berechneten Wert

Eine vorhandene `album.toml` wird nur mit `--force` überschrieben.

**Schritt 2 – `build`** liest die Konfiguration und schreibt die HTML-Datei, standardmäßig `album.html`
neben der Konfiguration. Mit `-o <Pfad>` oder dem Schlüssel `ausgabe` lässt sich das Ziel ändern.

## Konfiguration (`album.toml`)

```toml
titel = "Sommer an der Nordsee"
untertitel = "Zwei Wochen Föhr"        # optional

# Entweder ein einzelnes Datum ODER ein Zeitraum, beides optional
# datum = 2026-07-12
datum_von = 2026-07-12
datum_bis = 2026-07-26

ausgabe = "album.html"

[einstellungen]
vorschau_klein = 480          # lange Kante in px: Bilder im Raster
vorschau_gross = 1280         # lange Kante: scharfe Displays, Sofortbild der Großansicht
vollbild = 4000               # lange Kante des großen Bildes (Großansicht, Speichern)
qualitaet_vorschau = 80       # JPEG-Qualität
qualitaet_vollbild = 88
bilddatum_anzeigen = true     # Datum des einzelnen Bildes in der Großansicht
panorama_breite = 8192        # maximale Breite eines Panoramas in px
panorama_bildwinkel = 54.0    # senkrechter Bildwinkel in Grad, falls EXIF keine Brennweite liefert

[[bild]]
datei = "IMG_0001.HEIC"       # relativ zur album.toml
unterschrift = "Ankunft mit der Fähre"   # optional
datum = 2026-07-12            # optional

[[bild]]
datei = "IMG_0042.HEIC"
panorama = true               # schwenkbares, entzerrtes Panorama über die volle Breite
panorama_bildwinkel = 54.3    # von init aus EXIF berechnet; fehlt die Zeile, gilt EXIF, sonst [einstellungen]

[[station]]                   # optional: Zeitleiste zwischen Kopf und Karte
name = "Ferienwohnung"        # frei, z. B. "Tag 1" oder ein Datum
text = "Dorfstraße 1 in Musterdorf"
symbol = "haus"               # optional: haus oder punkt (Standard)

[[station]]
name = "Tag 1"
text = "Wanderung zum See"

[karte]
anzeigen = true
art = "route"                 # "route" = Wegpunkte verbunden, "punkte" = einzelne Wegpunkte
zoom = 0                      # 0 = automatisch, sonst 2–18
# kacheln = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
# quelle = "© OpenStreetMap-Mitwirkende"

[[wegpunkt]]
text = "Ankunft in Wyk"       # optional
datum = 2026-07-14            # optional
lat = 54.69250                # Pflicht
lon = 8.56780                 # Pflicht
```

- Die Reihenfolge der `[[bild]]`-Blöcke ist die Reihenfolge im Album; ein gelöschter Block lässt das Bild weg.
- Der Untertitel darf mehrzeilig sein: `untertitel = "Erste Zeile\nZweite Zeile"` oder als TOML-Block in
  drei Anführungszeichen. Zeilenumbrüche werden übernommen.
- Datumsangaben gehen als TOML-Datum (`2026-07-12`) oder als Text (`"12.07.2026"`).
- Stationen und Wegpunkte sind getrennte Dinge: Stationen erzählen den Ablauf als Text (ohne Koordinaten),
  Wegpunkte markieren ausgewählte Orte auf der Karte. Bei einer Station muss `name` oder `text` gefüllt sein.
- Die Karte erscheint, sobald es mindestens einen `[[wegpunkt]]` gibt und `anzeigen = true` ist.

## Was die erzeugte Seite kann

- **Raster** im Passepartout-Design: 3 Spalten am Desktop, 2 am Handy, Bildunterschriften unter dem Bild
- **Großansicht** mit Blättern (Pfeile, Tastatur, Wischen), Zähler, Unterschrift, Datum und „Speichern"
- **Hell/Dunkel** nach Systemeinstellung, mit Umschalter; die Wahl wird im Browser gemerkt
- **Stationen** als Zeitleiste mit Symbol pro Eintrag
- **Einklappbar:** Stationen und Karte lassen sich getrennt ein- und ausklappen; am Desktop sind sie
  standardmäßig offen, am Handy zu (funktioniert ohne JavaScript)
- **Karte** als eingebettetes Bild mit nummerierten Wegpunkten, wahlweise als Route verbunden
- **Panorama** ([PANORAMA.md](PANORAMA.md)): hochkant aufgenommene, seitwärts geschwenkte Panoramen werden per WebGL entzerrt; Ziehen
  schwenkt, Plus/Minus, Doppelklick oder zwei Finger zoomen
- **Ohne JavaScript** bleiben Raster, Unterschriften, Karte und Hell/Dunkel nach System erhalten

## Testseiten der Widgets

`python widgets/testseiten.py <Ordner>` erzeugt für jedes Widget eine Testseite mit synthetischen Testdaten
(hell/dunkel, Handy- und Desktopbreite, ohne JavaScript) und ein kleines Beispielalbum. Bei jedem Push
veröffentlicht ein Workflow sie auf GitHub Pages, je Branch in einem eigenen Ordner. Dafür muss Pages in den
Einstellungen des Repositorys auf den Branch `gh-pages` (Ordner `/`) stehen.

## Wissenswertes

- **Dateigröße:** Mit 36 echten Fotos sind grob 100–200 MB zu erwarten. Kleiner wird die Datei über
  `vollbild` und `qualitaet_vollbild`.
- **Metadaten:** EXIF-Daten der Fotos, auch GPS-Positionen, werden nicht in die HTML-Datei übernommen.
  Wegpunkte dagegen stehen bewusst mit Koordinaten in der Datei.
- **HEIC:** wird für alle Größen in JPEG umgewandelt; „Speichern" liefert `<Name>.jpg`.
- **Gemerktes Design:** gilt für alle Alben derselben Herkunft (Domain). Bei lokal geöffneten Dateien hängt
  es vom Browser ab; im Zweifel folgt die Seite der Systemeinstellung.
- **Route:** Die Wegpunkte werden per Luftlinie verbunden, nicht entlang von Straßen.
- **Karte:** Die Kacheln werden unter `~/.cache/fotoalbum/kacheln` zwischengespeichert.

## Bekannte Lücken

Nicht getestet sind bisher: echte OpenStreetMap-Kacheln, ein Album in
voller Größe, echte Handys sowie Safari und Firefox. Details und geplante Erweiterungen stehen in
[SPEC.md](SPEC.md).

## Lizenzhinweise

- Eingebettete Schrift: Bricolage Grotesque, SIL Open Font License 1.1
- Kartendaten: © OpenStreetMap-Mitwirkende (ODbL); die Nutzungsbedingungen des Kachelservers beachten