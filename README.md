<p align="center">
  <img src="hero.png" alt="Cusco als vierfarbiges Druckrelief: echtes Mesh-Rendering mit Stadt, Anden und horizontaler Beschriftung" width="1200">
</p>

<h1 align="center">Cusco · Print the Andes</h1>

<p align="center">
  Ein Stück Peru für dein Druckbett.<br>
  Echtes Gelände, kartierte Stadtstrukturen und vier AMS-Farben.
</p>

<p align="center">
  <strong>Bambu Lab P1S</strong> &nbsp;·&nbsp; 4 Farben &nbsp;·&nbsp; 200 × 216 × 24 mm
</p>

<p align="center">
  <a href="output/print_v2/Cusco_P1S_AMS.3mf"><strong>3MF herunterladen</strong></a>
  &nbsp; / &nbsp; <a href="output/print_v2/Cusco_Gesamtansicht.png">Modell ansehen</a>
  &nbsp; / &nbsp; <a href="output/print_v2/Druckhinweise.md">Druckhinweise</a>
</p>

---

## Die Anden im kleinen Maßstab

Dieses Relief zeigt **20 × 20 km rund um Cusco**: das Tal, seine Berghänge, Straßen, Häusergruppen und kartierte Grünflächen. SRTM-Höhendaten liefern die Landschaft, OpenStreetMap die Stadtstrukturen.

Ein geschlossener Sockel mit ebener Unterseite trägt das Modell. **„Cusco“ liegt horizontal** auf dem integrierten vorderen Rand, nur 0,48 mm erhaben. Vier getrennte Farbvolumen bilden gemeinsam das zusammenhängende Relief.

> **Digital geprüft, noch nicht physisch probegedruckt.** Geometrieprüfung und vollständiger Probeschnitt in Bambu Studio waren erfolgreich. Die Bilder sind Renderings der tatsächlichen Druckmeshes, keine Fotos eines fertigen Drucks.

## Vom Download auf die Druckplatte

1. **[Cusco_P1S_AMS.3mf herunterladen](output/print_v2/Cusco_P1S_AMS.3mf)** — auf GitHub über „Download raw file“ auf der Dateiseite.
2. In Bambu Studio **als Projekt öffnen**, damit Teile, Profile und Anordnung erhalten bleiben. Enthalten ist das P1S-Profil für die 0,4-mm-Düse.
3. Vier kompatible PLA-Filamente zuordnen und die tatsächlichen AMS-Slots prüfen.
4. Platte neu slicen, Schichtvorschau und Spülturm kontrollieren, dann drucken.

Zum Drucken sind weder Python noch Blender erforderlich. Die 3MF ist ein editierbares Projekt; es wird kein vorgefertigter G-Code an den Drucker gesendet.

### Vier Farben, vier Aufgaben

| Zuordnung im Projekt | Modellteil | Farbton |
| --- | --- | --- |
| 1 | Gelände und Sockel | Sand-/Erdbraun · `#B8A17C` |
| 2 | Straßen und Schrift | Steingrau · `#757575` |
| 3 | Gebäude | Terrakotta · `#B66548` |
| 4 | Vegetation | Gedämpftes Grün · `#637D46` |

Eine reduzierte, landschaftlich orientierte Palette, keine Satellitenbild-Textur. Filament und Beleuchtung beeinflussen den tatsächlichen Eindruck.

### Das mitgelieferte Druckprofil

| Einstellung | Wert |
| --- | --- |
| Drucker / Düse | Bambu Lab P1S / 0,4 mm |
| Material / Schichthöhe | PLA / 0,16 mm |
| Wände / Füllung | 3 / 12 % Gyroid |
| Deck- / Bodenschichten | 5 / 4 |
| Stützen | Aus |
| Modellabmessungen | 200 × 216 × 24,05 mm |
| Geschätzte Druckzeit | ca. 23 h 57 min |
| Geschätzter Materialbedarf | ca. 307 g inklusive Spülabfall |

Die Schätzungen stammen aus dem Probeschnitt mit **Bambu Studio 2.8.2.61**: 149 Schichten und 320 Filamentwechsel. Andere Filamente und Einstellungen ändern diese Werte. Die geprüfte Platzierung des Spülturms neben dem Modell ist im Projekt enthalten.

<details>
<summary><strong>Beschriftung aus der Nähe ansehen</strong></summary>

![Horizontal eingelassene Cusco-Beschriftung](output/print_v2/Cusco_Beschriftung.png)

DejaVu Sans, 7,5 mm Schriftbildhöhe; 0,48 mm in den Sockel eingebettet und 0,48 mm erhaben. Die Buchstaben schweben nicht und stehen nicht senkrecht im Gelände.

</details>

## Was im Modell steckt

- **Durchgängige Höhen:** Die Kacheln S14W073 und S14W072 haben an der geprüften Naht keine Höhendifferenz; der Ausschnitt enthält keine Datenlücken. Eine leichte Gauß-Glättung mit rund 34 m Standardabweichung beruhigt das Raster.
- **Erkennbare Stadtstrukturen:** 97.252 OSM-Gebäudegrundrisse werden zu druckbaren Häusergruppen zusammengefasst. Straßen werden maßstabsbedingt verbreitert.
- **Kartiertes Grün:** Grünflächen und Baumstandorte erscheinen als flache, integrierte Reliefbereiche, nicht als freistehende Miniaturbäume.
- **Stabiler Unterbau:** 4 mm Sockelbasis vor der 0,8 mm tiefen Einbettung der farbigen Oberflächen; ebene Unterseite und geschlossene Farbvolumen.

