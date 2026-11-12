# SPEC – fotoalbum.py

Verbindliche Beschreibung dessen, was das Tool tut und tun soll. Abschnitte 1–7 beschreiben den umgesetzten
Stand (Version `1.3.1-poc`), Abschnitt 8 die bekannten Lücken, Abschnitt 9 das Geplante mit offenen Entscheidungen.

## 1. Ziel und Grundsätze

- Familien-Fotoalbum als **standalone HTML-Datei**, optimiert auf 30–40 Bilder.
- Minimalistisch-ästhetisch, funktioniert auf Desktop und Handy.
- **G1 – Eine Datei:** Die HTML-Datei lädt nichts nach. Bilder, Schrift, CSS, JavaScript und Karte sind
  eingebettet. (Geplante Ausnahme: der verlinkte Modus, siehe 9.1.)
- **G2 – Grundansicht ohne JavaScript:** Titel, Raster, Unterschriften, Karte und Hell/Dunkel nach
  Systemeinstellung sind reines HTML/CSS. Großansicht, Speichern, Umschalter und Panorama-Widget sind Zusatz.
- **G3 – Keine Foto-Metadaten in der Ausgabe:** EXIF (inkl. GPS) wird nicht übernommen. Ausnahme sind die
  bewusst konfigurierten Wegpunkte.
- **G4 – Konfiguration von Hand editierbar:** TOML mit deutschen Schlüsseln und erklärenden Kommentaren.
- Hauptverbreitungsweg ist die Weitergabe der Datei (Ablage in der Cloud); daneben eigener Server.

## 2. Kommandozeile

| Befehl | Wirkung |
|---|---|
| `init <ordner> [--force]` | schreibt `<ordner>/album.toml`; bricht ab, wenn sie existiert und `--force` fehlt |
| `build <album.toml oder ordner> [-o ausgabe]` | schreibt die HTML-Datei |

Fehler enden mit `Fehler: …` und Exit-Code ≠ 0. Meldungen sind deutsch.

## 3. `init`

- Erfasst Dateien mit Endung `.jpg .jpeg .heic .heif` (ohne versteckte Dateien), nicht rekursiv.
- Sortierung: nach EXIF-Aufnahmezeit, Bilder ohne Zeit ans Ende, jeweils nach Dateiname.
- `titel` = Ordnername. Datum: bei unterschiedlichen Aufnahmetagen `datum_von`/`datum_bis`, sonst `datum`;
  die jeweils andere Variante steht auskommentiert da.
- Pro Bild: `datei`, `unterschrift = ""`, `datum` (falls EXIF vorhanden).
- **Panorama-Erkennung:** Breite ≥ 2,2 × Höhe (`PANORAMA_AB`) → `panorama = true` plus Kommentar mit dem aus
  EXIF geschätzten Bildwinkel.
- **Wegpunkte aus GPS:** Aufeinanderfolgende Fotos (in Aufnahmereihenfolge) im Umkreis von 1 km
  (`WEGPUNKT_RADIUS_KM`) um das erste Foto der Gruppe werden ein Wegpunkt; Koordinate = Mittelwert, Datum =
  erstes Foto. Nicht aufeinanderfolgende Besuche desselben Orts bleiben getrennte Wegpunkte. Ohne GPS-Daten
  steht ein auskommentiertes Beispiel in der Datei.

## 4. `build` – Validierung

- `titel` Pflicht. `datum` und `datum_von`/`datum_bis` schließen sich aus; ein Zeitraum braucht beide Enden.
- Unbekannte Schlüssel in `[einstellungen]` und `[karte]` sind Fehler; Typen müssen zu den Defaults passen.
- Es muss gelten: `vorschau_klein < vorschau_gross <= vollbild`.
- Jede `datei` muss existieren (relativ zur `album.toml`). HEIC ohne `pillow-heif` ist ein Fehler.
- `panorama_bildwinkel`: 10–150 Grad. Wegpunkte: `lat`/`lon` Pflicht und im gültigen Bereich.
- Datumsformat der Ausgabe: `12. Juli 2026`; Zeiträume verkürzt (`12. – 26. Juli 2026`,
  `28. Juli – 3. August 2026`).

## 5. `build` – Bildverarbeitung

- EXIF-Drehung wird angewendet, Modus RGB, ICC-Profil bleibt erhalten, sonstiges EXIF entfällt.
- Drei JPEG-Größen pro Foto (lange Kante): `vorschau_klein` 480, `vorschau_gross` 1280, `vollbild` 4000.
  Bilder werden nie vergrößert.
- Einbettung: beide Vorschauen als `srcset` mit data-URIs im `<img>`; das große Bild als Base64 in
  `<script type="text/plain" id="voll-N">` am Ende des `<body>`, damit das Raster zuerst erscheint.
- Panorama: nur eine Größe, Breite ≤ `panorama_breite` (8192), als `<img>` mit data-URI.
- Verarbeitung parallel in 4 Threads; Ausgabe wird stückweise geschrieben.

## 6. Die erzeugte Seite

### 6.1 Design „D · Passepartout"

