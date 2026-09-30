# Cusco-Relief für Bambu Lab P1S

Aktuell ist ausschließlich `output/print_v2/Cusco_P1S_AMS.3mf`. Die Datei enthält
das native P1S-Profil für die 0,4-mm-Düse und vier Farbzuordnungen. Als **Projekt**
öffnen, eigene Filamente und AMS-Slots zuordnen und neu slicen. Die Datei enthält
keinen vorgefertigten G-Code. Dateien direkt unter `output/` sind alte Prototypen.

## Modell und ergänzte Stadt

- 200 × 200 × 24,53 mm; 20 × 20 km Landschaft, horizontal 1:100.000, Höhen 1,6-fach überhöht.
- Ebene Unterseite, Sockelbasis 4 mm vor der 0,64 mm tiefen Farbeinbettung.
- Die ursprünglichen Geländedreiecke werden auf rund 14 m Rasterweite unterteilt; die Geländegrundlage und ihre Glättung bleiben erhalten.
- OSM wird durch 81.444 Microsoft-Grundrisse ergänzt. 21.874 stark überlappende Dubletten sowie 76 sehr kleine oder unzureichend bewertete Geometrien wurden ausgesondert. Verbleibende Überlappungen werden im Raster vereinigt; die Zahl ist keine Zählung neuer Einzelhäuser.
- Die Modellfläche für Gebäude beträgt rund 3.642 mm² statt 2.344 mm² in der letzten Vorschau. Etwa 4.938 getrennte Häusergruppen erhalten waagerechte Dächer und senkrechte Wände. Dächer liegen 1,20 mm über dem höchsten Oberflächenpunkt des jeweiligen Blocks; Höhen sind schematisch.
- Hauptstraßen und Flughafen sind geschützt. Nebenstraßen behalten in dichten Vierteln einen rund 0,27 mm breiten Rasterkern; ihre zuvor überzeichneten Randbereiche weichen der Bebauung. Sehr schmale Farbdetails können im Slicer weiter vereinfacht werden. Wohnstraßen außerhalb solcher Engstellen sind bis etwa 0,41 mm, Hauptstraßen rund 0,55 mm breit.
- Startbahn, 18 Rollwegsegmente und zwei Vorfelder bleiben enthalten. Startbahn rund 1,09 mm, Rollwege rund 0,55 mm breit; 0,40 mm Höhenaufschlag. Straßenaufschlag 0,32 mm.
- WorldCover und OSM färben rund 75 % der Draufsicht grün, ohne zusätzliche Vegetationshöhe. Die Daten sind eine Landbedeckungsklassifikation von 2021.
- „Cusco“ steht waagerecht auf einer etwa 30 × 9 mm großen internen Schriftfläche: 28,8 × 7,5 mm Schriftbild, 0,64 mm erhaben, 0,48 mm eingebettet. Ein neu hinzugekommenes Quellrasterfeld wird zugunsten dieser dekorativen Fläche ausgespart und im Prüfbericht ausgewiesen.
- Standort-Pin an **−13.521908269187426, −71.98500062613564**, Modellposition X = 81,016 / Y = 111,178 mm ab der südwestlichen Ecke. 5 mm über der höchsten unmittelbaren Umgebung, 1,8 mm Schaft und 3,2 mm abgerundeter Kopf; fest eingebettet und mit 45°-Schulter.

## Farben und Profil

| Teil / AMS-Zuordnung | Farbe |
| --- | --- |
| 1 · Gelände und Sockel | Sand-/Erdbraun `#B8A17C` |
| 2 · Straßen, Flughafen und Schrift | Steingrau `#64696C` |
| 3 · Gebäude und Pin | Terrakotta `#AC5438` |
| 4 · Vegetation | Grün `#637D46` |

PLA, 0,16-mm-Schichten, drei Wände, 12 % Gyroid, fünf Deck- und vier Bodenschichten,
Deckschale mindestens 1 mm, automatische Baumstützen aktiviert. Im geprüften
Probeschnitt werden keine Stützbahnen erzeugt. Füllschichten kombinieren und Spülen in
die Füllung sind aktiviert; innere Füllbahnbreite 0,45 mm. Vier kompatible, deckende
PLA-Filamente verwenden. Der Spülturm benötigt seitlich Platz; die geprüfte
Anordnung ist im Projekt gespeichert.

