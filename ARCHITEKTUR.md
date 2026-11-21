# ARCHITEKTUR – Rumpfseite und Web Components

**Stand: Idee, nicht umgesetzt.** Grundzüge sind entschieden (Abschnitt 2), Einzelheiten offen (Abschnitt 8).
Vor der Umsetzung müssen die offenen Fragen beantwortet sein.

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
- **Alle Teile werden Web Components:** Alle bisherigen Teile des Albums werden durch Web Components ersetzt.
  Was es heute gibt, steht in Abschnitt 4.
- **Die Wanderung ist von Anfang an eine Web Component.** Sie soll so gebaut sein, dass man sie auch
  isoliert auf einer beliebigen anderen Website einbinden kann.
- **G2 entfällt.** Die Seite muss ohne JavaScript nicht mehr vollständig nutzbar sein. An die Stelle von G2
  tritt:
  - **G2′ – Grundansicht ohne JavaScript:** Ohne JavaScript zeigt die Seite nur
    - Kopf und Fuß (Titel, Unterzeile, Datum, „N Fotos"),
    - das Fotoraster mit allen Fotos samt Unterschriften und
    - eine einfache Großansicht: Ein Klick auf ein Foto öffnet es groß (Abschnitt 3.1).

    Alle anderen Widgets (Stationen, Karte, Panorama-Widget, Wanderung) zeigen ohne JavaScript nichts.
    Hell/Dunkel folgt ohne JavaScript der Systemeinstellung.
- **G6 gilt weiter:** Der Umbau ändert nichts an der `album.toml`. Jede bisher gültige Konfiguration baut
  weiter und zeigt dieselben Inhalte.

## 3. Zusammenspiel

```
album.toml ──► fotoalbum.py ──────────────────────────────► album.html
               │ prüft die Konfiguration                    ┌──────────────────────────────┐
               │ verarbeitet Bilder, Kacheln, GPX ...       │ Rumpf: Kopf, Fuß, Hell/Dunkel │
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
- Das große Bild steht als `<img loading="lazy">` mit Data-URL darin. Unsichtbare Lazy-Bilder lädt und
  dekodiert der Browser erst beim Öffnen. Die Großansicht-Component mit JavaScript nimmt das Bild von dort;
  es wird also nicht zusätzlich im JSON eingebettet (siehe 8.2).

Ausprobiert mit einem Prototyp in Chrome (Playwright, JavaScript abgeschaltet): öffnen, blättern und
schließen funktionieren, die Seite springt beim Öffnen nicht. Nicht geprüft: Safari, Firefox, echte
Mobilgeräte, Speicherbedarf mit 36 großen Bildern.

Grenzen gegenüber der Großansicht mit JavaScript:

- Kein Wischen, keine Pfeiltasten, kein Esc, kein Einpassen per Skript (nur `max-width`/`max-height`).
- Jedes Öffnen und Blättern ist ein Eintrag im Verlauf: Die Zurück-Taste blättert zurück, statt zu schließen.
- Beim Schließen springt das Foto an den oberen Fensterrand (per `scroll-margin` milderbar).
- Kein Knopf „Speichern"; ein eigener Download-Link würde das große Bild ein zweites Mal einbetten. Speichern
  geht über das Kontextmenü des Browsers.

## 4. Die Widgets

Bisherige Teile, die zu Web Components werden (Abgrenzung im Einzelnen offen, siehe 8.1):

| Teil | SPEC | Ohne JavaScript heute | Ohne JavaScript künftig (G2′) |
|---|---|---|---|
| Kopf und Fuß | 6.1 | vollständig | vollständig |
| Fotoraster | 6.1 | vollständig | vollständig, alle Fotos |
| Großansicht | 6.3 | nicht vorhanden | einfach, per `:target` (3.1) |
| Stationen | 6.4, 6.5 | vollständig, einklappbar | nichts |
| Karte mit Wegpunkten | 6.5, 6.6 | vollständig, einklappbar | nichts |
| Panorama | 6.7 | flacher Streifen | offen (8.3) |
| Hell/Dunkel-Umschalter | 6.2 | Systemeinstellung, kein Umschalter | Systemeinstellung, kein Umschalter |
| Wanderung (geplant) | WANDERUNG.md | Abschnittskopf und Kennzahlen (WANDERUNG 13.1) | nichts |

## 5. Bau

- Python bleibt für alles Rechnen zuständig: Konfiguration prüfen, Bilder verarbeiten, Kacheln laden, GPX
  lesen, Kennzahlen bestimmen. Die Web Components stellen nur dar. (Vorschlag, siehe 8.5.)
- Der Bau ermittelt aus der `album.toml`, welche Widgets gebraucht werden, und bettet nur deren Code ein.
- Die großen Base64-Blöcke werden weiter direkt in die Datei geschrieben, nicht erst im Speicher
  zusammengesetzt.

## 6. Widgets außerhalb des Albums

Am Beispiel der Wanderung: Die Component soll ohne den Rest des Albums auf einer fremden Seite laufen. Daraus
folgt:

- Sie bringt alles mit, was sie selbst braucht, und hängt nicht von CSS oder JavaScript der Rumpfseite ab.
- Ihre Eingabe ist ein festgelegtes, dokumentiertes Datenformat. Dieses Format ist eine Schnittstelle und
  braucht eine Versionsangabe.
- Offen ist, woher sie auf einer fremden Seite ihre Daten, Kacheln und Schrift bekommt (siehe 8.4).

## 7. Tests

Die Aufteilung in Widgets ist auch die Aufteilung der Tests:

- Jedes Widget bekommt einen eigenen Satz synthetischer Testdaten, die nur dieses Widget betreffen.
- Jedes Widget bekommt eine Testseite (Harness), die das Widget isoliert einbindet und seine Testfälle zeigt:
  hell und dunkel, Handy- und Desktopbreite, ohne JavaScript.
- Die Testseiten werden über GitHub Pages veröffentlicht, auch von Feature-Branches, und zwar so, dass
  mehrere Branches gleichzeitig ihre eigenen Testseiten haben.

Einzelheiten werden festgelegt, wenn die Architektur steht (siehe 8.7).

## 8. Offene Fragen

### 8.1 Rumpf und Zuschnitt der Widgets

Was bleibt im Rumpf: nur Kopf, Fuß, Schrift und Hell/Dunkel, oder werden auch Kopf und Fuß Widgets? Die
Großansicht wird von mehreren Widgets geöffnet (Raster, Wanderung). Vorschlag: eine eigene Component, die die
anderen aufrufen. Wie sie miteinander reden (Ereignisse, Methoden), ist festzulegen.

### 8.2 Bilder im JSON

Heute stecken die Vorschauen im `<img>` des Rasters; jedes Bild ist einmal eingebettet (SPEC 9.6).
Vorschlag:

- Die Bilddaten selbst stehen nicht im JSON, sondern im HTML der Grundansicht: Vorschauen im `<img>` des
  Rasters, große Bilder im `<img>` der Großansicht ohne JavaScript (3.1). So ist jedes Bild einmal
  eingebettet, und G2′ kostet keinen zusätzlichen Platz.
- Das JSON enthält eine zentrale Bildtabelle (Kennung, Unterschrift, Datum, Maße); Widgets verweisen per
  Kennung darauf und holen sich die Bilddaten aus dem HTML.
- Bilder, die nicht im Raster stehen (nur in einem Widget wie der Wanderung, SPEC 9.6), brauchen einen eigenen
  Ort, z. B. `<script type="application/json">`-Blöcke, die der Bau direkt in die Datei schreibt.
- Auf einer fremden Seite gibt es diese Grundansicht nicht. Eine isoliert eingebundene Component braucht ihre
  Bilder deshalb auf anderem Weg (siehe 8.4).

### 8.3 Grundansicht erzeugen

- Kopf, Fuß, Raster und Großansicht ohne JavaScript erzeugt der Bau in Python, die Components mit JavaScript
  ihre volle Darstellung. Für diese vier Teile gibt es also doppelte Darstellungslogik. Vorschlag: Die
  Components bauen auf dem vorhandenen HTML auf (Bilder, Texte, Reihenfolge), statt es aus dem JSON neu zu
  erzeugen.
- Panoramen: Erscheinen sie ohne JavaScript als gewöhnliches Foto im Raster (flacher Streifen, öffnet in der
  Großansicht)? Heute sind sie nicht Teil der Großansicht (SPEC 6.7).
- „Alle Fotos": alle Fotos der Galerie (SPEC 9.6, `[galerie]`), oder auch Fotos, die nur in einem Widget wie
  der Wanderung vorkommen?
- Soll die Seite ohne JavaScript darauf hinweisen, dass Karte, Stationen usw. fehlen?

### 8.4 Widgets auf fremden Seiten

- Daten: nur als JSON im Element, oder auch nachladen per Adresse (`src="…json"`)?
- Kacheln: auf einer fremden Seite auch live von einem Kachelserver laden?
- Shadow DOM: schützt das Widget vor fremdem CSS; Farben kommen weiter über CSS-Variablen hinein, so dass
  hell und dunkel von außen steuerbar bleiben.
- Schrift (rund 60 KB): gehört in den Rumpf, nicht in jede Component. Auf einer fremden Seite nimmt das Widget
  dann deren Schrift. In Ordnung?

### 8.5 Arbeitsteilung

Bleibt es dabei, dass Python rechnet und die Components nur darstellen (Abschnitt 5)?

### 8.6 Dateien und Werkzeuge

- Heute ist das Werkzeug eine einzige Datei. Vorschlag: Die Components werden eigene Dateien (z. B.
  `widgets/wanderung/wanderung.js`), der Bau bettet sie ein. Dann reicht `fotoalbum.py` allein nicht mehr.
- Vorschlag: reines JavaScript ohne npm, Bundler oder TypeScript, damit keine neue Abhängigkeit entsteht und
  die Dateien direkt im Browser laufen.

### 8.7 Tests und GitHub Pages

- Ort der Testdaten und Testseiten: `tests/widgets/<name>/` oder neben dem Code des Widgets?
- Pages: Vorschlag ist ein Branch `gh-pages` mit einem Ordner pro Branch. Ein Workflow baut bei jedem Push die
  Testseiten und ersetzt nur den Ordner seines Branches; beim Löschen eines Branches wird der Ordner entfernt;
  eine Startseite listet Branches und Widgets. Die Kacheln liefert ein Testserver im Workflow.
- Die Testseiten sind öffentlich (das Repository ist öffentlich). Mit synthetischen Daten kein Problem; die
  echte Bergfex-GPX-Datei für die Wanderung wäre dort als Karte zu sehen.

### 8.8 Umbau und Reihenfolge

- Soll der Umbau das Aussehen der bestehenden Teile unverändert lassen? Dann dient die heutige Seite als
  Vergleich.
- Die Wanderung darf erst mit der echten Bergfex-GPX-Datei umgesetzt werden (WANDERUNG Entscheidung 15).
  Vorschlag: die Architektur an einem bestehenden Widget einführen, etwa am Panorama, das schon heute nur mit
  JavaScript voll läuft.

## 9. Bei der Umsetzung anzupassen

- SPEC.md: Grundsatz G2 durch G2′ ersetzen, Abschnitt 6.3 um die Großansicht ohne JavaScript ergänzen.
  Abschnitt 6.5 und 7 („Einklappen per Checkbox"): Der Grund dafür war G2; Stationen und Karte brauchen
  künftig JavaScript, das Einklappen kann also per Skript geschehen.
- AGENTS.md: Aufbau von `fotoalbum.py`, Regel 2, Prüfen.
- WANDERUNG.md: 13.1 widerspricht G2′ (dort Abschnittskopf und Kennzahlen ohne JavaScript, künftig nichts);
  13.1 und 13.4 an G2′ und die Component anpassen.
- README.md: Voraussetzungen und Aufbau, falls das Werkzeug aus mehreren Dateien besteht.
