# Cusco – Cusco-Relief für Bambu Lab P1S, Version 2

Die aktuelle Fassung liegt ausschließlich unter **`output/print_v2/`**.
Dateien direkt unter `output/` sowie die alten Generator- und Vorschau-Skripte
sind überholte Prototypen. Bitte nicht mehr zum Drucken verwenden.

Git enthält die Skripte und Quelldaten sowie die aktuelle `Cusco_P1S_AMS.3mf`,
die PNG-Vorschauen, Druckhinweise und den Prüfbericht. Generierte STL-Dateien,
alternative Exporte, Blender-Szenen und temporäre Slicer-Dateien bleiben lokal;
sie sind über `.gitignore` ausgeschlossen.

## Modell

- Grundfläche 200 × 200 mm; Höhe siehe `output/print_v2/validation.json`.
- Der vordere, 16 mm tiefe Beschriftungsstreifen entfällt. Der gesamte
  Landschaftsausschnitt bleibt erhalten. Nur die kleine Schriftfläche innerhalb
  des Modells wird eingeebnet.
- 20 × 20 km um Cusco, horizontal 1:100.000, Höhen 1,6-fach überhöht.
- Ebene Unterseite, durchgehender Sockel mit 4 mm Mindesthöhe vor der
  0,64 mm tiefen Einbettung der farbigen Oberflächen. Die unsichtbare Einbettung
  ist um 0,16 mm reduziert; die äußere Form bleibt dabei exakt gleich.
- Korrekte Höhendatenkacheln S14W073 und S14W072, keine wiederholte Kachel
  am westlichen Rand. Leichte Gauß-Glättung mit rund 34 m Standardabweichung.
- OSM-Gebäude werden zu druckbaren Häusergruppen zusammengefasst; Höhen
  sind schematisch. Kleine Gassen und Grundstücksgrenzen sind bei diesem
  Maßstab nicht einzeln druckbar. Straßen und Bebauung sind generalisiert.
- Dezent verstärkte Sichtbarkeit: Dachaufschlag 1,20 statt 0,95 mm,
  Straßenaufschlag 0,32 statt 0,18 mm, an gemeinsamen Rasterpunkten gemittelt.
  Straßenbreiten unverändert; Grau und Terrakotta etwas dunkler.
- Flughafen mit kartierter Startbahn 10/28, 18 Rollwegsegmenten und zwei
  Vorfeldern. Startbahn rund 1,09 mm breit, Rollwege rund 0,54 mm,
  Höhenaufschlag 0,40 mm; gleiche Farbe wie Straßen.
- Kartierte Grünflächen und Baumstandorte als flache grüne Reliefbereiche,
  ohne schwebende Baumkegel. OSM-Vegetationsdaten sind unvollständig;
  braune Flächen bedeuten nicht zwingend vegetationslosen Boden.
- Schrift exakt **„Cusco“**. DejaVu Sans, 7,5 mm Schriftbildhöhe,
  waagerecht auf einer etwa 30 × 9 mm großen ebenen Fläche vorne links,
  vollständig innerhalb der Modellkante. 0,48 mm erhaben und 0,48 mm eingebettet.
  Alle fünf Buchstaben stehen auf gleicher Höhe in einem kartografisch freien
  Bereich. Ein schmaler Rand verbindet die ebene Fläche mit dem Gelände.

## Vier AMS-Farben

| Teil | Farbe |
| --- | --- |
| 01_Terrain_Sockel | Sand-/Erdbraun |
| 02_Strassen_Schrift (mit Flughafen) | Dunkles Steingrau `#64696C` |
| 03_Gebaeude | Terrakotta `#AC5438` |
| 04_Vegetation | Gedämpftes Grün |

**`Cusco_P1S_AMS.3mf` ist die empfohlene Datei.** Sie wurde mit Bambu Studio
2.8.2.61 exportiert, enthält das P1S-Profil mit 0,4-mm-Düse, vier Farbzuordnungen,
0,16-mm-Schichten und die geprüfte Platzierung des Spülturms. Als Projekt öffnen,
eigene Filamente/AMS-Slots zuordnen und slicen. Es wird kein vorgefertigter
G-Code ungeprüft an einen Drucker gesendet.

`Cusco_AMS_4_Farben.3mf` ist die neutrale Geometriealternative ohne vollständiges
Druckprofil. STL-Dateien speichern selbst keine Farben.
Alternativ alle vier nummerierten STL gemeinsam als **ein Objekt mit mehreren
Teilen** importieren. Teile nicht einzeln auf das Druckbett absenken.
`Cusco_einfarbig.stl` ist die boolesch vereinigte Einfarb-Version.
Die erhabene Schrift ist auch in der Einfarb-Version geometrisch enthalten.

