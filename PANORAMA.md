# PANORAMA – Das Panorama-Widget

**Stand: umgesetzt (Version 1.6)** als Web Component `<album-panorama>` in `widgets/panorama/`. Offene Punkte
stehen in Abschnitt 13.

Dieses Dokument beschreibt, was das Widget tut und wie es aussieht. Es baut auf dem Grunddesign in
[DESIGN.md](DESIGN.md) auf, auf den Grundsätzen G1–G6 in [SPEC.md](SPEC.md) und auf der Architektur aus
Rumpfseite und Web Components in [ARCHITEKTUR.md](ARCHITEKTUR.md).

## 1. Zweck

Ein Panorama erscheint im Fotoraster als breiter Streifen über die volle Breite. Mit JavaScript wird daraus ein
Fenster, in dem man sich umsehen kann wie an Ort und Stelle: Das Bild wird entzerrt, so dass gerade Linien
gerade sind, und man kann schwenken, neigen und zoomen.

- Unterstützt wird genau ein Fall: Gerät hochkant gehalten und seitwärts geschwenkt, wie die
  Panorama-Funktion von Handys. Quer gehaltene und senkrecht geschwenkte Panoramen sind bewusst nicht
  vorgesehen (Entscheidung des Nutzers).
- Ein Album kann beliebig viele Panoramen enthalten.
- Alles steckt in der einen HTML-Datei (G1). Das Widget funktioniert offline.

## 2. Begriffe

| Begriff | Bedeutung |
|---|---|
| Panorama | ein `[[bild]]` mit `panorama = true` |
| Bildwinkel v | senkrechter Bildwinkel des Panoramas in Grad, vom unteren bis zum oberen Bildrand |
| Schwenkwinkel θ | waagerechter Winkel, den das Panorama umfasst, höchstens 360° |
| Streifen | das flache Panorama-Bild im Raster, wie es ohne JavaScript oder WebGL zu sehen ist |
| Schwenken, Neigen | Blickrichtung waagerecht bzw. senkrecht ändern (Gieren, Nicken) |
| Zoom | Vergrößerung; 1 = ganzer senkrechter Bildwinkel im Fenster |

## 3. Konfiguration

```toml
[einstellungen]
panorama_breite = 8192        # maximale Breite eines Panoramas in px
panorama_bildwinkel = 54.0    # senkrechter Bildwinkel in Grad, falls weder Bild noch EXIF einen liefern

[[bild]]
datei = "IMG_2001.jpg"
unterschrift = "Blick vom Gipfel"
panorama = true               # schwenkbares, entzerrtes Panorama über die volle Breite
panorama_bildwinkel = 54.3    # von init aus EXIF berechnet; fehlt die Zeile, gilt EXIF, sonst [einstellungen]
```

### 3.1 Schlüssel

| Schlüssel | Ort | Standard | Bedeutung |
|---|---|---|---|
| `panorama` | `[[bild]]` | `false` | das Bild als Panorama zeigen |
| `panorama_bildwinkel` | `[[bild]]` | aus EXIF, sonst `[einstellungen]` | senkrechter Bildwinkel dieses Panoramas |
| `panorama_breite` | `[einstellungen]` | `8192` | größte Breite des eingebetteten Panoramas in px |
| `panorama_bildwinkel` | `[einstellungen]` | `54.0` | Bildwinkel, wenn weder das Bild noch EXIF einen liefern |

`panorama` und `panorama_bildwinkel` stehen am `[[bild]]`, weil sie zum Foto selbst gehören (SPEC 9.6).

### 3.2 Fehler

Diese Fälle brechen den Bau mit einer Meldung ab (SPEC 4):

- `panorama_bildwinkel` außerhalb von 10–150 Grad
- falscher Typ in `[einstellungen]` (z. B. Text statt Zahl)

### 3.3 Was `init` schreibt

- Bilder, die mindestens 2,2-mal so breit wie hoch sind (`PANORAMA_AB`), bekommen `panorama = true` mit
  Kommentar.
- Liefert EXIF eine Brennweite, steht der daraus berechnete Bildwinkel als aktive Zeile
  `panorama_bildwinkel = …` mit Herkunft im Kommentar darunter. Sonst steht dort ein auskommentierter Hinweis,
  dass der Wert aus `[einstellungen]` gilt.
- In `[einstellungen]` stehen `panorama_breite` und `panorama_bildwinkel` mit ihren Standardwerten.