- Schrift Bricolage Grotesque (400, 600), als WOFF2 eingebettet.
- Farben hell: Grund `#DCE3DD`, Text `#1F2A24`, gedämpft `#4A584F`, Passepartout `#FFFFFF`,
  Großansicht-Grund `#CFD8D1`.
- Farben dunkel: Grund `#161C18`, Text `#E6ECE7`, gedämpft `#A9B5AC`, Passepartout `#242C27` mit Kontur
  `#36413A`, Großansicht-Grund `#0F1411`.
- Kopf zentriert: Titel, optionale Unterzeile (Zeilenumbrüche aus der Konfiguration bleiben erhalten),
  optionales Datum als Pille. Fuß: „N Fotos".
- Raster: `repeat(auto-fill, minmax(min(300px, 44%), 1fr))` → 3 Spalten Desktop, 2 Spalten Handy; Inhalt max.
  1120 px breit. Umbruch auf Handy-Maße bei 700 px.
- Jedes Foto sitzt mittig in einem quadratischen Passepartout (9 % Rand) im eigenen Seitenverhältnis.

### 6.2 Hell/Dunkel

- Standard: `prefers-color-scheme`. Umschalter oben rechts und in der Großansicht.
- Die Wahl steht in `localStorage` unter dem festen Schlüssel `fotoalbum-theme` (`light`/`dark`) und gilt
  damit für alle Alben derselben Herkunft. Ohne Speicherzugriff folgt die Seite dem System.
- Umsetzung: CSS-Variablen; dunkle Werte einmal in der Media-Query für `:root:not([data-theme=light])` und
  einmal für `:root[data-theme=dark]` (erzeugt von `dark_css()`).

### 6.3 Großansicht

- Öffnet per Klick/Enter auf ein Passepartout. Zeigt sofort die 1280er Vorschau, dann das große Bild als
  Blob-URL aus dem eingebetteten Base64 (höchstens 4 Blob-URLs gleichzeitig).
- Bedienung: Pfeile, Pfeiltasten, Wischen (nicht bei Pinch-Zoom), Esc, Klick neben das Bild, Zurück-Taste
  des Browsers. Fokus bleibt in der Großansicht und kehrt beim Schließen zum Auslöser zurück.
- „Speichern" lädt das große JPEG als `<Originalname>.jpg`.
- Bildgröße wird per JavaScript in die Bühne eingepasst, nie über die native Größe hinaus.

### 6.4 Karte

- Statisches Kartenbild 1500 × 1000 px (JPEG) aus Web-Mercator-Kacheln, beim Bauen geladen und eingebettet.
- Zoom automatisch: größte Stufe ≤ 15, bei der alle Wegpunkte in 76 % der Breite und 70 % der Höhe passen;
  ein einzelner Wegpunkt: Stufe 12. `zoom` überschreibt.