Der vollständige Probeschnitt mit Bambu Studio 2.8.2.61 ergibt **29 h 14 min 43 s**, **317,62 g PLA**, 153 Schichten und 353 Filamentwechsel.
Das Plattenergebnis enthält keine Warnmeldung; alle vier Teile wurden ohne
Mesh-Reparaturen importiert. Ohne automatische Stützerkennung meldet Bambu
mögliche schwebende Bereiche; die vollständige automatische Stützberechnung
erzeugt keine Stützbahnen. Die unabhängige Prüfung der STL-Schichten besteht
ebenfalls. Die automatische Erkennung bleibt im Profil aktiv. Es handelt sich
um Slicer-Schätzungen.
**Ein physischer Probedruck wurde noch nicht durchgeführt.**

## Prüfen und Alternativen

`validation.json` enthält geschlossene Farbvolumen, konsistente Normalen,
paarweise Schnittvolumen, einen zusammenhängenden Gesamtkörper und horizontale
Prüfschnitte in 0,16-mm-Abständen. Gebäudequellen, Straßenprioritäten,
Schriftfläche und Pin sind dokumentiert; Bambu-Ergebnis und SHA-256-Prüfsummen
gehören zur fertig paketierten Fassung.

`building_coverage_comparison.json` vergleicht drei zuvor lückenhafte Viertel.
`city_density_comparison.json` enthält die Rasterflächen; `print_time_comparison.json`
bewahrt die bisherigen Druckzeitvergleiche. Die ungeprüfte Zwischenvorschau mit
dichteren OSM-Blöcken ist dort ausdrücklich kein zusätzlicher Druckbenchmark.

`Cusco_AMS_4_Farben.3mf` ist die neutrale Geometriealternative ohne vollständiges
Druckprofil. Alle vier nummerierten STL gemeinsam als **ein Objekt mit mehreren
Teilen** importieren und nicht einzeln auf das Druckbett absenken. STL speichern
keine Farben. `Cusco_einfarbig.stl` enthält das vereinigte Modell einschließlich
Schrift und Pin. Das alternative STL-Archiv enthält diese Druckhinweise.

Die ergänzten Grundrisse wurden automatisch aus Bildern erkannt und können Fehler
oder Auslassungen enthalten. Für die übernommenen Zusatzgrundrisse ist kein
Konfidenzwert angegeben; unbekannte Werte werden nicht als hohe Sicherheit gewertet.
WorldCover dient zur Abdeckungsprüfung und Vegetationsfarbe, nicht zum Erfinden
einzelner Häuser. Dekoratives Modell, keine Vermessungsgrundlage.

## Daten und Attribution

- Gelände: [AWS Terrain Tiles / Mapzen](https://registry.opendata.aws/terrain-tiles/), SRTM-basierte Skadi-HGT-Kacheln S14W073 und S14W072; Abruf September 2026.
- Straßen, Gebäude und kartierte Vegetation: © [OpenStreetMap-Mitwirkende](https://www.openstreetmap.org/copyright), [ODbL](https://opendatacommons.org/licenses/odbl/1-0/). Overpass-Daten vom 13. September 2026; Flughafenabfrage vom 24. September, Server-Datenstand 15. Juli 2026.
- Zusätzliche Grundrisse: [Microsoft Global ML Building Footprints](https://github.com/microsoft/GlobalMLBuildingFootprints/), Stand 13. August 2026, [CDLA Permissive 2.0](https://cdla.dev/permissive-2-0/). Cusco-Kachel `210031023`; Download-URL, Filter und Prüfsummen in `data/cusco_buildings_ms.json`; vollständiger Lizenztext in `data/CDLA-Permissive-2.0.txt`.
- Landbedeckung: [ESA WorldCover 2021 v200, Zanaga et al.](https://doi.org/10.5281/zenodo.7254221), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). © ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium. Kacheln S15W075 und S15W072; Quellen und Prüfsummen in `data/cusco_worldcover_2021.json`.
- Schrift: DejaVu Sans Bold.