## 4. Aufbereitung beim Bauen

### 4.1 Bildwinkel

Reihenfolge: `panorama_bildwinkel` am Bild → EXIF → `[einstellungen]`. Der Bau nennt für jedes Panorama den
verwendeten Wert und seine Herkunft.

EXIF-Formel: v = 2·atan(`PANO_BESCHNITT` · 17,31 / f35)

- f35 = Kleinbild-Brennweite (EXIF-Tag 41989)
- 17,31 mm = halbe lange Seite eines 4:3-Bildes bei Kleinbild-Diagonale
- `PANO_BESCHNITT` = 0,77: Anteil der Sensorhöhe, der nach dem Beschnitt durch die Panorama-Funktion übrig
  bleibt. Eine Schätzung, so gewählt, dass 26 mm (iPhone-Hauptkamera) 54° ergibt.

### 4.2 Bilder

- EXIF-Drehung wird angewendet, sonstiges EXIF entfällt (G3), das ICC-Profil bleibt.
- **Volles Panorama:** höchstens `panorama_breite` breit, JPEG mit `qualitaet_vollbild`, als Base64 in
  `<script type="application/octet-stream" data-typ="image/jpeg" id="pano-N">` am Ende der Datei
  (ARCHITEKTUR.md 3.4). N zählt die Panoramen des Albums ab 1.
- **Streifen:** höchstens 2560 px breit (`PANO_VORSCHAU_BREITE`), JPEG mit `qualitaet_vorschau`, als `<img>`
  mit data-URI im Raster. Er ist die Ansicht ohne JavaScript.
- Das volle Panorama wird nur einmal eingebettet; der Streifen kommt dazu.

### 4.3 Daten

Der JSON-Block `album-daten` enthält je Panorama unter dem Schlüssel `panorama-N`:

```json
{"version": 1, "bild": "pano-N", "breite": 8192, "hoehe": 1342, "bildwinkel": 54.3}
```

`breite` und `hoehe` sind die Maße des vollen Panoramas in px, `bildwinkel` ist v in Grad.

## 5. Platz auf der Seite

- Panoramen stehen im Fotoraster an ihrer Stelle in der Reihenfolge der `album.toml` und spannen alle Spalten
  (`grid-column: 1 / -1`).
- Das Panorama liegt in einem Passepartout über die volle Breite (Rand 28 px, am Handy 12 px).
- Darunter steht die Unterschrift wie bei Fotos. Ein Aufnahmedatum wird nicht gezeigt.
- Panoramen zählen im Fuß „N Fotos" mit.

## 6. Aufbau

### 6.1 Desktop

- Fenster im Seitenverhältnis 2,2.
- Unten rechts zwei runde Knöpfe (44 px) „Verkleinern" und „Vergrößern" als schwebende Knöpfe (DESIGN.md 5).
  Ein Knopf ist abgeschwächt, wenn in seiner Richtung nicht weiter gezoomt werden kann.
- Unten links der Hinweis „Ziehen zum Umsehen" mit Pfeil-Symbol als schwebende Pille. Er verschwindet beim
  ersten Ziehen oder Berühren und kommt nicht wieder.

### 6.2 Handy (bis 700 px)

- Fenster im Seitenverhältnis 1,4.
- Hinweis in 13 px statt 14 px, schmaler.

## 7. Darstellung

- Annahme: zylindrische Projektion. Breite = f·θ, Höhe = 2·f·tan(v/2) ⇒ θ = (Breite/Höhe)·2·tan(v/2),
  begrenzt auf 360°. Ab knapp 360° gilt das Panorama als rund und lässt sich endlos drehen.
- Ein WebGL-Fragment-Shader rechnet für jeden Bildpunkt den Sichtstrahl einer geradlinigen Kamera (Schwenken,
  Neigen, Zoom) auf Zylinderkoordinaten um. So sind gerade Linien im Fenster gerade.
- WebGL2 mit Mipmaps, sonst WebGL1.
- Der Ausschnitt bleibt immer innerhalb des Bildes: Grenzen für Schwenken und Neigen und ein Mindestzoom. Bei
  Panoramen unter 180° ist der Mindestzoom größer als 1, damit links und rechts kein leerer Rand entsteht.
- Zoom bis 4.
- Ist das Panorama breiter als die größte Textur des Geräts (`MAX_TEXTURE_SIZE`), wird es im Browser vorher
  verkleinert.