PLA, P1S, 0,4-mm-Düse: 0,16-mm-Schichten, 3 Wände, 12 % Gyroid, 5 Deck- und
4 Bodenschichten, Deckschale mindestens 1 mm, keine Stützen.
Füllschichten kombinieren und Spülen in die innere Füllung sind aktiviert.
Vier kompatible, **deckende** PLA-Filamente verwenden und
die tatsächlichen AMS-Slots in Bambu Studio zuordnen. Bei Materialwechsel
passende Filamentprofile wählen und erneut slicen. Der Spülturm benötigt
seitlich Platz; die native Projektdatei enthält die geprüfte Anordnung.

Der vollständige Probeschnitt mit Bambu Studio 2.8.2.61 endete erfolgreich,
ohne Warnmeldung im Plattenergebnis: 150 Druckschichten, 316 Filamentwechsel,
ca. 23 h 00 min und 297 g PLA einschließlich Spülabfall. Das sind Schätzungen
des mitgelieferten Profils; andere Filamente und Einstellungen verändern sie.
Die vier Teile wurden ohne Mesh-Reparaturen importiert. Ein physischer
Probedruck wurde nicht durchgeführt.

## Druckzeit und sichtbare Qualität

Gegenüber der Fassung mit vorderem Schriftstreifen (23 h 19 min 13 s,
306,35 g) spart die aktuelle Fassung mit ebener Schriftfläche innerhalb des
Modells **19 Minuten und 9,2 g PLA**: 23 h 00 min 13 s und 297,17 g.
Gegenüber dem ursprünglichen Projekt (23 h 56 min 47 s) sind es insgesamt
56 min 34 s. `print_time_comparison.json` enthält alle sechs Vergleichsvarianten.

Der 16-mm-Schriftstreifen entfällt vollständig. Der ursprüngliche Rasterausschnitt
für Straßen, Flughafen, Gebäude und Vegetation sowie die Gebäudehöhen bleiben
erhalten. Nur an der neuen Vorderkante wird das Geländeraster angeschnitten.
Für die Schrift ist eine kleine freie Geländeoberfläche innerhalb des Modells
eingeebnet; die Buchstaben stehen waagerecht und leicht erhaben darauf.

Die sichtbaren Schichten bleiben 0,16 mm fein, Wandzahl und
Oberflächengeschwindigkeiten bleiben unverändert. Kombinierte Füllschichten
und Spülen in die Füllung betreffen das Innere. Die Farbeinbettung unter dem
Gelände ist von 0,80 auf 0,64 mm reduziert; sichtbare Form und Farbgrenzen
bleiben dabei gleich. Deckendes PLA verwenden: Mischfarben im Inneren können
bei durchscheinenden Filamenten sichtbar werden. Die Farbdurchdeckung der
neuen Einbettung ist physisch noch nicht geprüft.

316 Farbwechsel und rund 7½ Stunden Spülzeit begrenzen die Ersparnis.
Eine drastisch kürzere Druckzeit bei gleicher Vierfarb-Darstellung ist mit
diesen Tests nicht belegt. Gröbere Schichten oder weniger Farben ändern die
sichtbare Qualität. Spülmengen wurden nicht manuell reduziert.

## Prüfung und Reproduktion

`validation.json` dokumentiert Kachelnaht, ungültige Höhenwerte, geschlossene
Farbvolumen, Normalenausrichtung, Schnittvolumen, Zusammenhalt und horizontale
Schnitte in 0,16-mm-Abständen. Numerische Nullvolumen-Artefakte der booleschen
Vereinigung werden aus der Einfarb-Version entfernt.

```bash
MPLCONFIGDIR=/tmp/cusco-mpl .venv-model/bin/python build_print_model.py
blender -b --factory-startup -t 8 --python render_print_model.py
```

`build_print_model.py` erzeugt die Druckdateien. `render_print_model.py` importiert
exakt diese vier STL-Dateien in Blender und rendert mit Cycles/CPU. Die PNGs
sind echte Mesh-Renderings; Beleuchtung verändert den Farbeindruck. Sie zeigen
die Form, nicht die Extrusionsbahnen. Die Szene liegt als `Cusco_Render.blend` vor.

Python benötigt numpy, scipy, shapely, trimesh, manifold3d, pillow, mapbox-earcut
und matplotlib. Diese sind in `.venv-model` installiert.

## Daten und Attribution

Höhendaten: [AWS Terrain Tiles / Mapzen](https://registry.opendata.aws/terrain-tiles/),
SRTM-basierte Skadi-HGT-Kacheln, Abruf September 2026; etwa 30 m Quellraster.
Straßen, Gebäude und Vegetation: © [OpenStreetMap-Mitwirkende](https://www.openstreetmap.org/copyright),
[ODbL](https://opendatacommons.org/licenses/odbl/1-0/), Overpass-Abfragen vom
13. September 2026. Die lokale Auswahl enthält Wege und einzelne Baumknoten;
komplexe Multipolygon-Relationen wurden nicht zusätzlich abgefragt.
Flughafengeometrien: ergänzende Overpass-Abfrage vom 24. September 2026,
Server-Datenstand 15. Juli 2026; Abfrage und Geometrien in
`data/cusco_airport.json`, ebenfalls ODbL.
Schrift: DejaVu Sans. Dekoratives Modell, keine Vermessungsgrundlage.
