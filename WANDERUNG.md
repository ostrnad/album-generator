# WANDERUNG – Das Wanderungs-Widget

**Stand: geplant, nicht umgesetzt.** Vor der Umsetzung müssen die Fragen in Abschnitt 14 beantwortet sein.

Dieses Dokument beschreibt, was das Widget tut und wie es aussieht. Es baut auf dem Grunddesign in
[DESIGN.md](DESIGN.md) auf und auf den Grundsätzen G1–G6 in [SPEC.md](SPEC.md). Vorlage für das Aussehen sind
die Entwürfe „Wanderung" und „Mehrtägig" im Design-Artefakt.

## 1. Zweck

Eine Wanderung erscheint im Album als eigener Abschnitt. Er zeigt eine Karte mit der Route, ein Höhenprofil,
die Fotos der Tour und die Halte unterwegs. Man kann die Tour mit einem Regler abgehen.

- Eine Tour dauert einen oder mehrere Tage. Ein Album kann mehrere Wanderungen enthalten.
- Alles steckt in der einen HTML-Datei, auch die Kartenkacheln. Das Widget funktioniert offline.
- Das Format ist neu. Es gibt keine älteren Wanderungs-Formate, die weiter gelten müssen.

## 2. Begriffe

| Begriff | Bedeutung |
|---|---|
| Wanderung | eine ganze Tour, ein Abschnitt im Album |
| Etappe | ein Tag der Tour, mit einer eigenen GPX-Datei; eine eintägige Tour hat genau eine |
| Halt | ein Ort an der Route mit Titel, Text und Symbol, z. B. Rast oder Gipfel |
| Eintrag | ein Foto oder ein Halt der Tour |
| Ansicht | bei mehrtägigen Touren „Gesamt" oder ein einzelner Tag |

## 3. Konfiguration

```toml
[[wanderung]]
titel = "Über den Grat zur Alpe"
zoom_stufen = [0, 2, 3]       # relativ zur Stufe, bei der die Route ganz ins Bild passt
grundkarte = true             # false = nur die Route, ohne Kartenkacheln
kachel_qualitaet = 70         # 30–95
eigene_kennzahlen = false     # true = Kennzahlen selbst berechnen statt aus Bergfex
kacheln = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"   # Kachelserver für den Bau
quelle = "© OpenStreetMap-Mitwirkende"                       # Quellenangabe auf der Karte

  [[wanderung.etappe]]        # eine pro Tag
  gpx = "tag1.gpx"
  titel = "Tag 1"
  datum = "2026-08-04"
  von = "Parkplatz"           # wird zum Start
  bis = "Berghütte"           # wird zur Übernachtung bzw. zum Ziel

  [[wanderung.halt]]
  etappe = 1
  km = 2.7                    # Position entlang der Etappe
  titel = "Rast"
  text = "Brotzeit mit Blick ins Tal"
  symbol = "tasse"

  [[wanderung.halt]]
  lat = 47.4123               # statt km: Koordinate, z. B. aus OpenStreetMap
  lon = 11.0456
  titel = "Gipfel"
  symbol = "berg"

  [[wanderung.foto]]          # Verweis auf ein [[bild]], schreibt init
  bild = "IMG_1234.jpg"       # Dateiname wie in [[bild]]
  etappe = 1
  km = 3.4                    # Position entlang der Etappe
  unterschrift = "Fast oben"  # optional, ersetzt die Unterschrift des Bildes

[[bild]]
datei = "IMG_1234.jpg"
unterschrift = "Letzter Anstieg vor dem Grat"
```

Die Fotos sind zentral als `[[bild]]` definiert. Die Wanderung verweist nur darauf (SPEC 9.6).

### 3.1 Schlüssel

`[[wanderung]]`

| Schlüssel | Standard | Regel |
|---|---|---|
| `titel` | – | Pflicht |
| `zoom_stufen` | `[0, 2, 3]` | genau drei ganze Zahlen ab 0, aufsteigend; relativ, siehe 7.1 |
| `grundkarte` | `true` | |
| `kachel_qualitaet` | `70` | 30–95 |
| `eigene_kennzahlen` | `false` | `true` = Kennzahlen selbst berechnen, auch wenn Bergfex-Werte da sind (4.3) |
| `kacheln` | OpenStreetMap | Adresse des Kachelservers mit `{z}`, `{x}`, `{y}` (4.5) |
| `quelle` | `"© OpenStreetMap-Mitwirkende"` | Quellenangabe auf der Karte |

