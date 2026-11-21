# ARCHITEKTUR – Rumpfseite und Web Components

**Stand: beschrieben, nicht umgesetzt.** Die Entscheidungen stehen in Abschnitt 2, ihre Herleitung in
Abschnitt 8. Was erst bei der Umsetzung festgelegt wird, steht in 8.10. Zum Vorgehen siehe Abschnitt 10.

Dieses Dokument beschreibt, wie die erzeugte Seite künftig aufgebaut ist und wie der Bau sie zusammensetzt.
Was die einzelnen Teile tun und wie sie aussehen, steht weiter in [SPEC.md](SPEC.md), [WANDERUNG.md](WANDERUNG.md)
und [DESIGN.md](DESIGN.md).

## 1. Idee

Heute erzeugt `fotoalbum.py` jedes Teil der Seite als HTML-Schnipsel und hängt ein gemeinsames CSS und
JavaScript an. Künftig besteht die Seite aus zwei Dingen:

- einer **Rumpfseite**, die den Rahmen bildet und die Daten des Albums als JSON enthält, und
- **Widgets**, die als Web Components gebaut sind und diese Daten darstellen.

Der Bau setzt beides zu **einer** HTML-Datei zusammen, in der alles eingebettet ist (G1 bleibt).

## 2. Entschieden

- **Rumpfseite plus Widgets:** Die Rumpfseite bindet die Widgets ein. Der Bau fügt Rumpfseite und die
  benötigten Web Components zu einer Datei zusammen.
- **Nur verwendete Widgets:** In die Datei kommen nur die Widgets, die die `album.toml` tatsächlich benutzt.
- **Daten als JSON:** Die Rumpfseite enthält die Daten des Albums als JSON. Die Web Components lesen sie als
  Eingabe und rendern daraus ihre Darstellung.
- **Eingabe nur als JSON im Element:** Ein Widget bekommt seine Daten ausschließlich als JSON in seinem
  Element (z. B. `<script type="application/json">` als Kind). Die Daten des Albums sind also auf die
  Widget-Elemente der Rumpfseite verteilt. Nachladen per Adresse (`src="…"`) gibt es nicht, auch nicht auf
  fremden Seiten.
- **Keine Kacheln vom Server:** Auch auf fremden Seiten lädt ein Widget keine Kacheln nach; sie stecken in
  seinen Daten (G1 gilt auch für isoliert eingebundene Widgets).
- **Shadow DOM:** Jede Component kapselt ihre Darstellung im Shadow DOM. Farben kommen über CSS-Variablen
  hinein, so dass Hell/Dunkel von außen gesteuert wird.
- **Schrift von außen festlegbar:** Jedes Widget bietet eine Schnittstelle, über die man von außen die Schrift
  festlegt. Im Album nehmen die Widgets standardmäßig die eingebettete Schrift der Rumpfseite.
- **Python rechnet, die Components formatieren und stellen dar** (Abschnitt 5).
- **Eigene Dateien, kein Build-Werkzeug:** Jede Component liegt als reines JavaScript in einem eigenen
  Verzeichnis im Repository (Abschnitt 5.1). Kein npm, kein Bundler, kein TypeScript. `fotoalbum.py` fügt
  die Dateien beim Bau zusammen.
- **Testdaten je Component:** Zu jeder Component liegen ihre Testdaten im Repository, in ihrem Verzeichnis.
  Sie sind rein synthetisch (Abschnitt 7).
- **Aussehen bleibt:** Nach dem Umbau sehen die bestehenden Teile aus wie bisher. Die heutige Seite dient
  als Vergleich.
- **Components bauen auf der Grundansicht auf:** Raster und Großansicht übernehmen das HTML, das der Bau für
  die Grundansicht schreibt (Bilder, Texte, Reihenfolge), statt es aus dem JSON neu zu erzeugen.
- **Alle Teile außer dem Rumpf werden Web Components:** Alle bisherigen Teile des Albums werden durch Web
  Components ersetzt, bis auf das, was im Rumpf bleibt. Was es heute gibt, steht in Abschnitt 4.
- **Im Rumpf bleiben** Schrift, Hell/Dunkel (Farben und Umschalter), Kopf und Fuß. Sie werden keine eigenen
  Widgets.
