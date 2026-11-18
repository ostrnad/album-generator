# DESIGN – Grunddesign „D · Passepartout"

Dieses Dokument beschreibt das gemeinsame Aussehen, auf dem alle Teile des Albums aufbauen: Farben, Schrift,
Abstände und die wiederkehrenden Bausteine. Was die einzelnen Teile (Großansicht, Stationen, Karte, Panorama)
zusätzlich können und wie sie aussehen, steht in [SPEC.md](SPEC.md) Abschnitt 6.

Grundregel: Ein Teil des Albums verwendet nur, was hier steht. Braucht es etwas Neues, das auch anderen Teilen
nützen könnte (eine Farbe, eine Knopfart), wird es zuerst hier eingetragen.

## 1. Die Idee

Jedes Foto liegt wie ein Abzug in einem weißen Passepartout auf einem ruhigen, graugrünen Grund. Alles ist
mittig ausgerichtet, mit viel Luft und wenig Schmuck. Die Fotos bringen die Farbe; alles andere tritt zurück.

## 2. Farben

Jede Farbe hat eine feste Aufgabe. Im Code heißt sie wie in der letzten Spalte.

| Aufgabe | Hell | Dunkel | Wofür | Code |
|---|---|---|---|---|
| Grund | `#DCE3DD` | `#161C18` | Seitenhintergrund | `--bg` |
| Text | `#1F2A24` | `#E6ECE7` | Titel, Texte, Symbole | `--fg` |
| Gedämpft | `#4A584F` | `#A9B5AC` | Unterschriften, Datum, Ränder von Pillen und Knöpfen | `--muted` |
| Passepartout | `#FFFFFF` | `#242C27` | Fläche um Fotos, Karte, Panorama | `--mat` |
| Rand des Passepartouts | weicher Schatten | feine Kontur `#36413A` | hebt die Fläche vom Grund ab | `--mat-shadow` |
| Grund Großansicht | `#CFD8D1` | `#0F1411` | Hintergrund der Großansicht | `--lb-bg` |
| Gedämpft Großansicht | `#3F4D44` | `#A9B5AC` | wie „Gedämpft", auf dem Grund der Großansicht | `--lb-muted` |
| Betont | `#1F2A24` mit `#FFFFFF` | `#E6ECE7` mit `#161C18` | gefüllte Knöpfe, Marken, Route | `--btn-bg`, `--btn-fg` |
| Schwebend | `#FFFFFF` mit Schatten | `#242C27` mit Kontur | Knöpfe, die auf oder neben einem Bild liegen | `--nav-bg`, `--nav-shadow` |
| Linie | Gedämpft, halb durchsichtig | ebenso | Linie der Zeitleiste | `--linie` |
| Platzhalter | Grau, halb durchsichtig | gleich | Fläche, solange ein Bild noch lädt | – |
| Leichte Fläche | Text, 5 % deckend | Text, 6 % deckend | ruhiger Hintergrund innerhalb eines Passepartouts (geplant: Wanderung) | – |

Farben nur für Wanderungen (geplant, siehe [WANDERUNG.md](WANDERUNG.md)), hell und dunkel gleich:

| Aufgabe | Wert | Wofür |
|---|---|---|
| Orange | `#E8590C` | Route, Cursor, Auswahl; Fläche unter dem Höhenprofil mit 20 % |
| Orange hell, Orange dunkel | `#F08C4A`, `#A63D08` | zusammen mit Orange: die Etappen in der Ansicht „Gesamt" |
| Grün | `#2B8A3E` | Anfang der Route |
| Rot | `#C92A2A` | Ende der Route |

Regeln:

- **Keine weiteren Farben und keine Akzentfarbe.** Hervorgehoben wird mit „Betont", also dunkel auf hell
  bzw. hell auf dunkel. Einzige Ausnahme sind die Wanderungsfarben oben, und nur für die genannten Zwecke.
