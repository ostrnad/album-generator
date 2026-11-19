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
  - **G2′ – JavaScript-freie Darstellung je Widget:** Jede Web Component legt fest, was ohne JavaScript zu
    sehen ist, und hält das so vollständig wie möglich. Was ohne JavaScript nicht geht, entfällt dort.
    Wie bisher bei der Wanderung (WANDERUNG 13.1) steht das in der Beschreibung des Widgets.
- **G6 gilt weiter:** Der Umbau ändert nichts an der `album.toml`. Jede bisher gültige Konfiguration baut
  weiter und zeigt dieselben Inhalte.

## 3. Zusammenspiel

```
album.toml ──► fotoalbum.py ──────────────────────────────► album.html
               │ prüft die Konfiguration                    ┌──────────────────────────────┐
               │ verarbeitet Bilder, Kacheln, GPX ...       │ Rumpf: Kopf, Fuß, Hell/Dunkel │
               │ erzeugt die Daten als JSON          ──────►│ Daten (JSON)                  │
               │ erzeugt je Widget die                ──────►│ <album-…> mit JS-freier       │
               │   JavaScript-freie Darstellung              │   Darstellung darin           │
               └ wählt die benutzten Web Components  ──────►│ Code der benutzten Components │
                                                            └──────────────────────────────┘
```

Folgerung aus G2′: Ohne JavaScript läuft keine Web Component. Die JavaScript-freie Darstellung muss deshalb
der Bau als fertiges HTML in das Element schreiben. Läuft JavaScript, übernimmt die Component und rendert ihre
volle Darstellung aus dem JSON.

## 4. Die Widgets

Bisherige Teile, die zu Web Components werden (Abgrenzung im Einzelnen offen, siehe 8.1):

| Teil | SPEC | Ohne JavaScript heute |
|---|---|---|
| Kopf und Fuß | 6.1 | vollständig |
| Fotoraster | 6.1 | vollständig |
| Großansicht | 6.3 | nicht vorhanden |
| Stationen | 6.4, 6.5 | vollständig, einklappbar |
| Karte mit Wegpunkten | 6.5, 6.6 | vollständig, einklappbar |
| Panorama | 6.7 | flacher Streifen |
| Hell/Dunkel-Umschalter | 6.2 | Systemeinstellung, kein Umschalter |
| Wanderung (geplant) | WANDERUNG.md | Abschnittskopf und Kennzahlen (WANDERUNG 13.1) |

Die rechte Spalte ist der Ausgangspunkt für G2′: Was heute ohne JavaScript geht, soll möglichst so bleiben.

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

- eine zentrale Bildtabelle im Rumpf, Widgets verweisen per Kennung darauf
- die großen Base64-Daten in eigenen `<script type="application/json">`-Blöcken, damit der Bau sie weiter
  direkt in die Datei schreiben kann
- Vorschaubilder, die ohne JavaScript sichtbar sein sollen, stehen ohnehin als `<img>` in der
  JavaScript-freien Darstellung; die Component kann sie von dort übernehmen statt sie doppelt einzubetten

### 8.3 JavaScript-freie Darstellung erzeugen

Der Bau muss sie in Python erzeugen, die Component ihre volle Darstellung in JavaScript. Das ist doppelte
Darstellungslogik. Zu klären: Ersetzt die Component die JavaScript-freie Darstellung, oder baut sie darauf
auf? Und wo liegt die Vorlage dafür, im Python-Code oder neben der Component?

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

- SPEC.md: Grundsatz G2 durch G2′ ersetzen, Abschnitt 6 je Teil um die JavaScript-freie Darstellung ergänzen,
  Abschnitt 7 („Einklappen per Checkbox") neu bewerten.
- AGENTS.md: Aufbau von `fotoalbum.py`, Regel 2, Prüfen.
- WANDERUNG.md: 13.1 und 13.4 an G2′ und die Component anpassen.
- README.md: Voraussetzungen und Aufbau, falls das Werkzeug aus mehreren Dateien besteht.
