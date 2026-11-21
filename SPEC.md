# SPEC – fotoalbum.py

Verbindliche Beschreibung dessen, was das Tool tut und tun soll. Abschnitte 1–7 beschreiben den umgesetzten
Stand (Version `1.6`), Abschnitt 8 die bekannten Lücken, Abschnitt 9 das Geplante mit offenen Entscheidungen.

## 1. Ziel und Grundsätze

- Familien-Fotoalbum als **standalone HTML-Datei**, optimiert auf 30–40 Bilder.
- Minimalistisch-ästhetisch, funktioniert auf Desktop und Handy.
- **G1 – Eine Datei:** Die HTML-Datei lädt nichts nach. Bilder, Schrift, CSS, JavaScript und Karte sind
  eingebettet. (Geplante Ausnahme: der verlinkte Modus, siehe 9.1.)
- **G2 – Grundansicht ohne JavaScript:** Titel, Raster, Unterschriften, Karte und Hell/Dunkel nach
  Systemeinstellung sind reines HTML/CSS. Großansicht, Speichern, Umschalter und Panorama-Widget sind Zusatz.
  *Entfällt mit der Umstellung auf Web Components* (Entscheidung des Nutzers); an ihre Stelle tritt G2′,
  siehe [ARCHITEKTUR.md](ARCHITEKTUR.md). Bis dahin gilt G2 für den umgesetzten Stand.
- **G3 – Keine Foto-Metadaten in der Ausgabe:** EXIF (inkl. GPS) wird nicht übernommen. Ausnahme sind die
  bewusst konfigurierten Wegpunkte.
- **G4 – Konfiguration von Hand editierbar:** TOML mit deutschen Schlüsseln und erklärenden Kommentaren.
- **G5 – Keine Anforderung an Screenreader und Tastaturbedienung:** Für die erzeugten Seiten spielen beide
  laut Nutzer keine Rolle. Vorhandene Tastaturbedienung darf bleiben, begründet aber keine Designentscheidung.
- **G6 – Die `album.toml` bleibt rückwärtskompatibel:** Änderungen am Format der Konfiguration werden immer
  so ausgeführt, dass jede bisher gültige `album.toml` unverändert weiter funktioniert und dasselbe Ergebnis
  liefert. Das heißt: neue Schlüssel sind optional und haben einen Default, der das bisherige Verhalten
  erhält; vorhandene Schlüssel werden weder umbenannt noch entfernt noch in ihrer Bedeutung geändert.
  Ist das im Einzelfall nicht möglich, wird **vor jeder Änderung am Code** ausdrücklich darauf hingewiesen
  und die Entscheidung des Nutzers abgewartet.
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
- Stationen: `name` oder `text` Pflicht; `symbol` muss in `SYMBOLE` stehen.
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
- Panorama: Breite ≤ `panorama_breite` (8192), als Base64 in `<script type="application/octet-stream"
  data-typ="image/jpeg" id="pano-N">` am Ende des `<body>` (ARCHITEKTUR.md 3.4). Dazu ein flacher Streifen
  mit höchstens 2560 px Breite (`PANO_VORSCHAU_BREITE`) als `<img>` mit data-URI im Raster.
- Verarbeitung parallel in 4 Threads; Ausgabe wird stückweise geschrieben.

## 6. Die erzeugte Seite

### 6.1 Design „D · Passepartout"

- Das gemeinsame Grunddesign (Farben, Schrift, Abstände, Knöpfe und andere Bausteine) steht in
  [DESIGN.md](DESIGN.md). Die Abschnitte 6.1–6.7 beschreiben nur, was die einzelnen Teile darüber hinaus tun.
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

### 6.4 Stationen (Zeitleiste)

- Optionaler Abschnitt zwischen Kopf und Karte, gespeist aus `[[station]]` in Dateireihenfolge.
- Bedeutung: Stationen erzählen den Ablauf (z. B. Tagesinhalte, komplette Wanderungen) als reinen Text.
  Sie haben keine Koordinaten und sind bewusst **nicht** mit den Wegpunkten verknüpft; Wegpunkte sind eine
  lose Sammlung besuchter Orte auf der Karte.