- **Hell und Dunkel gehören zusammen.** Jede Farbe hat beide Werte. Im Code stehen die hellen Werte in `CSS`,
  die dunklen in `DARK_VARS`.
- **Im Dunkeln werden Schatten zu feinen Konturen**, weil man Schatten auf dunklem Grund nicht sieht.
- **Im Dunkeln sind Passepartouts dunkel**, sonst würden viele weiße Flächen blenden.
- Fremde Bilder, die keine Fotos sind (die Karte), werden im Dunkeln mit abgedunkelt.

## 3. Schrift

Eine Schrift: **Bricolage Grotesque**, nur in normal (400) und fett (600), in die Datei eingebettet.

| Stufe | Desktop | Handy | Wofür |
|---|---|---|---|
| Titel | 60 px, fett | 36 px, fett | Albumtitel; leicht enger gesetzt |
| Unterzeile | 20 px | 16 px | Zeile unter dem Titel, gedämpft |
| Groß | 18 px | 17 px | Unterschrift in der Großansicht |
| Lesetext | 16 px | 15 px | längere Texte, z. B. Stationen |
| Normal | 15 px | 13–14 px | Unterschriften, Fuß, Pillen, Knopftext |
| Klein | 13–14 px | 13–14 px | Datum, Nummern, kurze Namen (fett) |
| Kleinst | 11 px | 11 px | nur die Quellenangabe der Karte |

Regeln: Fett nur für den Titel und für kurze Namen oder Nummern. Kein Kursiv, keine Zeilen in Großbuchstaben.
Lange Wörter dürfen umbrechen, damit nichts über den Rand ragt.

## 4. Raum und Größen

- **Zwei Größen:** Desktop und Handy. Die Grenze liegt bei 700 px Fensterbreite. Dazwischen gibt es nichts.
- **Breite:** Inhalt höchstens 1120 px, mittig. Reine Lesetexte höchstens 720 px.
- **Seitenrand:** Desktop 88 px oben und unten, 40 px seitlich. Handy 68 px oben, 16 px seitlich, 48 px unten.
- **Abstand zwischen den großen Abschnitten** (Kopf, Stationen, Karte, Fotos, Fuß): 64 px, am Handy 36 px.
- **Fotoraster:** Desktop 3 Spalten, Handy 2. Abstand 40 px nach unten und 24 px zur Seite, am Handy 24 und
  14 px.
- **Unterschrift** sitzt 12 px unter dem Bild, am Handy 8 px.

## 5. Bausteine

Es gibt nur zwei Formen: **eckige Flächen** (das Passepartout, ohne Rundung) und **ganz runde** (Pillen,
Knöpfe, Marken). Nichts dazwischen.

- **Passepartout:** Fläche in „Passepartout" mit dessen Rand; der Inhalt liegt mittig darin. Alles, was ein
  Bild zeigt, sitzt in einem Passepartout.
  - Fotos im Raster: quadratische Fläche, 9 % Rand, das Foto in seinem eigenen Seitenverhältnis.
  - Breite Inhalte (Karte, Panorama, Bild in der Großansicht): fester Rand von 28 px, am Handy 12–14 px.
- **Pille:** Text und 1 px Rand in „Gedämpft", ganz rund. Für Angaben (Datum im Kopf) und, 44 px hoch, für
  Knöpfe zum Auf- und Zuklappen.
- **Runder Knopf:** 44 × 44 px, durchsichtig, Rand in „Gedämpft", ein Symbol darin. Für Hell/Dunkel und
  Schließen.
- **Betonter Knopf:** gefüllt in „Betont", 44 px hoch, Symbol und Wort. Höchstens einer pro Ansicht, für die
  Hauptaktion (Speichern).
- **Schwebender Knopf:** rund, 44–48 px, in „Schwebend". Für Knöpfe auf oder neben einem Bild (Blättern,
  Zoomen, Hinweise auf dem Panorama).
