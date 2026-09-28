# PLA-Farben für das Cusco-Modell

Diese Einkaufsempfehlung ergänzt die [Druckhinweise](output/print_v2/Druckhinweise.md)
für das Vierfarb-Modell auf dem **Bambu Lab P1S mit AMS**.
Dokumentiert am 28. September 2026 auf Grundlage der bisherigen Farbrecherche.

## Empfohlene Farben

Alle vier Filamente als **PLA mit mattem Finish, 1,75 mm Durchmesser** wählen.
Die gedeckten Naturfarben sollen die bestehende Modellgestaltung möglichst gut
wiedergeben. Die Einschätzung der Farbwirkung basiert auf den veröffentlichten
Farbangaben; ein physischer Vergleichsdruck steht noch aus.

| Modellteil | Zielfarbe im Modell | Filament und Link zu 3DJake Schweiz | Erwartete Farbwirkung |
| --- | --- | --- | --- |
| `01_Terrain_Sockel` – Gelände, Grundkörper und ebene Schriftfläche | Sand-/Erdbraun `#B8A17C` | [Polymaker Panchroma PLA Matte – Pastel Peanut](https://www.3djake.ch/de-CH/polymaker/panchroma-pla-matte-pastel-peanut) | Warmes Sandbraun; etwas wärmer als die Modellfarbe. |
| `02_Strassen_Schrift` – Strassen, Flughafen und „Cusco“ | Dunkles Steingrau `#64696C` | [3DJAKE mattePLA – Dunkelgrau / Dark Grey, RAL 7011](https://www.3djake.ch/en-CH/3djake/mattepla-dark-grey) | Gedämpftes Steingrau mit gutem Kontrast zum sandbraunen Gelände. |
| `03_Gebaeude` – Gebäude | Terrakotta `#AC5438` | [Polymaker Panchroma PLA Matte – Muted Terracotta](https://www.3djake.ch/de-CH/polymaker/panchroma-pla-matte-muted-terracotta) | Erdiges Ziegelrot; etwas heller und orangefarbener als die Modellfarbe. |
| `04_Vegetation` – Vegetationsflächen | Gedämpftes Grün `#637D46` | [Bambu Lab PLA Matte – Dark Green](https://www.3djake.ch/de-CH/bambu-lab/pla-matte-dark-green) | Gedecktes Olivgrün, passend zur vorgesehenen Vegetationsfarbe. |

Die Hex-Werte stammen aus [validation.json](output/print_v2/validation.json)
und beschreiben die digitalen Modellfarben, nicht gemessene Filamentfarben.
Die Auswahl nähert sich der Modellvorschau an; sie bildet keine vermessenen
oder jahreszeitlich exakten Landschaftsfarben Cuscos ab.

## Alternative für Terrakotta

Falls Polymaker Muted Terracotta nicht lieferbar ist, kommt
[GEEETECH PLA Matte – Terracotta](https://www.3djake.ch/de-CH/geeetech/pla-matte-terracotta)
als Alternative infrage. Dessen genaue Farbabweichung ist mangels eines
verifizierten Farbcodes schlechter einzuschätzen. Polymaker bleibt daher die
bevorzugte Auswahl für die geplante Farbwirkung.

## Bestellung und Vorbereitung

- Je Farbe die **1-kg-Ausführung mit Spule** wählen. Bei Bambu ist „Refill“
  nur sinnvoll, wenn eine passende wiederverwendbare Spule vorhanden ist.
- Verfügbarkeit und Preise direkt auf den verlinkten Shopseiten prüfen.
  Die Links führen zum Schweizer Shop; die graue Variante ist englischsprachig.
- Deckende Filamente verwenden. Im Projekt ist Spülen in die innere Füllung
  aktiviert; bei durchscheinendem Material könnten Mischfarben sichtbar werden.
- Vor dem vollständigen Druck eine kleine Probe mit allen vier Farben und
  derselben Farbschichtdicke wie im Modell drucken. Deckkraft und Übergänge
  beurteilen: Bildschirm, Produktfotos und Renderbeleuchtung erlauben keine
  Garantie für eine exakte Farbübereinstimmung.
- In [Cusco_P1S_AMS.3mf](output/print_v2/Cusco_P1S_AMS.3mf) die tatsächlichen
  Filamentprofile und AMS-Slots zuordnen, Spülmengen für die gewählten Farben
  prüfen und erneut slicen. Die Nummern der Modellteile sind keine zwingenden
  physischen AMS-Slotnummern.

Die vorhandene Schätzung von rund **308 g PLA inklusive Spülabfall** gilt für
das mitgelieferte Profil. Andere Filamente oder Spülmengen können Materialbedarf
und Druckzeit verändern.