`[[wanderung.etappe]]` – mindestens eine pro Wanderung

| Schlüssel | Standard | Regel |
|---|---|---|
| `gpx` | – | Pflicht; Pfad relativ zur `album.toml`; die Datei muss existieren und Punkte enthalten |
| `titel` | `"Tag n"` | |
| `datum` | kein Datum | Datum wie sonst in der `album.toml`; `init` schreibt es (3.3) |
| `von`, `bis` | – | optional |

`[[wanderung.halt]]`

| Schlüssel | Standard | Regel |
|---|---|---|
| `km` | – | Position entlang der Etappe; zwischen 0 und der Länge der Etappe |
| `lat`, `lon` | – | Position als Koordinate, z. B. aus OpenStreetMap kopiert; nur beide zusammen |
| `etappe` | `1` | die Etappe muss existieren; bei `lat`/`lon` optional, siehe unten |
| `titel`, `text` | – | eines von beiden muss gefüllt sein |

Ein Halt hat **entweder** `km` **oder** `lat`/`lon`, nie beides und nie keins.

Mit `lat`/`lon` sucht der Bau den nächsten Punkt der Route und nimmt dessen Etappe und km:

- Der Punkt muss höchstens 200 m von der Route entfernt sein (`HALT_ABSTAND_M`, Konstante), sonst Fehler.
- Ohne `etappe` wird in allen Etappen gesucht. Mit `etappe` nur in dieser. Das hilft, wenn die Route an
  derselben Stelle zweimal vorbeiführt.
- Sind zwei Routenpunkte gleich nah, gilt der frühere.
- Im Album steht danach nur Etappe und km, nicht die Koordinate.
| `symbol` | `punkt` | ein Name aus der gemeinsamen Tabelle `SYMBOLE` (Entscheidung 10) |

`[[wanderung.foto]]`

| Schlüssel | Standard | Regel |
|---|---|---|
| `bild` | – | Pflicht; ein `datei`-Wert aus `[[bild]]`; kein Panorama |
| `etappe` | `1` | die Etappe muss existieren; bei mehrtägigen Touren Pflicht |
| `km` | – | Pflicht; zwischen 0 und der Länge der Etappe |
| `unterschrift` | Unterschrift des Bildes | optional |

`[[bild]]` bekommt keine neuen Schlüssel.

### 3.2 Fehler

Diese Fälle brechen den Bau mit einer klaren Meldung ab, die sagt, was zu tun ist:

- unbekannter Schlüssel in `[[wanderung]]`, `[[wanderung.etappe]]`, `[[wanderung.halt]]` oder
  `[[wanderung.foto]]`
- ungültige Zoomstufen, fehlende oder leere GPX-Datei, unbekanntes Symbol
- `km` jenseits der Etappenlänge
- Halt mit `km` und `lat`/`lon` zugleich, mit keinem von beiden oder nur mit `lat` oder nur `lon`
- Halt mit `lat`/`lon` weiter als 200 m von der Route
- `[[wanderung.foto]]` ohne `etappe` bei einer mehrtägigen Tour
- Verweis auf ein Bild, das es nicht gibt, oder auf ein Panorama
- dasselbe Bild zweimal in derselben Wanderung

Unbekannte Schlüssel an `[[bild]]` bleiben erlaubt wie bisher (G6).

### 3.3 Was `init` schreibt

Die Zuordnung der Fotos passiert in `init`, nicht beim Bauen. So sieht und ändert man sie in der `album.toml`,
bevor die Seite entsteht.

- `init` sucht `.gpx`-Dateien im Ordner (nicht in Unterordnern, ohne versteckte Dateien).
- Wie die Dateien zu Wanderungen zusammengefasst werden: Abschnitt 3.4.
- Jede GPX-Datei wird eine Etappe. Reihenfolge: nach der ersten Zeit in der Datei, sonst nach Dateinamen.
- Je Etappe schreibt `init` `gpx`, `titel = "Tag n"` und `datum`. `von` und `bis` stehen auskommentiert da.
- `datum` kommt aus der ersten Zeitangabe der GPX-Datei, umgerechnet wie in 3.4. Hat die Datei keine
  Zeitangaben, nimmt `init` das Aufnahmedatum des ersten Fotos der Etappe (nach km) und schreibt einen
  Kommentar dazu, z. B. `datum = 2026-08-04   # aus Foto IMG_1234.jpg, nicht aus der GPX-Datei`. Gibt es
  auch kein Foto mit Datum, fehlt die Zeile.