- Markierungen sind HTML-Elemente über dem Bild (Position in Prozent), nummeriert in Dateireihenfolge.
  Wegpunkte, die weniger als 40 Kartenpixel auseinanderliegen, teilen sich eine Markierung („2 · 4").
- `art = "route"`: Polylinie in Dateireihenfolge (Luftlinie). `art = "punkte"`: keine Linie.
- Unter der Karte eine Liste mit Nummer, Text und Datum; Markierungen verlinken per Anker dorthin. Hat kein
  Wegpunkt Text oder Datum, entfällt die Liste.
- Dunkelmodus: CSS-Filter auf dem Kartenbild. Quellenangabe unten rechts auf der Karte.
- Kachelabruf mit eigenem User-Agent, 2 parallele Verbindungen, Zwischenspeicher `~/.cache/fotoalbum/kacheln`.

### 6.5 Panorama (PoC)

- Annahme: zylindrische Projektion. Breite = f·θ, Höhe = 2·f·tan(v/2) ⇒ Schwenkwinkel
  θ = (Breite/Höhe)·2·tan(v/2), begrenzt auf 360°.
- Senkrechter Bildwinkel v, Reihenfolge: `panorama_bildwinkel` am Bild → EXIF → `[einstellungen]`.
  EXIF-Formel: v = 2·atan(`PANO_BESCHNITT` · 17,31 / f35) mit f35 = Kleinbild-Brennweite (EXIF-Tag 41989),
  17,31 mm = halbe lange Seite eines 4:3-Bildes bei Kleinbild-Diagonale, `PANO_BESCHNITT` = 0,77.
- Darstellung: WebGL-Fragment-Shader rechnet pro Pixel den Sichtstrahl einer geradlinigen Kamera
  (Gieren, Nicken, Zoom) auf Zylinderkoordinaten um. WebGL2 mit Mipmaps, sonst WebGL1.
- Widget spannt alle Rasterspalten (`grid-column: 1 / -1`); Seitenverhältnis 2,2 am Desktop, 1,4 am Handy.
- Bedienung: Ziehen schwenkt; Plus/Minus, Doppelklick und `+`/`-` zoomen (bis 4×); Pfeiltasten schwenken.
  Auf Touch-Geräten schwenkt nur waagerechtes Wischen (`touch-action: pan-y`), senkrechtes scrollt die Seite.
- Der Ausschnitt bleibt immer innerhalb des Bildes (Grenzen für Gieren, Nicken und Mindestzoom).
- Ist das Bild breiter als `MAX_TEXTURE_SIZE`, wird es im Browser vorher verkleinert.
- Ohne JavaScript oder WebGL bleibt das Panorama als flacher Streifen sichtbar.
- Panoramen sind nicht Teil der Großansicht und haben kein „Speichern".

## 7. Entscheidungen mit Begründung

- **Großes Bild 4000 px statt Original:** hält die Datei handhabbar; die Originale liegen ohnehin separat.
- **HEIC → JPEG:** außer Safari zeigt kein verbreiteter Browser HEIC an.
- **Statische Karte statt Kartenbibliothek:** wahrt G1; Preis: nicht zoom- oder verschiebbar.
- **Dunkle Passepartouts im Dunkelmodus:** 36 weiße Flächen würden nachts blenden.
- **Keine WebGL-Verkleinerung der Fotos:** Browser skalieren bereits gut; WebGL brächte Probleme mit
  Texturgrenzen, Farbprofilen, Pinch-Zoom und lokal geöffneten Dateien. (Empfehlung, vom Nutzer noch nicht
  bestätigt.)

## 8. Bekannte Lücken und Ungeprüftes

Geprüft wurde bisher nur mit künstlich erzeugten Testbildern in Chrome (Desktop- und Handy-Viewport,
Software-Rendering). **Nicht** geprüft:

- echte iPhone-HEICs und echte iPhone-Panoramen
- ob iPhone-Panoramen die Kleinbild-Brennweite im EXIF tragen; ob `PANO_BESCHNITT` = 0,77 stimmt (der Wert
  ist so gewählt, dass 26 mm die angenommenen 54° ergibt, nicht gemessen)
- quer gehaltene Panoramen (anderer senkrechter Winkel) und hochkant geschwenkte Panoramen
- Abruf echter OpenStreetMap-Kacheln (nur gegen einen lokalen Ersatzserver getestet)
- ein Album in voller Größe (36 echte Fotos), Ladezeit und Speicherbedarf auf Handys
- Safari, Firefox, echte Mobilgeräte; lokales Öffnen auf dem iPhone (dort läuft JavaScript in der
  Dateien-Vorschau vermutlich nur eingeschränkt)
- Es gibt keine automatisierten Tests.

## 9. Geplant

### 9.1 Verlinkter Modus und `--self-contained` (angefragt, Entscheidungen offen)

Wunsch: Nur mit `--self-contained` werden die großen Bilder eingebettet. Ohne das Flag verweist die
Großansicht auf das Original im selben Pfad wie die HTML-Datei. Die Vorschaubilder bleiben immer eingebettet.

Bereits geklärt:

- Lazy Loading ergibt sich im verlinkten Modus von selbst (Laden erst beim Öffnen); sinnvoll ist das
  Vorladen des jeweils nächsten Bildes.
- Kein Qualitätsverlust; beim Zoomen steht mehr Auflösung bereit.

**Offen – vor der Umsetzung vom Nutzer zu entscheiden:**

1. HEIC im verlinkten Modus. Vorschlag: JPEG-Kopie in voller Auflösung in einem Unterordner für die Anzeige,
   „Speichern" liefert das Original. Alternative: HEIC direkt verlinken, Nicht-Safari-Browser sehen nur die
   1280er Vorschau.
2. Panoramen in beiden Modi eingebettet lassen? Gründe: lokal geöffnet verweigert WebGL nachgeladene Bilder
   als Textur (Annahme, nicht nachgetestet); Originale überschreiten ohnehin die Texturgrenzen.
3. Original am Handy erst bei Zoom oder Speichern laden (die 1280er Vorschau ist dort etwa bildschirmscharf)
   oder immer sofort?
4. WebGL-Verkleinerung weglassen (Empfehlung: ja)?
5. Verlinkte Originale tragen EXIF inkl. GPS (Konflikt mit G3). Akzeptieren oder bereinigte Kopien erzeugen?

Vorgesehenes Detail: Die HTML-Datei liegt im Bilderordner und nutzt relative, URL-kodierte Pfade; liegt die
Ausgabe per `-o` woanders, bricht der verlinkte Modus mit Fehlermeldung ab.

### 9.2 Route aus GPX-Datei (gewünscht)

Wegpunkte entlang eines GPX-Tracks verbinden statt per Luftlinie. Noch nicht spezifiziert.

### 9.3 Panorama über den PoC hinaus (gewünscht)

Offen: Großansicht und „Speichern" für Panoramen, Verifikation mit echten iPhone-Panoramen, Kalibrierung
von `PANO_BESCHNITT`, Umgang mit quer gehaltenen und senkrechten Panoramen.

### 9.4 Mögliche weitere Punkte (nicht beauftragt)

- Grundfarbe pro Album wählbar
- Automatisierte Tests (siehe AGENTS.md)