- Auflösung der Zeichenfläche: Bildschirmpixel, höchstens doppelte Dichte.

## 8. Bedienung

### 8.1 Maus und Stift

- Ziehen schwenkt und neigt (Neigen nur, wenn vergrößert; unvergrößert füllt das Bild die Höhe schon ganz).
- Doppelklick wechselt zwischen Mindestzoom und doppeltem Mindestzoom.
- Plus und Minus zoomen jeweils um den Faktor 1,5.
- Kein Nachlauf.

### 8.2 Finger

Das Widget nimmt alle Gesten auf dem Panorama selbst entgegen (`touch-action: none`, Touch-Ereignisse) und
entscheidet selbst, was sie bewirken. Überlässt man das dem Browser (`touch-action: pan-y`), übernimmt Safari
(iOS) Gesten, die leicht senkrecht beginnen oder werden, und das Schwenken hakt (am iPhone beobachtet).

- **Unvergrößert** entscheiden die ersten 8 px einer Geste:
  - waagerecht → die ganze Geste schwenkt, auch wenn sie danach die Richtung ändert;
  - senkrecht → die Geste scrollt die Seite. Das Widget scrollt dann selbst, mit Nachlauf.
- **Vergrößert** schwenkt und neigt jede Geste. Um die Seite zu scrollen, verkleinert man wieder oder wischt
  neben dem Panorama.
- **Zwei Finger** zoomen. Hebt man einen ab, schwenkt der andere weiter.
- **Nachlauf:** Nach dem Loslassen laufen Schwenken und (vergrößert) Neigen mit der Geschwindigkeit der
  letzten 100 ms weiter und werden gleichmäßig langsamer. Am Bildrand hält der Nachlauf in dieser Richtung an.
  Stand der Finger vor dem Loslassen still, gibt es keinen Nachlauf. Ein neuer Finger hält ihn an.
- Die eigene Zoomgeste von Safari ist auf dem Panorama unterdrückt; Langdrücken öffnet kein Menü.
- Folge auf fremden Seiten: Senkrechtes Wischen über dem Panorama scrollt immer das Fenster, nicht einen
  umgebenden Scrollbereich.

## 9. Ressourcen

- Das Widget lädt das volle Panorama und startet erst, wenn es in die Nähe des Sichtbereichs kommt
  (600 px Vorlauf).
- Browser erlauben nur wenige WebGL-Flächen gleichzeitig. Das Widget gibt seinen Grafikkontext außerhalb des
  Sichtbereichs (plus 600 px) frei und baut ihn beim Zurückscrollen neu auf. Ein vom Browser entzogener
  Kontext wird ebenso neu aufgebaut. Schwenk und Zoom bleiben dabei erhalten.

## 10. Schnittstelle der Component

| | |
|---|---|
| Datei | `widgets/panorama/panorama.js`, braucht `widgets/gemeinsam/einbettung.js` |
| Element | `<album-panorama>` |
| Eingabe | Eigenschaft `daten` (4.3); im Album gesetzt aus `album-daten`, Schlüssel im Attribut `data-daten` |
| Inhalt | ein `<img>` als Kind: der Streifen, sichtbar ohne JavaScript oder WebGL |
| Bilddaten | `daten.bild` ist die `id` eines `<script>`- oder `<img>`-Elements der Seite (ARCHITEKTUR.md 3.4) |
| Farben | `--nav-bg`, `--nav-shadow`, dazu `color` der Umgebung |
| Schrift | `--album-schrift`, Standard: die Schrift der Umgebung |
| Ereignisse | keine |
| Zustand | Attribut `aktiv`, sobald das Widget läuft |

Das Widget kapselt seine Darstellung im Shadow DOM. Solange es nicht läuft, zeigt ein Slot den Streifen; sobald
WebGL läuft, ersetzt es den Slot durch Zeichenfläche und Bedienelemente.

Auf einer fremden Seite bindet man `einbettung.js` und `panorama.js` ein, stellt das volle Panorama als
`<script type="application/octet-stream" data-typ="image/jpeg" id="…">` auf die Seite und setzt `daten`.

## 11. Allgemeines

### 11.1 Ohne JavaScript oder WebGL

Das Panorama steht als Streifen im Raster wie ein gewöhnliches Foto, über die volle Breite. Es ist kein Link
und öffnet keine Großansicht (ARCHITEKTUR.md 3.1). Allein löst es den Hinweis auf fehlendes JavaScript nicht aus
(ARCHITEKTUR.md 3.2).