- Beim Bauen wird ein fehlendes Datum nicht nachgeholt. Fehlt es, entfällt es an allen Stellen im Widget.
- Jedes Foto mit GPS kommt zum nächsten Routenpunkt aller Etappen, wenn er höchstens 200 m entfernt ist
  (`FOTO_ABSTAND_M`, eine Konstante wie `WEGPUNKT_RADIUS_KM`). Dafür schreibt `init` einen
  `[[wanderung.foto]]`-Block mit `bild`, `etappe` und `km` (auf 0,1 km gerundet).
- Fotos weiter weg, Fotos ohne GPS und Panoramen bekommen keinen Block.
- Die Blöcke stehen nach Etappe und km sortiert.
- Für Halte steht ein auskommentiertes Beispiel da.
- `init` schreibt keine `[galerie]`. Alle Fotos stehen also auch im Raster.

**Kachel-Schätzung:** Für jede Wanderung zählt `init`, wie viele Kacheln die Karte mit den Standard-Zoomstufen
braucht, und schätzt die Größe (Anzahl mal etwa 20 KB). Dafür wird nichts heruntergeladen; die Anzahl
ergibt sich aus der Route allein. `init` gibt beides aus und schreibt es als Kommentar an den
`[[wanderung]]`-Block, z. B. `# Karte: etwa 640 Kacheln, etwa 13 MB`. Ändert man danach `zoom_stufen`, stimmt
die Zahl nicht mehr; die genaue nennt der Bau.

Danach kann man Blöcke löschen, ändern oder von Hand ergänzen. Ein erneutes `init --force` überschreibt die
ganze Datei, wie bisher.

### 3.4 GPX-Dateien zu Wanderungen zusammenfassen

Das ist eine Automatik in `init`. Sie darf sich irren; das Ergebnis wird ohnehin von Hand geprüft und bei
Bedarf zusammengelegt oder getrennt.

- **Tag einer Datei:** der Kalendertag ihrer ersten Zeit, in geschätzter Ortszeit. Die Ortszeit ist UTC plus
  eine Stunde je 15 Grad östlicher Länge des ersten Punkts (westlich entsprechend minus). Fürs Datum reicht
  das, weil keine Wanderung um Mitternacht beginnt. Keine weitere Abhängigkeit.
- **Reihenfolge:** Die Dateien werden nach ihrer ersten Zeit sortiert. Jede wird mit der direkt davor
  verglichen.
- **Zusammenfassen:** Eine Datei wird die nächste Etappe der vorigen Wanderung, wenn
  - ihr Tag direkt auf den Tag der vorigen Datei folgt und
  - ihr Start höchstens 250 m vom Ziel der vorigen Datei entfernt liegt (`ETAPPEN_ABSTAND_M`, Konstante).
- **Ausnahme:** Sind beide Dateien Rundtouren, werden sie nicht zusammengefasst. Rundtour heißt: Start und
  Ziel liegen höchstens 250 m auseinander. Sonst würden Tagestouren ab derselben Unterkunft zu einer Tour.
  Eine Runde ab der Hütte mitten in einer Hüttentour stört nicht, weil der Tag davor und der Tag danach
  keine Rundtouren sind.
- Sonst beginnt mit der Datei eine neue Wanderung.
- Dateien ohne Zeitangaben werden je eine eigene Wanderung.
- Zwei Dateien am selben Tag werden nicht zusammengefasst. Eine Etappe ist genau eine GPX-Datei.

## 4. Aufbereitung beim Bauen

### 4.1 GPX lesen

- Gelesen werden Spuren (`trk`/`trkseg`/`trkpt`). Gibt es keine, dann Routen (`rte`/`rtept`).
- Höhe (`ele`) und Zeit (`time`) sind optional. Der XML-Namensraum spielt keine Rolle.
- Eine GPX-Datei ist immer genau eine Tour, auch wenn sie aus mehreren Spuren (`trk`) oder Stücken
  (`trkseg`) besteht. Das entsteht z. B., wenn die Aufzeichnung pausiert wurde.
