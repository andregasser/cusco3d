# Cusco – Cusco-Relief für Bambu Lab P1S, Version 2

Die aktuelle Fassung liegt ausschließlich unter **`output/print_v2/`**.
Dateien direkt unter `output/` sowie die alten Generator- und Vorschau-Skripte
sind überholte Prototypen. Bitte nicht mehr zum Drucken verwenden.

Git enthält die Skripte und Quelldaten sowie die aktuelle `Cusco_P1S_AMS.3mf`,
beide PNG-Vorschauen, Druckhinweise und den Prüfbericht. Generierte STL-Dateien,
alternative Exporte, Blender-Szenen und temporäre Slicer-Dateien bleiben lokal;
sie sind über `.gitignore` ausgeschlossen.

## Modell

- Grundfläche 200 × 216 mm; Höhe siehe `output/print_v2/validation.json`.
- 20 × 20 km um Cusco, horizontal 1:100.000, Höhen 1,6-fach überhöht.
- Ebene Unterseite, durchgehender Sockel mit 4 mm Mindesthöhe vor der
  0,8 mm tiefen Einbettung der farbigen Oberflächen.
- Korrekte Höhendatenkacheln S14W073 und S14W072, keine wiederholte Kachel
  am westlichen Rand. Leichte Gauß-Glättung mit rund 34 m Standardabweichung.
- OSM-Gebäude werden zu druckbaren Häusergruppen zusammengefasst; Höhen
  sind schematisch. Kleine Gassen und Grundstücksgrenzen sind bei diesem
  Maßstab nicht einzeln druckbar. Straßen und Bebauung sind generalisiert.
- Kartierte Grünflächen und Baumstandorte als flache grüne Reliefbereiche,
  ohne schwebende Baumkegel. OSM-Vegetationsdaten sind unvollständig;
  braune Flächen bedeuten nicht zwingend vegetationslosen Boden.
- Schrift exakt **„Cusco“**. DejaVu Sans, 7,5 mm Schriftbildhöhe,
  horizontal auf dem integrierten ebenen vorderen Rand. 0,48 mm erhaben und
  0,48 mm tief im Sockel verankert.

## Vier AMS-Farben

| Teil | Farbe |
| --- | --- |
| 01_Terrain_Sockel | Sand-/Erdbraun |
| 02_Strassen_Schrift | Steingrau |
| 03_Gebaeude | Terrakotta |
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

PLA, P1S, 0,4-mm-Düse: 0,16-mm-Schichten, 3 Wände, 12 % Gyroid, 5 Deck- und
4 Bodenschichten, keine Stützen. Vier kompatible PLA-Filamente verwenden und
die tatsächlichen AMS-Slots in Bambu Studio zuordnen. Bei Materialwechsel
passende Filamentprofile wählen und erneut slicen. Der Spülturm benötigt
seitlich Platz; die native Projektdatei enthält die geprüfte Anordnung.

Der vollständige Probeschnitt mit Bambu Studio 2.8.2.61 endete erfolgreich,
ohne Warnmeldung im Plattenergebnis: 149 Druckschichten, 320 Filamentwechsel,
ca. 23 h 57 min und 307 g PLA einschließlich Spülabfall. Das sind Schätzungen
des mitgelieferten Profils; andere Filamente und Einstellungen verändern sie.
Die vier Teile wurden ohne Mesh-Reparaturen importiert. Ein physischer
Probedruck wurde nicht durchgeführt.

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
Schrift: DejaVu Sans. Dekoratives Modell, keine Vermessungsgrundlage.