### 11.2 Hell und Dunkel

Passepartout, Knöpfe und Hinweis nehmen die Farben des Grunddesigns (DESIGN.md 2). Das Bild selbst wird nicht
verändert.

### 11.3 Abgrenzung

- Panoramen sind nicht Teil der Großansicht, nicht bildschirmfüllend zu öffnen und haben kein „Speichern"
  (Entscheidung des Nutzers, „erstmal", SPEC 9.3).
- Panoramen sind immer eingebettet, auch im späteren `--self-contained`-Modus (SPEC 9.1).
- Ausdrücklich nicht gewünscht: quer gehaltene und senkrecht geschwenkte Panoramen, mehr als 8192 px Breite.

### 11.4 Grundsätze

- **G1:** Volles Panorama und Streifen stecken in der Datei.
- **G2′:** Ohne JavaScript bleibt der Streifen (11.1).
- **G3:** Kein EXIF in der Ausgabe; nur der daraus berechnete Bildwinkel.
- **G6:** Die Umstellung auf die Web Component (Version 1.6) hat an der `album.toml` nichts geändert.

## 12. Entscheidungen

1. **Nur hochkant, seitwärts geschwenkt:** andere Aufnahmearten nicht vorgesehen (Nutzer).
2. **Bildwinkel-Reihenfolge** Bild → EXIF → `[einstellungen]`; `init` schreibt den EXIF-Wert als aktive Zeile.
3. **`PANO_BESCHNITT` = 0,77:** Schätzung, vom Nutzer an echten iPhone-Panoramen nicht beanstandet.
4. **Breite höchstens 8192 px:** reicht laut Nutzer.
5. **Keine Großansicht, kein Vollbild, kein Speichern** (erstmal, Nutzer).
6. **Web Component** mit Streifen als Inhalt und vollem Panorama in einem `<script>`-Block (ARCHITEKTUR.md).
7. **Streifen 2560 px breit:** Die Datei wird etwas größer, ohne JavaScript lädt die Seite schneller.
8. **Finger:** alle Gesten selbst entscheiden, mit Nachlauf (8.2); am iPhone vom Nutzer geprüft.
9. **Kein Nachlauf mit der Maus** (Vorschlag, nicht ausdrücklich bestätigt).

## 13. Offene Punkte und Ungeprüftes

- Zurückgestellt (SPEC 9.3): bildschirmfüllende Ansicht und „Speichern".
- Geprüft: Chrome mit Software-Rendering (Playwright, auch mit nachgestelltem iPhone); Fingersteuerung vom
  Nutzer am iPhone in Safari („fühlt sich gut an"). Echte iPhone-Panoramen hat der Nutzer früher ausprobiert
  (SPEC 8).
- Nicht geprüft: Zwei-Finger-Zoom ausdrücklich, Android, Firefox, Safari am Mac, Freigabe und Neuaufbau des
  Grafikkontexts außerhalb von Chrome, Panoramen breiter als `MAX_TEXTURE_SIZE` auf echten Geräten.

## 14. Prüfen

Zusätzlich zu den Prüfungen in AGENTS.md:

- Testseite: `python widgets/panorama/testseite.py <ordner>` oder auf GitHub Pages unter
  `<branch>/panorama/`. Testfälle aus `widgets/panorama/testdaten/erzeugen.py` (synthetischer Raum mit
  Gitterlinien, jede Wand in eigener Farbe):

  | Fall | Schwenkwinkel | Bildwinkel | prüft |
  |---|---|---|---|
  | `rund-360` | 360° | 54° | endloses Drehen |
  | `halb-180` | 180° | 54° | Grenzen beim Schwenken |
  | `schmal-120` | 120° | 54° | Mindestzoom größer als 1 |
  | `weit-70` | 240° | 70° | anderer Bildwinkel |

- Gitterlinien bleiben gerade, beim Schwenken, Neigen und Zoomen.
- Desktop und Handy, hell und dunkel, ohne JavaScript (Streifen).
- Am Handy: waagerecht wischen mit Richtungswechsel, senkrecht scrollen, vergrößert neigen, zwei Finger,
  Nachlauf. Für die Fehlersuche hat jeder Testfall einen Link „mit Touch-Protokoll" (`#protokoll`).
- Das Beispielalbum der Testseite: Panoramen zwischen Fotos, Großansicht blättert an ihnen vorbei.