- **Die Großansicht ist eine eigene Component.** Andere Widgets (Raster, Wanderung, …) rufen sie auf.
- **Widgets reden über Ereignisse miteinander** (Abschnitt 3.3), nicht über direkte Aufrufe.
- **Bilddaten stehen im HTML der Grundansicht, das JSON verweist darauf** (Abschnitt 3.4). Das gilt auch
  für Bilder, die nicht im Raster vorkommen.
- **Die Wanderung ist von Anfang an eine Web Component.** Sie soll so gebaut sein, dass man sie auch
  isoliert auf einer beliebigen anderen Website einbinden kann.
- **G2 entfällt.** Die Seite muss ohne JavaScript nicht mehr vollständig nutzbar sein. An die Stelle von G2
  tritt:
  - **G2′ – Grundansicht ohne JavaScript:** Ohne JavaScript zeigt die Seite nur
    - Kopf und Fuß (Titel, Unterzeile, Datum, „N Fotos"),
    - einen Hinweis, dass JavaScript abgeschaltet ist (Abschnitt 3.2),
    - das Fotoraster mit allen Fotos der Galerie (SPEC 9.6) samt Unterschriften und
    - eine einfache Großansicht: Ein Klick auf ein Foto öffnet es groß (Abschnitt 3.1).

    Panoramen stehen ohne JavaScript als gewöhnliches Foto im Raster (flacher Streifen), öffnen aber keine
    Großansicht. Alle anderen Widgets (Stationen, Karte, Panorama-Widget, Wanderung) zeigen ohne JavaScript
    nichts. Hell/Dunkel folgt ohne JavaScript der Systemeinstellung.
- **G6 gilt weiter:** Der Umbau ändert nichts an der `album.toml`. Jede bisher gültige Konfiguration baut
  weiter und zeigt dieselben Inhalte.

## 3. Zusammenspiel

```
album.toml ──► fotoalbum.py ──────────────────────────────► album.html
               │ prüft die Konfiguration                    ┌──────────────────────────────┐
               │ verarbeitet Bilder, Kacheln, GPX ...       │ Rumpf: Schrift, Hell/Dunkel,  │
               │                                            │   Kopf, Fuß                   │
               │ erzeugt die Daten als JSON          ──────►│ Daten (JSON)                  │
               │ erzeugt Kopf, Fuß, Raster und        ──────►│ Grundansicht als HTML         │
               │   Großansicht als fertiges HTML             │   (Kopf, Fuß, Raster, Bilder) │
               └ wählt die benutzten Web Components  ──────►│ Code der benutzten Components │
                                                            └──────────────────────────────┘
```

Folgerung aus G2′: Ohne JavaScript läuft keine Web Component. Die Grundansicht (Kopf, Fuß, Raster,
Großansicht) muss deshalb der Bau als fertiges HTML schreiben. Läuft JavaScript, übernehmen die Components;
alle übrigen Widgets rendern nur aus dem JSON und brauchen keine Darstellung aus Python.

### 3.1 Großansicht ohne JavaScript

Das geht mit reinem HTML/CSS über die CSS-Pseudoklasse `:target`:

- Jedes Foto im Raster ist ein Link auf `#gross-N`. Zu jedem Foto gibt es ein Element `id="gross-N"`, das
  normal unsichtbar ist und mit `:target` bildschirmfüllend erscheint (`position: fixed`).
- Darin: das große Bild, ein Schließen-Link zurück auf das Foto im Raster (`#foto-N`) und Blätter-Links auf
  `#gross-N-1` und `#gross-N+1`.
- Panoramen sind kein Link und haben kein `gross-N`; das Blättern überspringt sie (wie SPEC 6.7).
- Das große Bild steht als `<img loading="lazy">` mit Data-URL darin. Unsichtbare Lazy-Bilder lädt und
  dekodiert der Browser erst beim Öffnen. Die Großansicht-Component mit JavaScript nimmt das Bild von dort;
  es wird also nicht zusätzlich im JSON eingebettet (siehe 3.4).

Ausprobiert mit einem Prototyp in Chrome (Playwright, JavaScript abgeschaltet): öffnen, blättern und
schließen funktionieren, die Seite springt beim Öffnen nicht. Nicht geprüft: Safari, Firefox, echte
Mobilgeräte, Speicherbedarf mit 36 großen Bildern.

Grenzen gegenüber der Großansicht mit JavaScript:

- Kein Wischen, keine Pfeiltasten, kein Esc, kein Einpassen per Skript (nur `max-width`/`max-height`).
- Jedes Öffnen und Blättern ist ein Eintrag im Verlauf: Die Zurück-Taste blättert zurück, statt zu schließen.
- Beim Schließen springt das Foto an den oberen Fensterrand (per `scroll-margin` milderbar).
- Kein Knopf „Speichern"; ein eigener Download-Link würde das große Bild ein zweites Mal einbetten. Speichern
  geht über das Kontextmenü des Browsers.

### 3.2 Hinweis ohne JavaScript

- Ein `<noscript>`-Block unter dem Kopf sagt, dass JavaScript abgeschaltet ist und deshalb nur die Fotos zu
  sehen sind; mit JavaScript erscheinen auch die übrigen Teile (Karte, Stationen, Wanderung usw.).
- Der Hinweis erscheint nur, wenn das Album Widgets enthält, die ohne JavaScript fehlen (Stationen, Karte,
  Wanderung …). Ein Album, das nur aus Fotos besteht, zeigt ihn nicht (Entscheidung des Nutzers).
- Panoramen zählen als Fotos: Sie stehen ohne JavaScript als flacher Streifen im Raster, lösen den Hinweis
  also allein nicht aus (Entscheidung des Nutzers).
- Wortlaut und Aussehen (nach DESIGN.md) sind bei der Umsetzung festzulegen.


### 3.3 Ereignisse zwischen den Widgets

- Widgets und Rumpf rufen einander nicht direkt auf. Sie lösen Ereignisse (`CustomEvent`) aus und hören auf
  Ereignisse anderer.
- Beispiel: Das Raster löst „Großansicht öffnen" aus und gibt mit, welche Bilder in welcher Reihenfolge
  durchblättert werden und mit welchem es beginnt (SPEC 9.6: Reihenfolge des aufrufenden Widgets). Die
  Großansicht hört darauf und öffnet sich.
- Auch der Hell/Dunkel-Umschalter in der Großansicht (SPEC 6.2) wird so angebunden: Die Großansicht löst
  „Thema umschalten" aus, der Rumpf schaltet um.
- Offen bei der Umsetzung: Namen der Ereignisse, ihre Daten, und ob sie am `document` oder am auslösenden
  Element ausgelöst werden (sie müssen auch aus einem Shadow DOM herauskommen, also `bubbles` und
  `composed`). Die Ereignisse gehören zur Schnittstelle eines Widgets und werden mit ihm beschrieben.
- Folge für fremde Seiten: Eine isoliert eingebundene Wanderung braucht die Großansicht-Component mit. Ohne
  sie hat „Großansicht öffnen" keinen Empfänger.

### 3.4 Bilddaten

- Jedes Bild ist genau einmal eingebettet, und zwar im HTML der Grundansicht:
  - Vorschauen im `<img>` des Rasters,
  - große Bilder im `<img loading="lazy">` der Großansicht ohne JavaScript (3.1),
  - Bilder, die nicht im Raster vorkommen (z. B. nur in einer Wanderung, SPEC 9.6), ebenfalls im HTML,
    aber ohne JavaScript unsichtbar und nicht geladen. Vorschlag: in einem `<template>`-Element; dessen
    Inhalt lädt der Browser nicht, JavaScript kann ihn aber lesen.
- Das JSON eines Widgets nennt die Bilder, die es zeigt, mit Unterschrift, Datum und Maßen und verweist per
  Kennung auf die Bilddaten im HTML (z. B. die `id` eines `<img>`). Eine zentrale Bildtabelle für alle Widgets
  gibt es nicht, weil jedes Widget nur sein eigenes JSON liest (Abschnitt 2). Die Großansicht bekommt die
  Kennungen mit dem Ereignis „Großansicht öffnen" (3.3).
- Auf einer fremden Seite gibt es diese Grundansicht nicht. Da ein Widget nichts nachlädt (Abschnitt 2),
  müssen seine Bilder dort im Element selbst stecken, etwa als `<img>` oder `<template>` neben dem JSON.
  Die genaue Form ist bei der Umsetzung festzulegen.

## 4. Die Widgets

Bisherige Teile und was aus ihnen wird:

| Teil | SPEC | Künftig | Ohne JavaScript heute | Ohne JavaScript künftig (G2′) |
|---|---|---|---|---|
| Kopf und Fuß | 6.1 | Rumpf | vollständig | vollständig, dazu Hinweis auf fehlendes JavaScript (3.2) |
| Hell/Dunkel samt Umschalter | 6.2 | Rumpf | Systemeinstellung, kein Umschalter | Systemeinstellung, kein Umschalter |
| Schrift | 6.1 | Rumpf | vorhanden | vorhanden |
| Fotoraster | 6.1 | Component | vollständig | vollständig, alle Fotos der Galerie |
| Großansicht | 6.3 | Component | nicht vorhanden | einfach, per `:target` (3.1) |
| Stationen | 6.4, 6.5 | Component | vollständig, einklappbar | nichts |
| Karte mit Wegpunkten | 6.5, 6.6 | Component | vollständig, einklappbar | nichts |
| Panorama | 6.7 | Component | flacher Streifen | gewöhnliches Foto im Raster, ohne Großansicht |
| Wanderung (geplant) | WANDERUNG.md | Component | Abschnittskopf und Kennzahlen (WANDERUNG 13.1) | nichts |

## 5. Bau

- **Python rechnet:** `fotoalbum.py` führt alle Berechnungen durch und legt die vereinfachten bzw.
  errechneten Daten als JSON ab. Dazu gehören: Konfiguration prüfen, Bilder verarbeiten, Kacheln laden und
  ihre Lage bestimmen, GPX lesen und vereinfachen, Kennzahlen, km-Position von Halten und Fotos, Zoomstufen,
  Lage der Markierungen auf der Karte.
- **Die Components rechnen nur, was von der Bedienung abhängt,** z. B. Höhe und Steigung am Cursor oder den
  Kartenausschnitt beim Zoomen.
- **Die Components formatieren:** Das JSON enthält Rohwerte in festen Einheiten (Vorschlag: Meter, Sekunden,
  Datum als ISO-Text `2026-06-14`, Koordinaten in Grad). Wie sie angezeigt werden („8,1 km", „2:44 h",
  „14. Juni 2026"), legt die jeweilige Component bei der Darstellung fest.
- **Ausnahme Grundansicht:** Kopf und Fuß (Rumpf) sowie Raster und Großansicht ohne JavaScript erzeugt der Bau
  als fertiges HTML (Abschnitt 3); Texte darin, etwa Daten, formatiert also Python. Das Raster übernimmt sie
  von dort (Abschnitt 2). Datumsformatierung gibt es damit zweimal, in Python und in JavaScript; beide folgen
  SPEC 4 (`12. Juli 2026`, verkürzte Zeiträume) und sollten in den Tests gegeneinander geprüft werden.
- Folge für fremde Seiten: Das JSON eines Widgets erzeugt immer `fotoalbum.py`. Rohe Daten wie eine
  GPX-Datei kann man einem Widget nicht direkt geben.
- Der Bau ermittelt aus der `album.toml`, welche Widgets gebraucht werden, und bettet nur deren Code ein.
- Die großen Base64-Blöcke werden weiter direkt in die Datei geschrieben, nicht erst im Speicher
  zusammengesetzt.

### 5.1 Dateien im Repository

Vorschlag für den Aufbau:

```
fotoalbum.py                 Bau: rechnet, schreibt Rumpf und Grundansicht, fügt Components ein
widgets/
  grossansicht/
    grossansicht.js          die Component (reines JavaScript, mit ihrem CSS)
    testdaten/               synthetische Testdaten dieser Component
  raster/
  stationen/
  karte/
  panorama/
  wanderung/
```

- Der Bau liest die Dateien der benutzten Components und schreibt ihren Inhalt in die HTML-Datei (G1).
- Jede Datei läuft auch ungebaut direkt im Browser, z. B. in ihrer Testseite.
- Folge: `fotoalbum.py` allein reicht nicht mehr, man braucht das Verzeichnis `widgets/` daneben. Ob Rumpf
  und Schrift ebenfalls eigene Dateien werden, ist bei der Umsetzung festzulegen.

## 6. Widgets außerhalb des Albums

Am Beispiel der Wanderung: Die Component soll ohne den Rest des Albums auf einer fremden Seite laufen. Daraus
folgt:

- Sie bringt alles mit, was sie selbst braucht, und hängt nicht von CSS oder JavaScript der Rumpfseite ab.
- Ihre Eingabe ist ein festgelegtes, dokumentiertes Datenformat. Dieses Format ist eine Schnittstelle und
  braucht eine Versionsangabe.
- **Daten und Kacheln** stecken als JSON im Element; nachgeladen wird nichts (Abschnitt 2). Bilder siehe 3.4.
- **Aussehen:** Shadow DOM; Farben über CSS-Variablen, Hell/Dunkel steuert die einbindende Seite.
- **Schrift:** über die Schnittstelle des Widgets von außen festlegbar. Im Album ist es die eingebettete
  Schrift der Rumpfseite. Auf einer fremden Seite ohne eigene Festlegung erbt das Widget deren Schrift.
  (Technischer Hinweis: Eine im Dokument per `@font-face` eingebettete Schrift ist auch im Shadow DOM
  verfügbar; die Schnittstelle kann daher eine CSS-Variable sein, z. B. für `font-family`.)
- **Großansicht:** muss mit eingebunden werden (3.3).

## 7. Tests

Die Aufteilung in Widgets ist auch die Aufteilung der Tests:

- Jedes Widget bekommt einen eigenen Satz Testdaten, die nur dieses Widget betreffen. Sie liegen im
  Repository im Verzeichnis der Component (5.1) und sind rein synthetisch: erzeugte Bilder, Kacheln,
  GPX-Dateien. Echte Fotos oder Touren gehören nicht dazu.
- **Ausnahme Referenz:** Die echte Bergfex-Tour `tests/widgets/wanderung/Natz_-_Schabs_Apfelweg.gpx` bleibt
  im Repository. Sie dient als Referenz für den Aufbau einer Bergfex-Datei und die Kennzahlen (WANDERUNG
  4.3). Für weitere Fälle (mehrere Spuren, mehrere Stücke, ohne Höhe oder Zeit, nur `rte`, mehrtägig) kommen
  synthetische Tracks dazu. Bei der Umsetzung der Wanderung zieht die Datei in deren Verzeichnis um.
- **Eingecheckt oder erzeugt:** Grundsätzlich werden die Testdaten als fertige Dateien eingecheckt. Lassen
  sie sich mit wenig Aufwand deterministisch erzeugen, darf stattdessen ein Skript im Verzeichnis der
  Component sie erzeugen. Deterministisch heißt: gleicher Inhalt bei jedem Lauf, ohne Zufall und ohne Netz.
  (Byte-gleiche JPEGs über verschiedene Pillow-Versionen sind damit nicht gemeint.)
- Jedes Widget bekommt eine Testseite (Harness), die das Widget isoliert einbindet und seine Testfälle zeigt:
  hell und dunkel, Handy- und Desktopbreite, ohne JavaScript.
- Die Testseiten werden über GitHub Pages veröffentlicht, auch von Feature-Branches, und zwar so, dass
  mehrere Branches gleichzeitig ihre eigenen Testseiten haben.

### 7.1 Testseite

- Eine Testseite je Component, im Verzeichnis der Component. Sie zeigt alle Testfälle untereinander.
- Ein Umschalter für hell und dunkel.
- Jeder Testfall in festen Breiten (Handy und Desktop) per `<iframe>`.
- Eine Ansicht ohne JavaScript per `<iframe sandbox>` ohne `allow-scripts`; so lässt sie sich auch auf
  Geräten prüfen, auf denen man JavaScript nicht abschalten kann.

### 7.2 GitHub Pages

- Ein Branch `gh-pages` mit einem Ordner pro Branch, z. B. `…github.io/album-generator/<branch>/panorama/`.
  Schrägstriche im Branchnamen werden zu Bindestrichen.
- Ein Workflow baut bei jedem Push auf einen beliebigen Branch die Testseiten und ersetzt nur den Ordner
  dieses Branches. Schreibvorgänge auf `gh-pages` laufen nacheinander, damit sich parallele Läufe nicht
  überschreiben.
- Wird ein Branch gelöscht, entfernt ein zweiter Workflow seinen Ordner.
- Eine Startseite listet alle Branches und ihre Testseiten.
- Kacheln kommen aus den synthetischen Testdaten, nicht von OpenStreetMap.
- Der Nutzer stellt Pages einmalig in den Einstellungen des Repositorys auf den Branch `gh-pages`.
- Die Seiten sind öffentlich. Das betrifft auch die echte Bergfex-Tour, sobald die Wanderung eine Testseite
  hat.

## 8. Entscheidungen im Einzelnen

Alle Fragen dieses Abschnitts sind entschieden. Er bleibt stehen, damit nachvollziehbar ist, was wann
gefragt war.

### 8.1 Rumpf und Zuschnitt der Widgets

*Entschieden:* Rumpf mit Schrift, Hell/Dunkel, Kopf und Fuß; Großansicht als eigene Component; Ereignisse
zwischen den Widgets. Siehe 2 und 3.3.

### 8.2 Bilder

*Entschieden:* Bilddaten im HTML der Grundansicht, auch die, die nicht im Raster vorkommen; das JSON verweist
darauf. Siehe 2 und 3.4.

### 8.3 Grundansicht erzeugen

*Entschieden:* Die Components bauen auf dem HTML der Grundansicht auf. Panoramen ohne JavaScript als
gewöhnliches Foto im Raster, ohne Großansicht; „alle Fotos" heißt alle Fotos der Galerie; der Hinweis ohne
JavaScript erscheint nur, wenn das Album mehr als Fotos enthält. Siehe 2, 3.1, 3.2. Panoramen zählen dabei als Fotos (3.2).

### 8.4 Widgets auf fremden Seiten

*Entschieden:* Daten nur als JSON im Element, kein Nachladen; keine Kacheln vom Server; Shadow DOM mit Farben
über CSS-Variablen; Schrift von außen festlegbar, im Album die eingebettete Schrift. Siehe 2 und 6.

### 8.5 Arbeitsteilung

*Entschieden:* Python rechnet und legt die errechneten Daten als JSON ab; die Components formatieren bei der
Darstellung. Siehe 5. Bei der Umsetzung festzulegen: die Einheiten und Formate der Rohwerte im JSON.

### 8.6 Dateien und Werkzeuge

*Entschieden:* eigene Verzeichnisse, reines JavaScript ohne Build-Werkzeuge, `fotoalbum.py` fügt zusammen.
Siehe 2 und 5.1.

### 8.7 Tests und GitHub Pages

*Entschieden:* Testdaten je Component, synthetisch, eingecheckt oder deterministisch erzeugt; Bergfex-Tour
bleibt als Referenz; Testseite und Pages wie vorgeschlagen. Siehe 7.

### 8.8 Umbau und Reihenfolge

*Entschieden:* Die bestehenden Teile sehen nach dem Umbau aus wie bisher. Die Architektur wird zuerst am
Panorama-Widget eingeführt.

### 8.9 Hinweis ohne JavaScript bei Panoramen

*Entschieden:* Panoramen zählen als Fotos und lösen den Hinweis allein nicht aus (3.2).

### 8.10 Bei der Umsetzung festzulegen

Keine Grundsatzfragen mehr, sondern Einzelheiten, die mit dem jeweiligen Widget entschieden werden:

- Namen und Daten der Ereignisse (3.3)
- Aufbau des JSON je Widget samt Versionsangabe, Einheiten und Formate der Rohwerte (5, 6)
- Form der Bilder im Element auf fremden Seiten (3.4)
- Name und Art der Schnittstelle für die Schrift (6)
- ob Rumpf und Schrift eigene Dateien werden (5.1)
- Wortlaut und Aussehen des Hinweises ohne JavaScript (3.2)

## 9. Bei der Umsetzung anzupassen

- SPEC.md: Grundsatz G2 durch G2′ ersetzen, Abschnitt 6.3 um die Großansicht ohne JavaScript ergänzen.
  Abschnitt 6.5 und 7 („Einklappen per Checkbox"): Der Grund dafür war G2; Stationen und Karte brauchen
  künftig JavaScript, das Einklappen kann also per Skript geschehen.
- AGENTS.md: Aufbau von `fotoalbum.py`, Regel 2, Prüfen.
- WANDERUNG.md: 13.1 widerspricht G2′ (dort Abschnittskopf und Kennzahlen ohne JavaScript, künftig nichts);
  13.1 und 13.4 an G2′ und die Component anpassen.
- README.md: Voraussetzungen und Aufbau; das Werkzeug besteht künftig aus `fotoalbum.py` und `widgets/`.
- SPEC.md 9.6: Die dort beschriebene Einbettung (Vorschauen im `<img>` des Rasters, eigener Datenblock für
  Bilder außerhalb des Rasters) wird durch 3.4 ersetzt.
- AGENTS.md, Abschnitt Git: Testdaten der Components werden eingecheckt (bisher verboten), sofern sie
  synthetisch sind oder die Bergfex-Referenz; erzeugte Alben bleiben draußen.

## 10. Vorgehen

1. Die Architektur wird in diesem Dokument fertig beschrieben, bis Abschnitt 8 keine offenen Fragen mehr hat.
2. Dann ein Pull Request nach `main`.
3. Erst wenn der Stand auf `main` ist, beginnt die Umsetzung, in einer neuen Sitzung auf einem neuen Branch.