**Bewusste Vereinfachungen:** Horizontaler Maßstab 1:100.000, Höhen 1,6-fach überhöht. Gebäudehöhen sind schematisch. Kleine Gassen und Grundstücksgrenzen lassen sich nicht einzeln darstellen. Vegetationsdaten sind unvollständig: Braune Flächen bedeuten nicht automatisch vegetationslosen Boden. Dekoratives Modell, keine Vermessungsgrundlage.

## Geprüft und nachvollziehbar

Der [Prüfbericht](output/print_v2/validation.json) dokumentiert:

- vier geschlossene Farbvolumen mit konsistenter Normalenausrichtung;
- einen zusammenhängenden Körper nach boolescher Vereinigung;
- numerisch vernachlässigbare Überschneidungen der Farbteile;
- 150 nichtleere horizontale Prüfschnitte in 0,16-mm-Abständen;
- Import ohne Mesh-Reparaturen und erfolgreichen Bambu-Probeschnitt;
- SHA-256-Prüfsummen der Druckdatei und der erzeugten STL-Teile.

Das finale Plattenergebnis enthält keine Warnmeldung. Das ist keine Garantie für einen fehlerfreien physischen Druck; Material, Haftung und Druckereinstellungen müssen vor Ort passen.

## Selbst bauen und rendern

Die fertige 3MF liegt bereits im Repository. Für eigene Läufe wurden **Python 3.12**, die festgehaltenen Abhängigkeiten und **Blender 5.0.1** verwendet. Die Skripte erwarten DejaVu Sans unter `/usr/share/fonts/truetype/dejavu/`.

```bash
python3.12 -m venv .venv-model
.venv-model/bin/python -m pip install -r requirements-print.txt

# Gelände, Farbteile, neutrale 3MF und Geometrieprüfung
MPLCONFIGDIR=/tmp/cusco-mpl .venv-model/bin/python build_print_model.py

# STL-Renderings und anschließend die README-Hero-Grafik
blender -b --factory-startup -t 8 --python render_print_model.py
blender -b --factory-startup -t 8 --python render_hero.py
```

Diese Befehle erzeugen Geometrie und Bilder, **nicht automatisch das native P1S-Projekt**. `prepare_bambu_check.py` und `finalize_print_package.py` gehören zum lokalen Bambu-Prüfworkflow. Ersteres erwartet extrahierte offizielle Bambu-Profile unter `/tmp/squashfs-root/resources/profiles/BBL`; Letzteres benötigt den nativen Export und einen erfolgreichen vollständigen Probeschnitt unter `output/print_v2/check/`.

Ein erneuter Modellbau ersetzt den Prüfbericht zunächst durch die reine Geometrieprüfung; anschließend muss auch der Probeschnitt erneuert werden.

### Orientierung im Repository

| Datei / Verzeichnis | Inhalt |
| --- | --- |
| [`hero.png`](hero.png) | Hero-Rendering aus der tatsächlichen STL-Szene |
| [`output/print_v2/Cusco_P1S_AMS.3mf`](output/print_v2/Cusco_P1S_AMS.3mf) | Empfohlenes Druckprojekt mit vier Farbzuordnungen |
| [`output/print_v2/Druckhinweise.md`](output/print_v2/Druckhinweise.md) | Eigenständige Druckhinweise |
| [`data/`](data/) | Lokale Höhen- und OSM-Quelldaten |
| [`build_print_model.py`](build_print_model.py) | Modellgenerator und Mesh-Prüfungen |
| [`render_print_model.py`](render_print_model.py) | Gesamtansicht und Beschriftungsdetail mit Cycles/CPU |
| [`render_hero.py`](render_hero.py) | Breites Hero-Layout aus der gespeicherten Blender-Szene |
| [`requirements-print.txt`](requirements-print.txt) | Python-Abhängigkeiten |

Aktuell ist ausschließlich die Modellfassung unter **`output/print_v2/`**. Andere Generator- und Vorschau-Skripte stammen aus früheren Entwicklungsständen. Alte Exporte, generierte STL-Dateien, alternative 3MFs, Blender-Szenen und temporäre Slicer-Dateien bleiben lokal und werden von Git ignoriert. Die aktuelle P1S-3MF, Hero-Grafik, Modell-PNGs, Druckhinweise und der Prüfbericht sind versioniert.

## Daten & Credits

- **Gelände:** [AWS Terrain Tiles / Mapzen](https://registry.opendata.aws/terrain-tiles/), SRTM-basierte Skadi-HGT-Kacheln mit etwa 30 m Quellraster; Abruf September 2026.
- **Stadt und Vegetation:** © [OpenStreetMap-Mitwirkende](https://www.openstreetmap.org/copyright), [ODbL](https://opendatacommons.org/licenses/odbl/1-0/); Overpass-Abfragen vom 13. September 2026. Wege und einzelne Baumknoten sind enthalten; komplexe Multipolygon-Relationen wurden nicht zusätzlich abgefragt.
- **Schrift:** DejaVu Sans.

Ein unabhängiges Modellprojekt, nicht von Bambu Lab herausgegeben.