- **Marke:** kleine gefüllte Pille, 28 px hoch, in „Betont", mit Nummer oder Symbol. Für Kartenpunkte und
  Stationen.
- **Auswahlring:** oranger Ring um eine Marke oder ein kleines Passepartout. Zeigt, was gerade ausgewählt
  ist. Geplant für die Wanderung.
- **Schalter:** eine Pille mit mehreren Knöpfen (je 44 px hoch). Der gewählte ist in „Betont" gefüllt.
  Geplant für den Tag-Schalter der Wanderung.
- **Kennzahl:** Wert groß und fett (20 px, am Handy 17 px), darunter die Beschriftung in „Normal klein",
  gedämpft. Mehrere stehen mittig in einer Reihe. Geplant für die Wanderung.
- **Symbole:** einfache Strichzeichnungen auf 24 × 24, Strichstärke 2, runde Enden, in der Textfarbe.
  18 px in Knöpfen, 20 px beim Blättern. Keine Emojis.

## 6. Verhalten

- **Ohne JavaScript ist alles zum Ansehen da.** Knöpfe, die nur mit JavaScript funktionieren, werden erst
  eingeblendet, wenn JavaScript läuft (Klasse `.js`).
- **Hell oder Dunkel** folgt der Einstellung des Geräts. Der Umschalter merkt sich die Wahl.
- **Alles Bedienbare ist mindestens 44 px groß**, damit es sich am Handy gut treffen lässt.
- **Aufklappbare Abschnitte** sind am Desktop offen und am Handy zu.
- **Bewegung sparsam:** nur kurze, ruhige Übergänge (ein Pfeil dreht sich, ein Hinweis blendet aus).
- **Nichts wird nachgeladen:** Schrift, Bilder und Symbole stecken in der Datei.

## 7. Aufbau der Seite

Von oben nach unten: Kopf (Titel, Unterzeile, Datum als Pille) – Stationen – Karte – Wanderungen (geplant) – Fotos – Fuß
(„N Fotos"). Kopf und Fuß sind mittig. Der Hell/Dunkel-Knopf sitzt oben rechts in der Ecke. Jedes Teil
dazwischen nimmt entweder die volle Inhaltsbreite ein oder sitzt im Fotoraster.

## 8. Die Teile des Albums

Wie die Teile das Grunddesign nutzen. Die Einzelheiten stehen in SPEC.md.

| Teil | Nutzt | SPEC |
|---|---|---|
| Foto im Raster | Passepartout (quadratisch), Unterschrift | 6.1 |
| Großansicht | eigener Grund, Passepartout mit festem Rand, runde Knöpfe, betonter Knopf „Speichern", schwebende Blätterknöpfe | 6.3 |
| Stationen | Linie, Marken, Lesetext, Pille zum Aufklappen | 6.4, 6.5 |
| Karte | Passepartout mit festem Rand, Marken, Route in „Betont", Pille zum Aufklappen | 6.5, 6.6 |
| Panorama | Passepartout über die volle Breite, schwebende Zoomknöpfe und Hinweis | 6.7 |
| Wanderung (geplant) | Passepartout über die volle Breite, Kennzahlen, Schalter, Marken, Auswahlring, schwebende Knöpfe, Wanderungsfarben, Pille zum Aufklappen | [WANDERUNG.md](WANDERUNG.md) |

## 9. Checkliste für ein neues Teil

- Nur Farben aus Abschnitt 2. Braucht es eine neue, kommt sie hier in die Tabelle, mit hellem und dunklem Wert.
- Bilder und Karten liegen im Passepartout.
- Knöpfe, Pillen und Marken aus Abschnitt 5, Schriftgrößen aus Abschnitt 3.
- Am Desktop und am Handy ansehen, jeweils hell und dunkel, und einmal ohne JavaScript.
- Was nur dieses Teil betrifft, kommt in SPEC.md, nicht hierher.