- Alle Stücke werden in der Reihenfolge der Datei zu einer Route aneinandergehängt.
- Auf der Karte wird die Lücke zwischen zwei Stücken nicht mit einer Linie überbrückt. Sonst gibt es keinen
  Hinweis auf die Unterbrechung; Kilometer und Höhenprofil laufen einfach weiter.
- Die Strecke der eigenen Berechnung zählt die Lücke nicht mit.
- Für `init` (3.4) ist der Start der erste Punkt des ersten Stücks, das Ziel der letzte Punkt des letzten.

### 4.2 Route vereinfachen

- Jede Etappe wird auf höchstens etwa 1500 gleichmäßig verteilte Punkte gebracht, mit mindestens 10 m
  Abstand.
- Fehlende Höhen und Zeiten werden entlang der Strecke aus den Nachbarpunkten ergänzt.

### 4.3 Kennzahlen

Bergfex ist das übliche Werkzeug zum Aufzeichnen. Die Kennzahlen sollen mit denen in der Bergfex-Webanwendung
übereinstimmen. Deshalb gilt je Etappe:

- **Standard:** Strecke, Aufstieg, Abstieg, höchster Punkt und Dauer kommen aus den Bergfex-Angaben in der
  GPX-Datei (`TrackStatsExtension`). Sie werden unverändert übernommen.
- **Fehlen die Bergfex-Angaben** oder einzelne Werte darin, wird der fehlende Wert selbst berechnet (unten).
  Der Bau nennt die betroffenen Etappen.
- **`eigene_kennzahlen = true`:** Alle Werte werden selbst berechnet, auch wenn Bergfex-Angaben da sind.

Eigene Berechnung:

- **Strecke:** Summe der Abstände zwischen den ursprünglichen GPX-Punkten.
- **Aufstieg und Abstieg:** Höhe vorher auf etwa 40 m Strecke geglättet. Kleine Schwankungen unter 3 m
  zählen nicht.
- **Höchster Punkt.**
- **Dauer:** letzte minus erste Zeit. Ohne Zeitangaben gibt es keine Dauer.

Für die ganze Tour: Strecke, Aufstieg und Abstieg zusammengezählt, höchster Punkt ist das Maximum, Dauer ist
die Summe der Etappen (Nächte zählen nicht). Das gilt für beide Quellen.

Höhenprofil, Höhe am Cursor und Steigung kommen immer aus den Punkten der GPX-Datei. Sie können daher leicht
von den Bergfex-Kennzahlen abweichen, z. B. kann der höchste Punkt im Profil etwas anders sein.

Welche Felder die Bergfex-Angaben genau enthalten (Namen, Einheiten, ob die Dauer Pausen enthält), ist noch
an einer echten Bergfex-GPX-Datei festzustellen (Entscheidung 15).

### 4.4 Fotos der Tour

- Zur Tour gehören genau die Fotos aus `[[wanderung.foto]]`. Beim Bauen wird kein GPS ausgewertet.
- In der Tour stehen die Fotos nach Etappe und km sortiert.
- Ein Foto darf in mehreren Wanderungen vorkommen.
- Im Album steht nur die Position auf der Route (Etappe und km), nie eine GPS-Koordinate (G3).

### 4.5 Kartenkacheln

- Der Bau lädt die Kacheln vom Server in `kacheln` der jeweiligen Wanderung, Standard OpenStreetMap. Die
  Quellenangabe `quelle` steht sichtbar auf der Karte.
- Jede Wanderung hat ihre eigene Einstellung. Das Widget hängt nicht von `[karte]` ab und funktioniert auch,
  wenn das Album keine Karte hat. Eine Einstellung für die ganze Datei gibt es bewusst nicht.
- Die fertige Seite lädt keine Kacheln nach; alle stecken in der HTML-Datei (G1).
- Je Zoomstufe werden nur die Kacheln geladen, die die Route berührt, plus ein Ring von Kacheln drumherum.
- Jede Kachel steckt nur einmal pro Wanderung in der Datei. Sie wird als JPEG mit `kachel_qualitaet`
  gespeichert.