- Felder: `name` (frei, z. B. „Tag 1"), `text`, `symbol`. `name` oder `text` muss gefüllt sein.
- Darstellung: senkrechte Linie, pro Eintrag eine Marke, `name` klein darüber, `text` darunter; max. 720 px.
- **Symbole:** Tabelle `SYMBOLE` im Code (Name → SVG-Inhalt 24×24, `None` = Aufzählungspunkt). Vorhanden:
  `punkt` (Standard) und `haus`. Kein Eintrag bekommt automatisch ein Symbol. Ein unbekannter Name ist ein
  Fehler, der die verfügbaren Namen nennt. Erweitern = eine Zeile in `SYMBOLE`.

### 6.5 Einklappbare Abschnitte

- Stationen und Karte (samt Wegpunkt-Liste) sind getrennt einklappbar, jeweils über eine Pille mit Pfeil.
- Standard: am Desktop offen, am Handy (≤ 700 px) zu.
- Umsetzung ohne JavaScript (`klappbar()`): unsichtbare Checkbox plus `<label>`; die Bedeutung von
  „angehakt" ist je Media-Query umgekehrt (Desktop: angehakt = zu, Handy: angehakt = offen). Folge: Wer die
  Fensterbreite über die 700-px-Grenze zieht, sieht den Zustand umspringen. Der Zustand wird nicht gemerkt.

### 6.6 Karte

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

### 6.7 Panorama

- Unterstützt wird genau ein Fall: Gerät hochkant, seitwärts geschwenkt. Quer gehaltene und senkrecht
  geschwenkte Panoramen sind bewusst nicht vorgesehen (Entscheidung des Nutzers).
- Annahme: zylindrische Projektion. Breite = f·θ, Höhe = 2·f·tan(v/2) ⇒ Schwenkwinkel
  θ = (Breite/Höhe)·2·tan(v/2), begrenzt auf 360°.
- Senkrechter Bildwinkel v, Reihenfolge: `panorama_bildwinkel` am Bild → EXIF → `[einstellungen]`.
  `init` schreibt den aus EXIF berechneten Wert als aktive Zeile in den `[[bild]]`-Block; ohne Brennweite
  im EXIF steht dort nur ein auskommentierter Hinweis.
  EXIF-Formel: v = 2·atan(`PANO_BESCHNITT` · 17,31 / f35) mit f35 = Kleinbild-Brennweite (EXIF-Tag 41989),
  17,31 mm = halbe lange Seite eines 4:3-Bildes bei Kleinbild-Diagonale, `PANO_BESCHNITT` = 0,77.
- Umsetzung als Web Component `<album-panorama>` in `widgets/panorama/panorama.js` (ARCHITEKTUR.md).
  Eingabe ist die Eigenschaft `daten` = `{version: 1, bild: "pano-N", breite, hoehe, bildwinkel}`; das
  Übergabeskript der Seite setzt sie aus dem JSON-Block `album-daten` (Schlüssel im Attribut `data-daten`).
  Die Component ersetzt den flachen Streifen per Shadow DOM, sobald WebGL läuft. Farben über
  `--nav-bg`/`--nav-shadow`, Schrift über `--album-schrift`. Testseite: `widgets/panorama/testseite.py`.
- Darstellung: WebGL-Fragment-Shader rechnet pro Pixel den Sichtstrahl einer geradlinigen Kamera
  (Gieren, Nicken, Zoom) auf Zylinderkoordinaten um. WebGL2 mit Mipmaps, sonst WebGL1.
- Widget spannt alle Rasterspalten (`grid-column: 1 / -1`); Seitenverhältnis 2,2 am Desktop, 1,4 am Handy.
- Bedienung: Ziehen schwenkt; Plus/Minus, Doppelklick und Zwei-Finger-Geste zoomen (bis 4×).
- Touch: Das Panorama nimmt alle Gesten selbst entgegen (`touch-action: none`, Touch-Ereignisse) und
  entscheidet selbst; dem Browser überlassen (`pan-y`), übernimmt Safari (iOS) leicht senkrechte Gesten und das
  Schwenken hakt. Unvergrößert entscheiden die ersten 8 px: waagerecht -> die ganze Geste schwenkt, auch nach
  einem Richtungswechsel; senkrecht -> das Panorama scrollt die Seite selbst, mit Nachlauf. Vergrößert schwenkt
  und neigt jede Geste. Nach dem Loslassen laufen Schwenken und (vergrößert) Neigen mit abnehmender
  Geschwindigkeit nach und halten am Bildrand an; hat der Finger vor dem Loslassen stillgestanden, gibt es
  keinen Nachlauf. Ein neuer Finger hält den Nachlauf an. Zwei Finger zoomen; die eigene Zoomgeste von Safari ist auf dem Panorama unterdrückt.
  Folge: Auf einer fremden Seite scrollt senkrechtes Wischen über dem Panorama immer das Fenster, nicht einen
  umgebenden Scrollbereich.
- Der Ausschnitt bleibt immer innerhalb des Bildes (Grenzen für Gieren, Nicken und Mindestzoom).
- Auflösung: Breite ≤ `panorama_breite` (8192 px, reicht laut Nutzer). Ist das Bild breiter als
  `MAX_TEXTURE_SIZE` des Geräts, wird es im Browser vorher verkleinert.
- Ressourcen: Das Widget startet erst, wenn es in die Nähe des Sichtbereichs kommt (600 px Vorlauf), gibt
  seinen Grafikkontext außerhalb davon frei und baut ihn beim Zurückscrollen neu auf. Ein vom Browser
  entzogener Kontext wird ebenso neu aufgebaut. Schwenk und Zoom bleiben dabei erhalten.
- Ohne JavaScript oder WebGL bleibt das Panorama als flacher Streifen sichtbar.
- Panoramen sind nicht Teil der Großansicht, nicht bildschirmfüllend zu öffnen und haben kein „Speichern"
  (Entscheidung des Nutzers, „erstmal").
- Panoramen sind immer eingebettet, auch im späteren `--self-contained`-Modus.

## 7. Entscheidungen mit Begründung

- **Großes Bild 4000 px statt Original:** hält die Datei handhabbar; die Originale liegen ohnehin separat.
- **HEIC → JPEG:** außer Safari zeigt kein verbreiteter Browser HEIC an.
- **Statische Karte statt Kartenbibliothek:** wahrt G1; Preis: nicht zoom- oder verschiebbar.
- **Dunkle Passepartouts im Dunkelmodus:** 36 weiße Flächen würden nachts blenden.
- **Einklappen per Checkbox statt `<details>` oder JavaScript:** nur so ist der Startzustand je
  Bildschirmgröße ohne JavaScript verschieden; der Nachteil für Tastatur und Screenreader ist laut G5 egal.
- **Keine WebGL-Verkleinerung der Fotos:** Browser skalieren bereits gut; WebGL brächte Probleme mit
  Texturgrenzen, Farbprofilen, Pinch-Zoom und lokal geöffneten Dateien. (Empfehlung, vom Nutzer noch nicht
  bestätigt.)

## 8. Bekannte Lücken und Ungeprüftes

Geprüft wurde bisher nur mit künstlich erzeugten Testbildern in Chrome (Desktop- und Handy-Viewport,
Software-Rendering). **Nicht** geprüft:

- Echte iPhone-Panoramen hat der Nutzer selbst ausprobiert („sieht super aus und funktioniert"); welche
  Geräte und Browser, ist nicht dokumentiert. `PANO_BESCHNITT` = 0,77 bleibt eine Schätzung (so gewählt,
  dass 26 mm 54° ergibt), wurde aber nicht beanstandet.
- Zwei-Finger-Zoom im Panorama: nur implementiert, nicht auf einem Touch-Gerät geprüft
- Freigabe und Neuaufbau des Grafikkontexts: nur in Chrome mit Software-Rendering geprüft
- Abruf echter OpenStreetMap-Kacheln (nur gegen einen lokalen Ersatzserver getestet)
- ein Album in voller Größe (36 echte Fotos), Ladezeit und Speicherbedarf auf Handys
- Safari, Firefox, echte Mobilgeräte; lokales Öffnen auf dem iPhone (dort läuft JavaScript in der
  Dateien-Vorschau vermutlich nur eingeschränkt)
- Es gibt keine automatisierten Tests. Die Testseiten der Web Components (ARCHITEKTUR.md 7) sind zum
  Ansehen gedacht; geprüft wurde das Panorama-Widget bisher nur in Chrome mit Software-Rendering.

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
2. Panoramen: Für `--self-contained` entschieden (eingebettet). Für den verlinkten Modus nicht ausdrücklich
   beantwortet; Empfehlung bleibt, sie auch dort einzubetten: lokal geöffnet verweigert WebGL nachgeladene
   Bilder als Textur (Annahme, nicht nachgetestet), und Originale überschreiten ohnehin die Texturgrenzen.
3. Original am Handy erst bei Zoom oder Speichern laden (die 1280er Vorschau ist dort etwa bildschirmscharf)
   oder immer sofort?
4. WebGL-Verkleinerung weglassen (Empfehlung: ja)?
5. Verlinkte Originale tragen EXIF inkl. GPS (Konflikt mit G3). Akzeptieren oder bereinigte Kopien erzeugen?

Vorgesehenes Detail: Die HTML-Datei liegt im Bilderordner und nutzt relative, URL-kodierte Pfade; liegt die
Ausgabe per `-o` woanders, bricht der verlinkte Modus mit Fehlermeldung ab.

### 9.2 Route aus GPX-Datei (gewünscht)

Wegpunkte entlang eines GPX-Tracks verbinden statt per Luftlinie. Noch nicht spezifiziert.

Wird durch das Wanderungs-Widget (9.5) ersetzt und ist erledigt, sobald dieses umgesetzt ist. Die
Wegpunkte-Karte (6.6) selbst bekommt keine GPX-Route.

### 9.3 Panorama (zurückgestellt)

Vom Nutzer vorerst abgelehnt, bei Bedarf wieder aufgreifen: bildschirmfüllende Ansicht und „Speichern".
Ausdrücklich nicht gewünscht: quer gehaltene und senkrecht geschwenkte Panoramen, mehr als 8192 px Breite.

### 9.4 Mögliche weitere Punkte (nicht beauftragt)

- Grundfarbe pro Album wählbar
- Automatisierte Tests (siehe AGENTS.md)

### 9.5 Wanderungen aus GPX-Dateien (spezifiziert, Entscheidungen offen)

Eigener Abschnitt pro Wanderung mit Karte, Höhenprofil, Regler, Fotos und Halten, ein- oder mehrtägig.
Vollständig beschrieben in [WANDERUNG.md](WANDERUNG.md). Vor der Umsetzung sind die Fragen in deren
Abschnitt 14 zu klären.

Mit der Umsetzung bekommt die Tabelle `SYMBOLE` die Symbole `start`, `tasse`, `berg`, `bett`, `flagge`
und `kamera`.
Sie stehen dann auch den Stationen (6.4) zur Verfügung.

### 9.6 Bilder zentral, Widgets verweisen (entschieden, nicht umgesetzt)

Fotos werden einmal als `[[bild]]` definiert. Widgets verweisen über den Dateinamen darauf.

- Am `[[bild]]` steht nur, was zum Foto selbst gehört: `datei`, `unterschrift`, `datum`, `panorama`,
  `panorama_bildwinkel`. Neue Widgets fügen dort keine Schlüssel hinzu.
- Was nur in einem Widget gilt, steht am Verweis dieses Widgets. Ein Verweis darf `unterschrift` ersetzen.
- Verweis ist der Wert von `datei`, genau so geschrieben.
- Zuordnungen, die aus EXIF-Daten berechnet werden (z. B. Fotos zu einer Wanderung), schreibt `init` in die
  `album.toml`. Beim Bauen wird dafür kein EXIF ausgewertet. So kann man alles vor dem Bauen prüfen und ändern.

**Galerie (das Fotoraster):**

- Neue, optionale Tabelle `[galerie]` mit `bilder`: Inhalt und Reihenfolge des Rasters. Ein Eintrag ist ein
  Dateiname oder eine Tabelle mit `bild` und `unterschrift`:

  ```toml
  [galerie]
  bilder = [
    "IMG_1300.jpg",
    { bild = "IMG_1234.jpg", unterschrift = "Andere Unterschrift im Raster" },
  ]
  ```

- Fehlt `[galerie]`, zeigt das Raster alle `[[bild]]` in Dateireihenfolge, wie bisher (G6).
- `init` schreibt keine `[galerie]`.
- Der Fuß „N Fotos" und der Zähler der Großansicht zählen nur die Galerie.
- Aus dem Raster geöffnet, blättert die Großansicht in der Reihenfolge der Galerie. Aus einem anderen Widget
  geöffnet, in dessen Reihenfolge.

**Prüfungen beim Bauen:**

- Ein Verweis auf eine Datei, die es in `[[bild]]` nicht gibt, ist ein Fehler.
- Dasselbe Bild zweimal in `[galerie]` ist ein Fehler.
- Steht dieselbe `datei` mehrfach in `[[bild]]`, ist das nur dann ein Fehler, wenn ein Verweis darauf zeigt.
  Ohne Verweise bleibt es erlaubt wie bisher (G6).
- Ein `[[bild]]`, auf das nichts verweist, ergibt eine Warnung. Es wird nicht verarbeitet und nicht
  eingebettet. Das kann nur mit `[galerie]` passieren.

**Einbetten:**

- Jedes Bild wird einmal verarbeitet und einmal eingebettet, egal wie viele Widgets darauf verweisen.
- Die Vorschauen stecken wie bisher im `<img>` des Rasters. Widgets, die ohnehin nur mit JavaScript laufen
  (z. B. die Wanderung), holen sie sich von dort.
- Bilder, die nicht im Raster stehen, bekommen einen eigenen Datenblock.

**Bei der Umsetzung anzupassen:** Abschnitte 4, 5, 6.1 und 6.3 sowie README.md (Konfiguration und der Satz
zur Reihenfolge der `[[bild]]`-Blöcke).

### 9.7 Rumpfseite und Web Components (entschieden, nicht umgesetzt)

Die Seite wird aus einer Rumpfseite mit den Daten als JSON und Widgets als Web Components zusammengesetzt; nur
benutzte Widgets kommen in die Datei. Alle bisherigen Teile werden Web Components, G2 entfällt zugunsten von
G2′. Beschrieben in [ARCHITEKTUR.md](ARCHITEKTUR.md). Begonnen wird mit dem Panorama-Widget.