- Zwischenspeicher und Abruf wie bei der Karte (SPEC 6.6): `~/.cache/fotoalbum/kacheln`, eigener
  User-Agent, zwei Verbindungen.
- Es gibt keine Höchstzahl von Kacheln (Entscheidung 6). Der Bau nennt je Wanderung Anzahl und Größe der
  Kacheln.
- Mit `grundkarte = false` werden keine Kacheln geladen. Die Route liegt dann auf einer leichten Fläche.

## 5. Platz auf der Seite

- Jede Wanderung ist ein eigener Abschnitt, in der Reihenfolge der `album.toml`. Die Wanderungen stehen
  zwischen Karte und Fotoraster.
- Der Abschnitt ist einklappbar wie Stationen und Karte (SPEC 6.5): am Desktop offen, am Handy zu. Der Kopf ist
  eine Pille mit dem Titel der Wanderung.
- Der Inhalt liegt in einem Passepartout über die volle Breite (Rand 28 px, am Handy 12 px).

## 6. Aufbau

### 6.1 Desktop

Von oben nach unten:

1. Tag-Schalter mit Zeile darunter (nur mehrtägig, Abschnitt 11)
2. Kennzahlen in einer Reihe, mittig
3. Karte links, Detailspalte rechts (300 px breit)
4. Höhenprofil mit Regler, volle Breite
5. „Unterwegs"-Liste

### 6.2 Handy

Alles untereinander: Tag-Schalter, Kennzahlen in zwei Reihen, Karte im Format 5:4, Höhenprofil mit Regler,
Detailkarte, „Unterwegs"-Liste.

### 6.3 Kennzahlen

- Je Kennzahl ein Wert (20 px fett, am Handy 17 px) und darunter eine Beschriftung (13 px, gedämpft).
- Reihenfolge: Datum (nur mehrtägig), Strecke, Aufstieg, Abstieg, Höchster Punkt, Dauer.
- Schreibweise: `4,7 km`, `825 m`, `2.093 m`, `2:53 h`. Fehlt ein Wert, entfällt die Kennzahl.

## 7. Karte

### 7.1 Bedienung

- Drei feste Zoomstufen. Zoomen springt von Stufe zu Stufe.
- Die Stufen sind relativ. `0` ist die größte Kartenstufe, bei der die ganze Route der Ansicht ins Bild passt,
  am Desktop wie am Handy. `2` heißt: zwei Stufen näher heran. So passen eine lange Gesamttour und eine kurze
  Etappe gleich gut.
- Jede Ansicht (Gesamt, jeder Tag) hat ihre eigene Stufe `0`. Dadurch werden mehr Kacheln gebraucht (4.5).
- Keine Stufe geht über die größte Stufe der Kachelquelle hinaus (bei OpenStreetMap 18, wie bei der Karte).
- Knöpfe: Plus, Minus, „Alles zeigen". Es sind schwebende Knöpfe (44 px) oben rechts auf der Karte.
- Maus: Ziehen verschiebt, Doppelklick zoomt hinein, Strg/⌘ + Mausrad zoomt.
- Touch: zwei Finger verschieben und zoomen. Ein Finger scrollt die Seite.
- „Alles zeigen" kehrt zur ersten Stufe zurück, mit der ganzen Route der Ansicht im Bild.
- Verschieben geht nur so weit, wie Kacheln vorhanden sind.

### 7.2 Zeichnung

- Route: Orange, 3,5 px, mit weißem Rand.
- Anfang der Route: grüner Punkt. Ende: roter Punkt. Beide mit weißem Rand.
- Foto: Marke mit Kamera-Symbol. Halt: Marke mit seinem Symbol. Marken sind 30 px groß, in „Betont", mit
  weißem Rand.
- Der ausgewählte Eintrag bekommt einen orangen Ring.
- Die Cursor-Position des Reglers ist ein orangener Punkt auf der Route.
- Im Dunkelmodus wird nur das Kartenbild abgedunkelt. Route, Punkte und Marken bleiben gleich.

### 7.3 Foto-Fenster

- Ein Klick auf eine Foto-Marke öffnet ein kleines Fenster an der Marke. Es zeigt das Foto im Passepartout.
- Es hat Knöpfe für zurück, weiter und schließen.
- Ein Klick auf das Foto öffnet die Großansicht (Abschnitt 12).

## 8. Höhenprofil und Regler

### 8.1 Profil

- Das Profil zeigt die Höhe über der Strecke. Unten steht die Strecke in km, links die Höhe in m.
- Feine Rasterlinien, die Fläche unter der Linie leicht orange.

### 8.2 Leiste mit Einträgen

- Über dem Profil steht eine Leiste mit allen Einträgen an ihrer Position.
- Desktop, einzelner Tag: Fotos als kleine Passepartouts (50 px), Halte als Marke mit Namen darunter.
- Sonst (Handy, „Gesamt"): Fotos als Punkte, Halte als Marke.
- Ein Klick auf einen Eintrag wählt ihn aus.

### 8.3 Regler

- Unter dem Profil liegt eine Schiene. Der Teil bis zum Griff ist orange.
- Jeder Eintrag ist ein kleiner Punkt auf der Schiene.
- Der Griff ist 44 px groß, weiß, mit orangem Rand.
- Ziehen am Griff bewegt den Cursor im Profil und den Punkt auf der Karte mit.
- Unter dem Regler steht: Etappe (nur in „Gesamt"), km, Höhe und Steigung in Prozent. Die Steigung kommt aus
  der geglätteten Höhe.

### 8.4 Auswahl und freier Cursor

- Ist ein Eintrag ausgewählt, steht der Griff an seiner Stelle. Einen eigenen Cursor gibt es dann nicht.
- Wer den Griff zieht, hebt die Auswahl auf. Dann ist der freie Cursor zu sehen.
- **Startzustand:** Beim Öffnen und bei jedem Wechsel der Ansicht (Gesamt, Tag) ist der erste Eintrag der
  Ansicht ausgewählt. Das ist der Start, wenn die erste Etappe ein `von` hat; sonst das erste Foto oder der
  erste Halt. In der Ansicht eines späteren Tages ist es der erste Eintrag dieses Tages. Der Griff steht an
  seiner Stelle, Ring und Detail zeigen ihn.

## 9. Detail

- Desktop: Spalte rechts neben der Karte, auf einer leichten Fläche. Handy: Karte unter dem Profil.
- Oben eine kleine Zeile: Art des Eintrags, Etappe (nur in „Gesamt"), km und Höhe. Beispiel:
  `Foto · Tag 2 · 2,0 km · 1.933 m`.
- Foto: im quadratischen Passepartout, darunter die Unterschrift. Ein Klick öffnet die Großansicht.
- Halt: großes Symbol, Titel und Text.
- Unten: zurück, Zähler `n / m`, weiter. Gezählt werden die Einträge der aktuellen Ansicht.
- Blättern wählt den Eintrag aus und bewegt Regler und Karte mit.

## 10. „Unterwegs"-Liste

- Überschrift „Unterwegs", mittig, gedämpft.
- Aufbau wie die Zeitleiste der Stationen (SPEC 6.4): senkrechte Linie, Marke mit Symbol, darüber klein
  `km · Höhe`, darunter der Titel. Fotos zeigen rechts ein kleines Passepartout.
- Halte zeigen `Titel – Text`.
- Der ausgewählte Eintrag ist fett und hat einen orangen Ring um die Marke.
- Ein Klick auf einen Eintrag wählt ihn aus.
- Desktop, ein Tag: die Einträge in zwei Spalten. „Gesamt": je Etappe eine Spalte, nebeneinander, mit
  Überschrift `Tag n` und darunter `Datum · km`. Handy: alles untereinander.

## 11. Mehrtägige Touren

### 11.1 Tag-Schalter

- Eine Reihe von Knöpfen: `Gesamt | Tag 1 | Tag 2 | …`. Der gewählte ist gefüllt.
- Darunter eine Zeile, bei „Gesamt": `3 Tage · 28,4 km · Parkplatz → Talstation`. Bei einem Tag:
  `Titel · Datum · von → bis`.
- Bei eintägigen Touren gibt es keinen Schalter.

### 11.2 Ansicht „Gesamt"

- Die Etappen wechseln sich in drei Orangetönen ab. Jede hat eine Plakette `Tag n`.
- Fotos und einfache Halte sind auf der Karte nur kleine Punkte (10 px). Übernachtung, Gipfel und Ziel behalten
  ihr Symbol.
- Das Profil läuft durch alle Tage. Trennlinien zeigen die Tagesgrenzen. Die Tage liegen auf abwechselnd
  getönten Streifen, beschriftet mit `Tag n · km`.

### 11.3 Ansicht eines Tages

- Die gewählte Etappe ist orange. Die anderen sind gestrichelt und gedämpft.
- Profil, Kennzahlen, Detail und Liste zeigen nur diese Etappe.

### 11.4 Start, Übernachtung, Ziel

Diese Halte entstehen von selbst aus `von` und `bis`:

- `von` der ersten Etappe wird der Start (Symbol `start`).
- `bis` jeder Etappe außer der letzten wird eine Übernachtung (Symbol `bett`).
- `bis` der letzten Etappe wird das Ziel (Symbol `flagge`).
- `von` späterer Etappen erscheint nur in der Zeile unter dem Tag-Schalter.

## 12. Fotos, Raster und Großansicht

- Tour und Fotoraster sind unabhängig. Was im Raster steht, regelt `[galerie]` (SPEC 9.6). Ohne `[galerie]`
  stehen alle Fotos im Raster, auch die der Tour.
- Ein Foto nur in der Tour zeigen: in `[galerie]` weglassen.
- Unterschrift in der Tour: die vom Verweis, sonst die vom Bild.
- Aus der Tour geöffnet, blättert die Großansicht durch die Fotos der Tour in ihrer Reihenfolge.
- Jedes Foto steckt nur einmal in der Datei. Die Tour nutzt die Vorschauen aus dem Raster. Fotos, die nicht im
  Raster stehen, bekommen einen eigenen Datenblock (SPEC 9.6).

## 13. Allgemeines

### 13.1 Ohne JavaScript

Zu sehen sind nur der Abschnittskopf und die Kennzahlen der Wanderung. Karte, Profil, Detail und Liste
erscheinen erst mit JavaScript.

### 13.2 Hell und Dunkel

Farben, Schrift und Schatten wie im übrigen Album (DESIGN.md). Orange, Grün und Rot sind in beiden Modi gleich.
Im Dunkeln wird nur das Kartenbild abgedunkelt.

### 13.3 Abgrenzung

- Stationen (SPEC 6.4) und Wegpunkte (SPEC 6.6) bleiben eigene Dinge. Sie haben keine Verbindung zu Wanderungen
  und Halten.
- Ein Halt heißt in der Oberfläche nie „Station".
- Eine Diashow ist ein eigenes Thema und hier nicht beschrieben.

### 13.4 Grundsätze

- **G1:** Kacheln, Route und Fotos stecken in der Datei.
- **G3:** Es werden nur Etappe und km ausgegeben, keine Foto-Koordinaten. Die Route selbst ist bewusst
  konfiguriert, wie die Wegpunkte.
- **G6:** Alle neuen Schlüssel sind optional, `[[bild]]` bekommt keine neuen. Ohne `[[wanderung]]` bleibt
  jedes Album wie bisher.
- **Dateigröße:** Kacheln machen die Datei deutlich größer. Der Bau nennt die Größe.

## 14. Offene Entscheidungen

Vor der Umsetzung mit dem Nutzer zu klären. Fragen 1–8 stammen vom Nutzer, 9–15 sind beim Ausarbeiten
dazugekommen.

1. **Kennzahlen:** *Entschieden:* aus Bergfex, Schalter `eigene_kennzahlen` (Standard aus), siehe 4.3.
2. **Eintägige Touren:** *Entschieden:* immer mit genau einer `[[wanderung.etappe]]`. Eine Kurzform `gpx` direkt
   an `[[wanderung]]` gibt es nicht; dort ist `gpx` ein unbekannter Schlüssel und damit ein Fehler (3.2).
3. **Zoomstufen:** *Entschieden:* relativ zur Stufe, bei der die Route ganz ins Bild passt, je Ansicht. Siehe 7.1.
4. **Position eines Halts:** *Entschieden:* entweder `km` oder `lat`/`lon`, nicht beides. Siehe 3.1.
5. **Mehrere Spuren in einer GPX:** *Entschieden:* aneinanderhängen, Lücken auf der Karte nicht verbinden. Siehe 4.1.
6. **Höchstzahl Kacheln:** *Entschieden:* vorerst keine Höchstzahl. `init` schätzt Anzahl und Größe (3.3), der
   Bau nennt die genauen Werte (4.5).
7. **Datum einer Etappe:** *Entschieden:* `init` schreibt es aus der GPX-Zeit, sonst aus dem ersten Foto mit
   Kommentar. Der Bau holt nichts nach. Siehe 3.3.
8. **Symbole:** *Entschieden:* feste Liste im Programm (`SYMBOLE`). Alle Symbole der Liste sind erlaubt, auch `kamera`.
   Eigene Symbole über die `album.toml` (z. B. als SVG) gibt es nicht. Ein unbekannter Name ist ein Fehler, der
   die verfügbaren Namen nennt. Neue Symbole kommen per Änderung am Programm dazu.
9. **Symbol des Starts und Standard-Symbol eines Halts:** *Entschieden:* Der Start bekommt ein neues Symbol
   `start`, einen Kreis mit Punkt in der Mitte. Ein Halt ohne `symbol` bekommt `punkt`, wie eine Station.
10. **Gemeinsame Symbol-Tabelle:** *Entschieden:* Halte und Stationen nutzen dieselbe Tabelle `SYMBOLE` mit
    `punkt`, `start`, `haus`, `tasse`, `berg`, `bett`, `flagge`, `kamera`. Stationen bekommen damit die neuen Symbole
    dazu; ihr Standard bleibt `punkt` (G6).
11. **Startzustand:** *Entschieden:* der erste Eintrag der Ansicht ist ausgewählt, meist der Start. Siehe 8.4.
12. **Kachelquelle:** *Entschieden:* je Wanderung eigene Schlüssel `kacheln` und `quelle`, unabhängig von
    `[karte]`. Siehe 4.5.
13. **Name aus der GPX** (`trk/name`, `metadata/name`): wofür? Empfehlung: nicht verwenden, da Titel in der
    `album.toml` stehen.

14. **GPX-Dateien zu Wanderungen zusammenfassen:** *Entschieden*, siehe Abschnitt 3.4.

15. **Felder der Bergfex-Angaben:** Dafür wird eine echte, von Bergfex exportierte GPX-Datei gebraucht.
    Daran wird festgelegt, welches Feld welche Kennzahl liefert. Ohne Beispieldatei lässt sich 4.3 nicht
    umsetzen. Der Nutzer legt die Datei später ins Repository. Bis dahin wird das Widget nicht umgesetzt.

**Für später vorgemerkt:** Andere Wege, an die Kacheln zu kommen, als jede einzeln vom OpenStreetMap-Server
zu laden. Grund: Dateigröße und die Nutzungsregeln von OpenStreetMap, die massenhaftes Herunterladen
verbieten. Dazu gehört auch die Möglichkeit, die Kacheln in einem Verzeichnis neben der HTML-Datei abzulegen
statt sie einzubetten (vgl. SPEC 9.1). Noch nicht beauftragt.

Außerdem ist zu klären, ob SPEC 9.2 („Route aus GPX-Datei" für die Wegpunkte-Karte) mit diesem Widget erledigt
ist.

## 15. Prüfen

Zusätzlich zu den Prüfungen in AGENTS.md:

- Testdaten: eine echte Bergfex-GPX-Datei; künstliche GPX-Dateien mit und ohne Höhe und Zeit, eine mit zwei Spuren, eine nur mit `rte`.
  Fotos mit GPS nahe der Route und weit weg.
- Kacheln von einem lokalen Testserver (per `kacheln` an der Wanderung), nicht von OpenStreetMap.
- Eintägig und mehrtägig, jeweils Desktop und Handy, hell und dunkel, und ohne JavaScript.
- Regler, Blättern, Tag-Schalter, Zoom per Knopf, Mausrad und zwei Fingern, Foto-Fenster, Großansicht aus der
  Tour.
- `init` mit GPX-Dateien und Fotos mit GPS: Blöcke, Etappen und km stimmen; Fotos weiter als 200 m weg
  fehlen.
- `[galerie]` ohne ein Tour-Foto: Foto fehlt im Raster, ist in der Tour da und nur einmal in der Datei.
