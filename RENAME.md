# Umbenennungs-Vorlage — PackagingOptimizer

Trage in der Spalte **NEU** den gewünschten Namen ein. Leer lassen = Name bleibt unverändert.
Danach kann Claude alle eingetragenen Namen im gesamten Projekt konsistent umbenennen.

## Legende


| Symbol | Bedeutung                                                                                                                                                                                                        |
| ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 🔗     | **Schnittstellen-Name.** Kommt als JSON-Key, localStorage-Schlüssel oder CSV-Spalte über eine Grenze (Backend ↔ Frontend ↔ Datei). Umbenennen betrifft immer *beide* Seiten — geht, muss aber überall mit. |
| 🔒     | **Fremdvorgabe.** Von MuJoCo, FastAPI, React, three.js o. ä. vorgegeben. Umbenennen bricht die Bibliothek — bitte nicht ändern.                                                                               |
| ↔     | Name kommt in mehreren Dateien vor; eine Änderung wirkt überall.                                                                                                                                               |

**Hinweis zu den Physik-Parametern (Zeilen 232–236):** Diese Namen stehen so auch in der Bachelorarbeit (`tab:parameterstand`, `tab:kalibrierung_uebersicht`). Wenn du sie umbenennst, muss der Text mitgezogen werden.

---

# BACKEND

## `backend/app/core/config.py`


| # | Alt                | Bedeutung                                           | NEU               |
| - | ------------------ | --------------------------------------------------- | ----------------- |
| 1 | `BASE_DIR`         | Wurzelverzeichnis von`backend/`                     | base_directory    |
| 2 | `DATA_DIR`         | Ordner`backend/data` (Stammdaten)                   | data_directory    |
| 3 | `STORAGE_DIR`      | Ordner`backend/storage`                             | storage_directory |
| 4 | `UPLOAD_DIR`       | Ablage der hochgeladenen STP-Dateien ↔             | upload_directory  |
| 5 | `CONVERTED_DIR`    | Ablage der konvertierten STL-Dateien ↔             | convert_directory |
| 6 | `BOXES_CSV`        | Pfad zur CSV mit allen verfügbaren Verpackungen ↔ | boxes_data        |
| 7 | `FRONTEND_ORIGINS` | Erlaubte CORS-Herkünfte des Frontends              | allowed_origins   |
| 8 | `origin`           | Laufvariable beim Zerlegen der Origin-Liste         | origin            |

## `backend/app/packing/models.py`


| #  | Alt                | Bedeutung                                                    | NEU |
| -- | ------------------ | ------------------------------------------------------------ | --- |
| 9  | `Item.length`      | Artikellänge in mm (x-Achse) 🔗 ↔                          |     |
| 10 | `Item.width`       | Artikelbreite in mm (y-Achse) 🔗 ↔                          |     |
| 11 | `Item.height`      | Artikelhöhe in mm (z-Achse) 🔗 ↔                           |     |
| 12 | `rotation_key`     | Achsen-Permutation als 3-Buchstaben-Code, z. B.`"zyx"` 🔗 ↔ |     |
| 13 | `dimensions`       | Kantenlängen-Tripel einer Orientierung ↔                   |     |
| 14 | `Box.name`         | Bezeichnung der Verpackung aus der CSV 🔗 ↔                 |     |
| 15 | `Box.length`       | Innenlänge der Verpackung in mm 🔗 ↔                       |     |
| 16 | `Box.width`        | Innenbreite der Verpackung in mm 🔗 ↔                       |     |
| 17 | `Box.height`       | Innenhöhe der Verpackung in mm 🔗 ↔                        |     |
| 18 | `Box.lhm_capacity` | Anzahl dieser Verpackungen je Ladehilfsmittel 🔗 ↔          |     |
| 19 | `Box.volume`       | Innenvolumen in mm³ (berechnet) ↔                          |     |

## `backend/app/packing/lhm.py`


| #  | Alt                     | Bedeutung                                         | NEU        |
| -- | ----------------------- | ------------------------------------------------- | ---------- |
| 20 | `LHM_LENGTH`            | Länge des Ladehilfsmittels, 570 mm               | lhm_length |
| 21 | `LHM_WIDTH`             | Breite des Ladehilfsmittels, 370 mm               | lhm_width  |
| 22 | `LHM_HEIGHT`            | Nutzhöhe des Ladehilfsmittels, 190 mm            | lhm_height |
| 23 | `EPS`                   | Rundungstoleranz beim Maßvergleich (1e-9)        | tolerance  |
| 24 | `get_lhm_capacity.box`  | Zu prüfende Verpackung                           |            |
| 25 | `get_lhm_capacity.best` | Bisher beste Stückzahl über alle Orientierungen |            |
| 26 | `L` / `W` / `H`         | Kantenlängen der aktuell geprüften Orientierung |            |
| 27 | `count`                 | Verpackungen je LHM in dieser Orientierung        |            |

## `backend/app/packing/box_loader.py`


| #  | Alt                                      | Bedeutung                                                          | NEU                |
| -- | ---------------------------------------- | ------------------------------------------------------------------ | ------------------ |
| 28 | `row`                                    | Eine Zeile der Verpackungs-CSV ↔                                  |                    |
| 29 | `stability`                              | Gewünschte Stabilitätsklasse ("1E"/"1B"/"Beliebig") 🔗 ↔        |                    |
| 30 | `"Stabilität"`                          | CSV-Spaltenname der Stabilitätsklasse 🔗                          |                    |
| 31 | `"Object Name"`                          | CSV-Spaltenname der Verpackungsbezeichnung 🔗                      |                    |
| 32 | `_box_from_row.box`                      | Aus einer CSV-Zeile gebaute Verpackung                             |                    |
| 33 | `rows`                                   | Alle CSV-Zeilen ↔                                                 |                    |
| 34 | `total_article_volume`                   | Gesamtvolumen aller Artikel einer VPE in mm³ ↔                   | article_volume_sum |
| 35 | `_load_pattern_boxes.boxes`              | Ergebnisliste des Packmuster-Vorfilters                            |                    |
| 36 | `_clamp.value`                           | Zu begrenzender Wert                                               |                    |
| 37 | `_clamp.lower`                           | Untere Schranke                                                    |                    |
| 38 | `_clamp.upper`                           | Obere Schranke                                                     |                    |
| 39 | `estimated_packing_density`              | Aus Referenzboxen geschätzte Schüttdichte (0–1) ↔              | expected_fillrate  |
| 40 | packing_density                          | Geklemmte Arbeits-Packdichte für den Vorfilter                    | fillrate           |
| 41 | `fitting_boxes`                          | Kandidaten, die rechnerisch passen (mit Überlaufquote)            | fitting_boxes      |
| 42 | `fallback_boxes`                         | Kandidaten, die rechnerisch zu klein sind                          |                    |
| 43 | `required_density`                       | Dichte, die diese Box erfordern würde                             |                    |
| 44 | `overflow_ratio`                         | `required_density / packing_density`; ≤ 1 = passt                 | fitting_ratio      |
| 45 | `entry`                                  | Tupel (Überlaufquote, Box) beim Sortieren                         |                    |
| 46 | `_unique_boxes_by_dimensions.unique`     | Duplikatfreie Boxliste                                             |                    |
| 47 | `seen_dimensions`                        | Bereits gesehene Maß-Tripel                                       | existing_dims      |
| 48 | `base_a` / `base_b`                      | Grundfläche, absteigend sortiert (L/B-unabhängig)                |                    |
| 49 | `_unique_boxes_by_dimensions.dimensions` | Normiertes Maß-Tripel für den Dublettencheck                     |                    |
| 50 | `csv_path`                               | Pfad zur Verpackungs-CSV                                           | box_data_path      |
| 51 | `quantity`                               | Artikelmenge je VPE ↔                                             |                    |
| 52 | `bulk`                                   | Schüttgut-Pfad ja/nein                                            |                    |
| 53 | `mesh_volume`                            | Volumen eines Artikels in mm³ 🔗 ↔                               |                    |
| 54 | `load_boxes_from_csv.path`               | CSV-Pfad als`Path`                                                 |                    |
| 55 | `csvfile`                                | Geöffneter CSV-Dateihandle                                        | box_data           |
| 56 | `load_boxes_from_csv.boxes`              | Gefilterte Kandidatenliste                                         |                    |
| 57 | `limit`                                  | Obergrenze des Kandidatenfelds (10 Schüttgut / 200 Packmuster) ↔ |                    |

## `backend/app/packing/optimizer.py`

### Felder von `PackingOptimizer`


| #  | Alt                            | Bedeutung                                                 | NEU          |
| -- | ------------------------------ | --------------------------------------------------------- | ------------ |
| 58 | `item`                         | Der zu verpackende Artikel ↔                             |              |
| 59 | `PackingOptimizer.quantity`    | Artikelmenge je VPE                                       |              |
| 60 | `PackingOptimizer.boxes`       | Kandidatenverpackungen                                    |              |
| 61 | `pattern`                      | Vom Nutzer im 3D-Editor gelegtes Packmuster 🔗 ↔         | packing_grid |
| 62 | `PackingOptimizer.mesh_volume` | Volumen eines Artikels in mm³                            |              |
| 63 | `fill_residual`                | Resträume neben dem Hauptraster auffüllen ja/nein 🔗 ↔ | fill_res     |
| 64 | `_toleranz`                    | Numerische Toleranz gegen Rundungsfehler (1e-9) ↔        | _tolerace    |

### `_fill_remaining_space`


| #  | Alt                               | Bedeutung                                         | NEU              |
| -- | --------------------------------- | ------------------------------------------------- | ---------------- |
| 65 | `region`                          | Restraum als Tupel (Ursprung + Restmaße) ↔      | res_space        |
| 66 | `orientations`                    | Erlaubte Artikelorientierungen                    |                  |
| 67 | `x0` / `y0` / `z0`                | Ursprungsecke des Restraums                       |                  |
| 68 | `rest_x` / `rest_y` / `rest_z`    | Restmaße des Raums                               |                  |
| 69 | `best_fit`                        | Beste Orientierung für diesen Restraum           | best_orientation |
| 70 | `orientation`                     | Aktuell geprüfte Orientierung ↔                 |                  |
| 71 | `length` / `width` / `height`     | Kantenlängen in aktueller Orientierung ↔        |                  |
| 72 | `count_x` / `count_y` / `count_z` | Artikel je Achse ↔                               |                  |
| 73 | `_fill_remaining_space.count`     | Artikel im Restraum gesamt                        |                  |
| 74 | `"dims"`                          | Dict-Key: Kantenlängen der Bestlösung ↔        |                  |
| 75 | `"grid"`                          | Dict-Key: Rasteranzahl der Bestlösung            |                  |
| 76 | `positions`                       | Liste der Artikelmittelpunkte 🔗 ↔               |                  |
| 77 | `pattern_index`                   | Index des Musterelements,`None` im Restraum 🔗 ↔ |                  |
| 78 | `rotation`                        | Zusatzrotation im Bogenmaß je Achse 🔗 ↔        |                  |

### `_unique_orientations`, `_normalized_elements`, `effective_article_volume`, `_pattern_step`


| #  | Alt                           | Bedeutung                                               | NEU       |
| -- | ----------------------------- | ------------------------------------------------------- | --------- |
| 79 | `_unique_orientations.unique` | Orientierungen ohne doppelte Kantenlängen              |           |
| 80 | `seen`                        | Bereits gesehene Kantenlängen-Tripel                   |           |
| 81 | `elements`                    | Elemente des Packmusters 🔗 ↔                          |           |
| 82 | `prepared_elements`           | Elemente mit ausgedrehten Abmessungen                   |           |
| 83 | `element`                     | Einzelnes Musterelement ↔                              |           |
| 84 | `min_x` / `min_y` / `min_z`   | Untere Ecke des Musters (zum Nullpunkt-Verschieben)     |           |
| 85 | `"index"`                     | Dict-Key: laufende Nummer des Musterelements 🔗         |           |
| 86 | `"position"`                  | Dict-Key: Position des Musterelements 🔗 ↔             |           |
| 87 | `"size"`                      | Dict-Key: Abmessungen des Musterelements 🔗 ↔          |           |
| 88 | `step_volume`                 | Volumen des Rasterquaders (Schrittweiten multipliziert) |           |
| 89 | `_pattern_step.key`           | Achsenbezeichner "x"/"y"/"z"                            |           |
| 90 | `full_dimension`              | Volle Kantenlänge als Fallback bei nur einem Artikel   | full_dims |
| 91 | `coords`                      | Sortierte Positionen entlang einer Achse                | positions |
| 92 | `gaps`                        | Abstände zwischen benachbarten Positionen              |           |

### `_fits_overlap`


| #   | Alt                                                         | Bedeutung                                           | NEU |
| --- | ----------------------------------------------------------- | --------------------------------------------------- | --- |
| 93  | `point`                                                     | Kandidatenecke für die Platzierung ↔              |     |
| 94  | `full_dims`                                                 | Tatsächliche Artikelmaße ↔                       |     |
| 95  | `effective_dims`                                            | Rasterschrittweiten = Mindestabstand ↔             |     |
| 96  | `placements`                                                | Bereits gesetzte Artikel (Ecke + Maße) ↔          |     |
| 97  | `px` / `py` / `pz`                                          | Koordinaten des Kandidatenpunkts ↔                 |     |
| 98  | `effective_length` / `effective_width` / `effective_height` | Mindestabstände je Achse ↔                        |     |
| 99  | `placed`                                                    | Bereits platzierter Artikel im Überlappungstest    |     |
| 100 | `dx` / `dy` / `dz`                                          | Achsabstand zum bereits platzierten Artikel         |     |
| 101 | `"x0"` / `"y0"` / `"z0"`                                    | Dict-Keys: Ursprungsecke eines platzierten Artikels |     |

### `_build_pattern_lookup`, `_find_best_orientation`


| #   | Alt                            | Bedeutung                                        | NEU                  |
| --- | ------------------------------ | ------------------------------------------------ | -------------------- |
| 102 | `base_steps`                   | Schrittweiten des Musters je Achse ↔            |                      |
| 103 | `step_x` / `step_y` / `step_z` | Rasterabstand je Achse ↔                        |                      |
| 104 | `lookup`                       | Zuordnung Rasterzelle → Rotation + Musterindex  |                      |
| 105 | `ix` / `iy` / `iz`             | Rasterindizes einer Zelle ↔                     |                      |
| 106 | `pattern_grid`                 | Größe des Musters in Zellen ↔                 |                      |
| 107 | `base_dimensions`              | Maximale Artikelmaße je Achse aus dem Muster ↔ |                      |
| 108 | `unique_orientations`          | Duplikatfreie Orientierungen (für den Restraum) |                      |
| 109 | `best`                         | Beste gefundene Orientierung mit Kennzahlen ↔   |                      |
| 110 | `axis_x` / `axis_y` / `axis_z` | Achsenbuchstaben aus dem`rotation_key`           |                      |
| 111 | `main_capacity`                | Kapazität des Hauptrasters                      | grid_capacity        |
| 112 | `used_x` / `used_y` / `used_z` | Vom Hauptraster belegte Maße                    |                      |
| 113 | `residual_positions`           | Artikelpositionen in den Resträumen ↔          | res_positions        |
| 114 | `residual_count`               | Artikelzahl in den Resträumen                   | res_capacity         |
| 115 | `regions`                      | Die drei Restraum-Quader neben dem Hauptraster   | res_regions          |
| 116 | `region_positions`             | Positionen aus einem Restraum                    | res_region_positions |
| 117 | `region_count`                 | Artikelzahl aus einem Restraum                   | res_region_count     |
| 118 | `total_capacity`               | Hauptraster + Resträume                         |                      |
| 119 | `required_main`                | Im Hauptraster tatsächlich benötigte Artikel   |                      |
| 120 | `used_layers_z`                | Tatsächlich benötigte Lagen in z               |                      |
| 121 | `compact_used_z`               | Höhe nur der benötigten Lagen                  |                      |
| 122 | `estimated_used_volume`        | Geschätzt belegtes Volumen (Rankingkriterium)   | expected_used_volume |
| 123 | `excess_capacity`              | Überkapazität gegenüber der VPE-Menge         | overcapacity         |
| 124 | `score`                        | Sortierschlüssel (−Überkapazität, −Volumen) | sort_score           |
| 125 | `"steps"`                      | Dict-Key: Schrittweiten der Bestlösung          |                      |
| 126 | `"capacity"`                   | Dict-Key: Gesamtkapazität 🔗 ↔                 |                      |

### `_place_articles`, `_build_result`, `_rotated_size`, `_pack_pattern`, `find_top_boxes`


| #   | Alt                                                   | Bedeutung                                                         | NEU           |
| --- | ----------------------------------------------------- | ----------------------------------------------------------------- | ------------- |
| 127 | `pattern_lookup`                                      | Rasterzelle → Rotation/Index ↔                                  |               |
| 128 | `pattern_nx` / `pattern_ny` / `pattern_nz`            | Musterausdehnung in Zellen je Achse                               |               |
| 129 | `extreme_points`                                      | Freie Ecken für die nächste Platzierung (Extreme-Point-Packing) |               |
| 130 | `placed_in_round`                                     | Wurde in dieser Runde ein Artikel gesetzt?                        |               |
| 131 | `pattern_key`                                         | Zellindex modulo Musterausdehnung                                 |               |
| 132 | `pattern_match`                                       | Am Rasterpunkt gültige Rotation + Musterindex                    |               |
| 133 | `article_length` / `article_width` / `article_height` | Artikelmaße in der Bestorientierung                              |               |
| 134 | `single_volume`                                       | Volumen eines Artikels                                            |               |
| 135 | `used_volume`                                         | Volumen aller Artikel zusammen                                    |               |
| 136 | `"box"`                                               | Ergebnis-Key: Verpackungsname 🔗 ↔                               |               |
| 137 | `"box_dimensions"`                                    | Ergebnis-Key: Innenmaße der Verpackung 🔗 ↔                     |               |
| 138 | `"article_dims"`                                      | Ergebnis-Key: Artikelmaße in Bestorientierung 🔗 ↔              |               |
| 139 | `"scaledLength"`                                      | Ergebnis-Key: skalierte Artikellänge 🔗 ↔                       |               |
| 140 | `"fill_rate"`                                         | Ergebnis-Key: Füllgrad 0–1 🔗 ↔                                |               |
| 141 | `_rotated_size.size`                                  | Abmessungen vor der Rotation                                      |               |
| 142 | `_rotated_size.rotation`                              | Rotation im Bogenmaß je Achse                                    |               |
| 143 | `dims`                                                | Abmessungen, die durch die Rotationen getauscht werden            |               |
| 144 | `quarter_turn`                                        | 90° im Bogenmaß (1.5707963…)                                   |               |
| 145 | `rx` / `ry` / `rz`                                    | Anzahl Vierteldrehungen je Achse                                  |               |
| 146 | `residual_position`                                   | Einzelne Restraumposition beim Auffüllen                         | res_positions |
| 147 | `find_top_boxes.limit`                                | Maximale Anzahl Ergebnisse                                        |               |
| 148 | `candidates`                                          | Ergebnisse aller passenden Verpackungen                           |               |

## `backend/app/geometry.py`


| #   | Alt                                | Bedeutung                                                   | NEU      |
| --- | ---------------------------------- | ----------------------------------------------------------- | -------- |
| 149 | `file_url`                         | URL/Pfad der STL, aus dem der Dateiname gezogen wird 🔗 ↔  | stl_url  |
| 150 | `resolve_converted_stl.filename`   | Reiner Dateiname der STL                                    | stl_name |
| 151 | `resolve_converted_stl.path`       | Absoluter Pfad im`converted`-Ordner                         |          |
| 152 | `VHACD_PARAMS`                     | Parametersatz der konvexen Zerlegung ↔                     |          |
| 153 | `maxConvexHulls`                   | 🔒 V-HACD: Zahl der Teilkörper (5)                         |          |
| 154 | `resolution`                       | 🔒 V-HACD: Voxelauflösung (300 000)                        |          |
| 155 | `maxNumVerticesPerCH`              | 🔒 V-HACD: Vertices je Teilkörper (32)                     |          |
| 156 | `minimumVolumePercentErrorAllowed` | 🔒 V-HACD: erlaubter Volumenfehler in %                     |          |
| 157 | `raw`                              | Serialisierte Parameter für den Cache-Fingerprint          |          |
| 158 | `stl_path`                         | Pfad zur STL-Datei ↔                                       |          |
| 159 | `cache`                            | Pfad der gecachten`.vhacd-<tag>.npz`                        |          |
| 160 | `mesh`                             | Geladenes Dreiecksnetz ↔                                   |          |
| 161 | `parts`                            | Konvexe Teilkörper aus der Zerlegung ↔                    |          |
| 162 | `stl_file`                         | STL-Pfad (Parameter der Volumenberechnung) 🔗 ↔            |          |
| 163 | `scaled_length`                    | Ziel-Artikellänge in mm für die Skalierung 🔗 ↔          |          |
| 164 | `vol`                              | Volumen der konvexen Hülle in mm³                         |          |
| 165 | `size_x`                           | Länge der Bounding-Box in x (Bezug für den Skalierfaktor) |          |

## `backend/app/services/converterStpStl/converter.py`


| #   | Alt                     | Bedeutung                             | NEU |
| --- | ----------------------- | ------------------------------------- | --- |
| 166 | `input_step`            | Pfad der hochgeladenen STP-Datei      |     |
| 167 | `output_stl`            | Zielpfad der erzeugten STL            |     |
| 168 | `step_to_stl_cq.result` | Von CadQuery importiertes STEP-Modell |     |

## `backend/app/simulation/common.py` — `SimulationConfig`


| #   | Alt                            | Bedeutung                                          | NEU                |
| --- | ------------------------------ | -------------------------------------------------- | ------------------ |
| 169 | `SimulationConfig.item`        | Geometrie eines Artikels 🔗                        |                    |
| 170 | `item_quantity`                | Artikelmenge je VPE 🔗 ↔                          |                    |
| 171 | `SimulationConfig.boxes`       | Zu simulierende Kandidatenverpackungen 🔗          |                    |
| 172 | `SimulationConfig.mesh_volume` | Volumen eines Artikels in mm³                     |                    |
| 173 | `SimulationConfig.stl_file`    | Pfad der Visual-STL 🔗                             |                    |
| 174 | `SimulationConfig.stability`   | Stabilitätsfilter 🔗                              |                    |
| 175 | `collision_file`               | Pfad der V-HACD-npz mit den Kollisionsteilen ↔    | vhacd_file         |
| 176 | `item_mass`                    | Masse eines Artikels in kg (0,01)                  |                    |
| 177 | `mesh_scale`                   | Skalierung mm → m je Achse 🔗 ↔                  |                    |
| 178 | `wall_thickness`               | Dicke von Boden und Wänden in m ↔                |                    |
| 179 | `fixed_time_step`              | Zeitschritt der Physik in s (0,002) ↔             |                    |
| 180 | `solver_iterations`            | Newton-Iterationen je Schritt (30) ↔              |                    |
| 181 | `max_simulation_steps`         | Obergrenze Zeitschritte je Phase ↔                |                    |
| 182 | `min_simulation_steps`         | Mindestschritte vor der Ruheprüfung ↔            |                    |
| 183 | `early_validation_factor`      | Abbruch, wenn Schütthöhe > Faktor × Boxhöhe ↔ | early_cancel_value |
| 184 | `settle_duration`              | Dauer der Rüttelphase in s ↔                     |                    |
| 185 | `settle_force_scale`           | Amplitude der Rüttelkraft in N ↔                 |                    |
| 186 | `settle_frequency`             | Frequenz der Rüttelkraft in Hz ↔                 |                    |
| 187 | `fit_height_tolerance`         | Erlaubte Überschreitung der Innenhöhe (0) ↔     |                    |
| 188 | `random_seed`                  | Basis-Startwert des Zufallsgenerators 🔗 ↔        |                    |
| 189 | `runs_per_box`                 | Läufe je Verpackung für die Mittelung 🔗 ↔      |                    |
| 190 | `use_gui`                      | MuJoCo-Viewer anzeigen (Debug/Replay) ↔           |                    |
| 191 | `parallel_simulations`         | Boxen parallel simulieren ↔                       |                    |
| 192 | `max_workers`                  | Obergrenze paralleler Prozesse ↔                  |                    |
| 193 | `box_x` / `box_y` / `box_z`    | Innenmaße der ersten Box in m ↔                  |                    |

## `backend/app/simulation/common.py` — Funktionen


| #   | Alt                                                   | Bedeutung                                         | NEU                  |
| --- | ----------------------------------------------------- | ------------------------------------------------- | -------------------- |
| 194 | `simulation_results`                                  | Rohergebnisse aller Boxen ↔                      |                      |
| 195 | `valid_results`                                       | Ergebnisse, die passen und keine Ausbrecher haben |                      |
| 196 | `result`                                              | Einzelnes Ergebnis-Dict ↔                        |                      |
| 197 | `config`                                              | Simulationskonfiguration ↔                       |                      |
| 198 | `_build_dynamic_reference_boxes.total_article_volume` | Gesamtvolumen aller Artikel in m³                |                      |
| 199 | `estimated_bulk_volume`                               | Geschätztes Schüttvolumen bei 30 % Dichte       | expected_bulk_volume |
| 200 | `_build_dynamic_reference_boxes.boxes`                | Die drei erzeugten Referenzboxen                  |                      |
| 201 | `"ref_small"` / `"ref_medium"` / `"ref_large"`        | Namen der drei Referenzboxen                      |                      |
| 202 | `length_m` / `width_m`                                | Grundfläche der Referenzbox in m                 |                      |
| 203 | `height_m`                                            | Errechnete Höhe der Referenzbox in m             |                      |

## `backend/app/simulation/sim_mujoco.py` — Modulparameter (Physik)


| #   | Alt                 | Bedeutung                                       | NEU |
| --- | ------------------- | ----------------------------------------------- | --- |
| 204 | `object_friction`   | Gleitreibungskoeffizient (0,2)                  |     |
| 205 | `spinning_friction` | Bohrreibung (0,01)                              |     |
| 206 | `rolling_friction`  | Rollreibung (0,01)                              |     |
| 207 | `joint_damping`     | Dämpfung am Free-Joint (0,08)                  |     |
| 208 | `pressing_gravity`  | Ersatzschwerkraft während des Rüttelns (−60) |     |

## `backend/app/simulation/sim_mujoco.py` — Modulfunktionen


| #   | Alt                                     | Bedeutung                                               | NEU |
| --- | --------------------------------------- | ------------------------------------------------------- | --- |
| 209 | `_box_seed_offset.box`                  | Verpackung, aus deren Maßen der Seed-Versatz kommt     |     |
| 210 | `_box_seed_offset.key`                  | Maß-String, aus dem die CRC32-Prüfsumme gebildet wird |     |
| 211 | `args`                                  | Argumenttupel (Config, Box, Index) für den Worker ↔   |     |
| 212 | `box_index`                             | Position der Box im Kandidatenfeld (nur Signatur)       |     |
| 213 | `n_runs`                                | Anzahl Läufe für diese Box                            |     |
| 214 | `runs`                                  | Einzelergebnisse aller Läufe                           |     |
| 215 | `seed_offset`                           | Aus den Boxmaßen abgeleiteter Seed-Versatz             |     |
| 216 | `run_index`                             | Laufende Nummer des Einzellaufs                         |     |
| 217 | `single_box_config`                     | Config, auf genau eine Box reduziert ↔                 |     |
| 218 | `mean_height`                           | Über die Läufe gemittelte Füllhöhe                  |     |
| 219 | `heights`                               | Füllhöhen der Einzelläufe                            |     |
| 220 | `variance`                              | Varianz der Füllhöhen                                 |     |
| 221 | `current_box`                           | Referenzbox in der aktuellen Vergrößerungsstufe       |     |
| 222 | `attempt`                               | Nummer der Nachvergrößerung (0–3)                    |     |
| 223 | `single_config`                         | Config für einen Referenzbox-Lauf                      |     |
| 224 | `_reference_box_density.scale`          | Vergrößerungsfaktor 1,25 je Versuch                   |     |
| 225 | `reference_boxes`                       | Die drei dynamischen Referenzboxen                      |     |
| 226 | `executor`                              | Prozesspool ↔                                          |     |
| 227 | `densities`                             | Gemessene Packdichten der Referenzboxen                 |     |
| 228 | `density`                               | Einzelne gemessene Packdichte                           |     |
| 229 | `roll` / `pitch` / `yaw`                | Euler-Winkel für die Spawn-Rotation                    |     |
| 230 | `cr` / `sr` / `cp` / `sp` / `cy` / `sy` | Cosinus/Sinus der halben Euler-Winkel                   |     |
| 231 | `obj_path`                              | Pfad der zu zerlegenden OBJ-Datei                       |     |
| 232 | `_parse_obj_groups.vertices`            | Alle Vertices der OBJ                                   |     |
| 233 | `groups`                                | Vertexindizes je OBJ-Gruppe                             |     |
| 234 | `current`                               | Indizes der gerade gelesenen Gruppe                     |     |
| 235 | `line`                                  | Aktuelle OBJ-Zeile                                      |     |
| 236 | `token`                                 | Face-Eintrag der Form`v/vt/vn`                          |     |
| 237 | `vertex_array`                          | Vertices als numpy-Array                                |     |
| 238 | `indices`                               | Vertexindizes einer Gruppe ↔                           |     |

## `backend/app/simulation/sim_mujoco.py` — `PackagingSimulation`


| #   | Alt                                          | Bedeutung                                                 | NEU                      |
| --- | -------------------------------------------- | --------------------------------------------------------- | ------------------------ |
| 239 | `self.config`                                | Simulationskonfiguration ↔                               |                          |
| 240 | `self.item`                                  | Artikelgeometrie                                          |                          |
| 241 | `self.model`                                 | 🔒 Kompiliertes MuJoCo-Modell                             |                          |
| 242 | `self.data`                                  | 🔒 MuJoCo-Zustandsdaten ↔                                |                          |
| 243 | `self._viewer`                               | MuJoCo-Viewerfenster (nur GUI-Modus)                      |                          |
| 244 | `self._next_frame_time`                      | Zielzeit des nächsten Bildes (Echtzeitbremse)            |                          |
| 245 | `self._aborted`                              | Lauf wurde abgebrochen (Fenster zu)                       |                          |
| 246 | `self.article_body_ids`                      | MuJoCo-Body-IDs aller Artikel                             |                          |
| 247 | `self._article_geom_vertices`                | (Geom-ID, Vertices) je Kollisionsteil                     | `_article_mesh_vertices` |
| 248 | `self.article_x` / `article_y` / `article_z` | Artikelmaße in m                                         |                          |
| 249 | `self._lid_bottom_z`                         | Unterkante des abgesetzten Deckels in m                   | _lid_pos                 |
| 250 | `simulation_args`                            | Argumenttupel für alle Boxen                             |                          |
| 251 | `PackagingSimulation.run.max_workers`        | Tatsächliche Zahl paralleler Prozesse                    |                          |
| 252 | `spawn_states`                               | Startpositionen und -rotationen aller Artikel ↔          |                          |
| 253 | `cfg`                                        | Kurzform von`self.config` ↔                              |                          |
| 254 | `half_x` / `half_y`                          | Halbe Boxinnenmaße in m ↔                               |                          |
| 255 | `floor_top`                                  | Oberkante des Bodens = Nullhöhe der Schüttung ↔        | floor_height             |
| 256 | `escaped`                                    | Zähler ausgebrochener Artikel                            | escaped_articles         |
| 257 | `body_id`                                    | MuJoCo-Body-ID eines Artikels ↔                          |                          |
| 258 | `geom_start`                                 | Erste Geom-ID des Bodys ↔                                |                          |
| 259 | `geom_count`                                 | Anzahl Geoms des Bodys ↔                                 |                          |
| 260 | `weighted_sum`                               | Vertexgewichtete Summe für den Schwerpunkt               |                          |
| 261 | `vertex_total`                               | Gesamtzahl gewerteter Vertices                            |                          |
| 262 | `geom_id`                                    | MuJoCo-Geom-ID ↔                                         |                          |
| 263 | `mesh_id`                                    | MuJoCo-Mesh-ID ↔                                         |                          |
| 264 | `_count_escaped_articles.start` / `.count`   | Vertexbereich des Meshes                                  |                          |
| 265 | `_count_escaped_articles.vertices`           | Vertices eines Kollisionsteils ↔                         |                          |
| 266 | `_count_escaped_articles.rotation`           | Rotationsmatrix des Geoms ↔                              |                          |
| 267 | `centre`                                     | Schwerpunkt der Kollisionsteile eines Artikels            |                          |
| 268 | `cols_x` / `cols_y`                          | Spalten des Spawn-Rasters ↔                              |                          |
| 269 | `ux` / `uy`                                  | Halbe nutzbare Grundfläche in m ↔                       |                          |
| 270 | `per_layer`                                  | Rasterplätze je Lage ↔                                  |                          |
| 271 | `_plan_spawn_positions.step_x` / `.step_y`   | Rasterabstand beim Spawnen                                |                          |
| 272 | `cells`                                      | Verwürfelte Rasterzellen                                 |                          |
| 273 | `states`                                     | Erzeugte Spawn-Zustände                                  |                          |
| 274 | `layer`                                      | Lagennummer beim Spawnen ↔                               |                          |
| 275 | `cx` / `cy`                                  | Zellindizes im Spawn-Raster                               |                          |
| 276 | `jitter_limit_x` / `jitter_limit_y`          | Maximaler Zufallsversatz je Achse                         |                          |
| 277 | `jitter_x` / `jitter_y`                      | Tatsächlicher Zufallsversatz                             |                          |
| 278 | `x_pos` / `y_pos` / `z_pos`                  | Spawnkoordinaten in m                                     |                          |
| 279 | `quat`                                       | Spawn-Quaternion (w, x, y, z)                             |                          |
| 280 | `_spawn_grid.gap`                            | 5 mm Luft zwischen Rasterzellen                           |                          |
| 281 | `cell`                                       | Kantenlänge einer Rasterzelle                            |                          |
| 282 | `margin`                                     | Randabstand zur Wand beim Spawnen                         |                          |
| 283 | `highest_layer`                              | Oberste belegte Spawn-Lage                                |                          |
| 284 | `highest_spawn_z`                            | Höhe des obersten Spawns in m                            |                          |
| 285 | `_collision_part_vertices.scale`             | Skalierungsvektor mm → m                                 |                          |
| 286 | `_collision_part_vertices.data`              | Geladenes npz mit den Kollisionsteilen                    |                          |
| 287 | `wall_height`                                | Höhe der Kollisionswände (bis über den obersten Spawn) |                          |
| 288 | `visual_height`                              | Höhe der sichtbaren, transparenten Boxwände             |                          |
| 289 | `wall_floor_overlap`                         | Überlappung Wand/Boden gegen Spaltbildung                |                          |
| 290 | `wall_center_z`                              | Mittelpunkthöhe der Kollisionswände                     |                          |
| 291 | `visual_center_z`                            | Mittelpunkthöhe der Sichtwände                          |                          |
| 292 | `friction`                                   | Fertiger MJCF-Attributstring für Reibung/`condim`        |                          |
| 293 | `safety_wall_gap`                            | Abstand der äußeren Sicherheitswand (aktuell ungenutzt) |                          |
| 294 | `safety_wall_thickness`                      | Dicke der Sicherheitswand (aktuell ungenutzt)             |                          |
| 295 | `safety_half_t`                              | Halbe Sicherheitswanddicke (aktuell ungenutzt)            |                          |
| 296 | `_build_scene_xml.stl_path`                  | Absoluter STL-Pfad für das Visual-Mesh                   |                          |
| 297 | `part_vertices`                              | Vertices aller Kollisionsteile                            |                          |
| 298 | `mass_per_part`                              | Masse je Kollisionsteil (Artikelmasse / Teilezahl)        |                          |
| 299 | `mesh_assets`                                | MJCF-Block mit allen`<mesh>`-Definitionen                 |                          |
| 300 | `collision_geoms`                            | MJCF-Block mit allen Kollisions-Geoms                     |                          |
| 301 | `scale_str`                                  | Skalierung als MJCF-Attributstring                        |                          |
| 302 | `articles`                                   | MJCF-Block mit allen Artikel-Bodies                       |                          |
| 303 | `"article_{i}"`                              | Namensschema der Artikel-Bodies ↔                        |                          |
| 304 | `half_t`                                     | Halbe Wanddicke in m ↔                                   |                          |
| 305 | `walls`                                      | MJCF-Block Boden + Wände                                 |                          |
| 306 | `_build_scene_xml.gap`                       | 1 mm Untermaß des Deckels gegen Wandklemmen              |                          |
| 307 | `lid`                                        | MJCF-Block des Mocap-Deckels                              |                          |
| 308 | `"lid"` / `"lid_geom"`                       | MJCF-Namen des Deckelkörpers ↔                          |                          |
| 309 | `camera_extent`                              | Bezugsgröße für den Kameraausschnitt                   |                          |
| 310 | `vert_start` / `vert_count`                  | Vertexbereich beim Einsammeln der Geoms                   |                          |
| 311 | `remaining`                                  | Restwartezeit bis zum nächsten Bild                      |                          |
| 312 | `filling_height`                             | Höhe der Schüttung über dem Boden in m ↔              |                          |
| 313 | `lid_body`                                   | MuJoCo-Body-ID des Deckels                                |                          |
| 314 | `mocap_id`                                   | Mocap-Index des Deckels                                   |                          |
| 315 | `rim_z`                                      | Höhe der Boxoberkante in m ↔                            | box_height               |
| 316 | `lid_z`                                      | Aktuelle Deckelhöhe in m                                 |                          |
| 317 | `lid_speed`                                  | Absenkgeschwindigkeit des Deckels (0,03 m/s)              |                          |
| 318 | `sweep_z`                                    | Deckelhöhe während des Abstreifens                      | ersetzen durch lid_z     |
| 319 | `sweep_steps`                                | Zeitschritte der Abstreifphase                            |                          |
| 320 | `max_z`                                      | Höchster Punkt der Schüttung in m                       |                          |
| 321 | `_current_max_z.top`                         | Oberkante eines einzelnen Kollisionsteils                 |                          |
| 322 | `step`                                       | Schrittzähler in den Simulationsschleifen ↔             |                          |
| 323 | `duration`                                   | Dauer der Rüttelphase in s                               |                          |
| 324 | `force_scale`                                | Amplitude der Rüttelkraft                                |                          |
| 325 | `frequency`                                  | Frequenz der Rüttelkraft                                 |                          |
| 326 | `steps`                                      | Zahl der Zeitschritte in der Rüttelphase                 |                          |
| 327 | `t`                                          | Zeit seit Beginn der Rüttelphase in s                    |                          |
| 328 | `force_x` / `force_y`                        | Momentane Rüttelkraft je Achse                           |                          |
| 329 | `settled_height`                             | Schütthöhe VOR dem Deckelandruck in m                   |                          |
| 330 | `single_article_volume`                      | Volumen eines Artikels in m³                             |                          |
| 331 | `_evaluate.total_article_volume`             | Volumen aller Artikel in m³                              |                          |
| 332 | `used_box_volume`                            | Von der Schüttung beanspruchtes Volumen in m³           |                          |
| 333 | `box_volume`                                 | Gesamtes Innenvolumen der Box in m³                      |                          |
| 334 | `_evaluate.packing_density`                  | Dichte der Schüttung in sich (0–1)                      |                          |
| 335 | `box_utilization`                            | Auslastung der ganzen Box (0–1) →`fill_rate_percent`    | fill_rate_percent        |
| 336 | `results`                                    | Ergebnis-Dict eines Laufs ↔                              |                          |

## Ergebnis-Keys der Simulation (Backend → Frontend) 🔗


| #   | Alt                               | Bedeutung                                          | NEU |
| --- | --------------------------------- | -------------------------------------------------- | --- |
| 337 | `filling_height_m`                | Füllhöhe in m (nur im Abbruchfall gesetzt)       |     |
| 338 | `filling_height_mm`               | Füllhöhe in mm nach Deckelandruck ↔             |     |
| 339 | `relative_filling_height_percent` | Füllhöhe bezogen auf die Innenhöhe in % ↔      |     |
| 340 | `total_article_volume_cm3`        | Theoretisches Artikelvolumen gesamt in cm³        |     |
| 341 | `used_box_volume_cm3`             | Beanspruchtes Boxvolumen in cm³                   |     |
| 342 | `packing_density_percent`         | Schüttdichte in % ↔                              |     |
| 343 | `fits_in_box`                     | Passt-Urteil ↔                                    |     |
| 344 | `fill_rate_percent`               | Füllgrad der ganzen Box in % ↔                   |     |
| 345 | `aborted`                         | Lauf wurde abgebrochen ↔                          |     |
| 346 | `escaped_articles`                | Zahl der ausgebrochenen Artikel ↔                 |     |
| 347 | `filling_height_std_mm`           | Standardabweichung der Füllhöhe über die Läufe |     |
| 348 | `articles_per_lhm`                | Artikel je Ladehilfsmittel ↔                      |     |

## `backend/app/api/routes/simulation.py`


| #   | Alt                                      | Bedeutung                                              | NEU |
| --- | ---------------------------------------- | ------------------------------------------------------ | --- |
| 349 | `RequestedBox`                           | Vom Client für das Replay gewählte Verpackung 🔗     |     |
| 350 | `SingleBoxSimulationRequest.config`      | Ursprüngliche Simulationskonfiguration 🔗             |     |
| 351 | `SingleBoxSimulationRequest.box`         | Zu wiederholende Verpackung 🔗                         |     |
| 352 | `SingleBoxSimulationRequest.random_seed` | Basis-Seed des Originallaufs 🔗                        |     |
| 353 | `router`                                 | FastAPI-Router des Moduls ↔                           |     |
| 354 | `stl_path`                               | Aufgelöster Pfad der Visual-STL ↔                    |     |
| 355 | `error`                                  | Abgefangene Ausnahme ↔                                |     |
| 356 | `collision_path`                         | Pfad der V-HACD-npz ↔                                 |     |
| 357 | `reference_config`                       | Config für die Referenzbox-Dichteschätzung           |     |
| 358 | `simulation`                             | Instanz von`PackagingSimulation` ↔                    |     |
| 359 | `request`                                | Eingehender Replay-Request                             |     |
| 360 | `requested_box`                          | Vom Client übergebene Boxmaße                        |     |
| 361 | `selected_box`                           | Daraus gebaute`Box` mit neu berechneter LHM-Kapazität |     |

## `backend/app/api/routes/packing.py`


| #   | Alt                                  | Bedeutung                                             | NEU |
| --- | ------------------------------------ | ----------------------------------------------------- | --- |
| 362 | `Vec3`                               | 3D-Vektor im Request 🔗                               |     |
| 363 | `PatternElementRequest`              | Ein Element des Packmusters 🔗                        |     |
| 364 | `PatternRequest`                     | Das gesamte Packmuster 🔗                             |     |
| 365 | `PackingRequest`                     | Anfrage an`/packing/top20` 🔗                         |     |
| 366 | `item_width`                         | Artikelbreite in mm 🔗 ↔                             |     |
| 367 | `item_height`                        | Artikelhöhe in mm 🔗 ↔                              |     |
| 368 | `get_top_20_packing_results.data`    | Deserialisierter Request ↔                           |     |
| 369 | `optimizer`                          | Instanz von`PackingOptimizer`                         |     |
| 370 | `get_top_20_packing_results.results` | Gefundene Verpackungen 🔗 ↔                          |     |
| 371 | `"message"`                          | Ergebnis-Key: Meldungstext für die Oberfläche 🔗 ↔ |     |

## `backend/app/api/routes/uploads.py`


| #   | Alt                            | Bedeutung                                       | NEU |
| --- | ------------------------------ | ----------------------------------------------- | --- |
| 372 | `get_item_from_stl.stl_path`   | Pfad der eingelesenen STL                       |     |
| 373 | `bounds`                       | Bounding-Box des Meshes (min/max)               |     |
| 374 | `min_bounds` / `max_bounds`    | Untere/obere Ecke der Bounding-Box              |     |
| 375 | `get_item_from_stl.dimensions` | Kantenlängen der Bounding-Box                  |     |
| 376 | `file`                         | 🔒 Hochgeladene Datei (FastAPI-`UploadFile`) ↔ |     |
| 377 | `file_id`                      | Zufällige UUID des Uploads 🔗 ↔               |     |
| 378 | `input_path`                   | Zielpfad der STP-Datei                          |     |
| 379 | `output_path`                  | Zielpfad der STL-Datei ↔                       |     |
| 380 | `buffer`                       | Schreib-Handle beim Kopieren ↔                 |     |
| 381 | `item`                         | Aus der STL gelesene Artikelmaße 🔗 ↔         |     |
| 382 | `e`                            | Abgefangene Ausnahme ↔                         |     |

## `backend/app/api/main.py`


| #   | Alt                 | Bedeutung                                                     | NEU |
| --- | ------------------- | ------------------------------------------------------------- | --- |
| 383 | `app`               | 🔒 FastAPI-Anwendung (von`uvicorn app.api.main:app` erwartet) |     |
| 384 | `uploads_router`    | Router der Upload-Endpunkte                                   |     |
| 385 | `packing_router`    | Router der Packmuster-Endpunkte                               |     |
| 386 | `simulation_router` | Router der Simulations-Endpunkte                              |     |

---

# FRONTEND

## `frontend/lib/api/clients.ts`


| #   | Alt            | Bedeutung                                        | NEU |
| --- | -------------- | ------------------------------------------------ | --- |
| 387 | `API_BASE_URL` | Basis-URL des Backends                           |     |
| 388 | `apiUrl`       | Baut aus einem Pfad eine absolute Backend-URL ↔ |     |
| 389 | `apiUrl.path`  | Endpunktpfad, z. B.`/packing/top20`              |     |
| 390 | `base`         | Basis-URL ohne Schrägstrich am Ende             |     |
| 391 | `suffix`       | Pfad mit garantiertem führendem Schrägstrich   |     |

## `frontend/lib/api/uploads.ts`


| #   | Alt              | Bedeutung                                   | NEU |
| --- | ---------------- | ------------------------------------------- | --- |
| 392 | `uploadStlFile`  | Lädt eine STL hoch                         |     |
| 393 | `uploadStepFile` | Lädt eine STP hoch und lässt konvertieren |     |
| 394 | `formData`       | 🔒`FormData` mit der Datei ↔               |     |
| 395 | `response`       | Antwort des Backends ↔                     |     |

## `frontend/lib/packing.ts`


| #   | Alt                              | Bedeutung                                 | NEU |
| --- | -------------------------------- | ----------------------------------------- | --- |
| 396 | `RotationKey`                    | Typ der sechs Achsen-Permutationen ↔     |     |
| 397 | `PositionItem`                   | Ein platzierter Artikel im Ergebnis 🔗 ↔ |     |
| 398 | `PackingResult`                  | Ergebnis für eine Verpackung 🔗 ↔       |     |
| 399 | `PackingResponse`                | Gesamte Antwort von`/packing/top20` 🔗 ↔ |     |
| 400 | `getRotationFromKey`             | Wandelt`rotation_key` in Grad-Rotation ↔ |     |
| 401 | `getRotationFromKey.rotationKey` | Zu übersetzender Achsen-Code             |     |

## `frontend/app/positioning/utils/params.ts`


| #   | Alt                  | Bedeutung                               | NEU |
| --- | -------------------- | --------------------------------------- | --- |
| 402 | `getNumberParam`     | Liest einen Zahlenwert aus der Query ↔ |     |
| 403 | `sp`                 | 🔒`ReadonlyURLSearchParams` ↔          |     |
| 404 | `getNumberParam.key` | Name des Query-Parameters               |     |
| 405 | `fallback`           | Vorgabewert, wenn der Parameter fehlt   |     |
| 406 | `v`                  | Rohwert des Parameters                  |     |
| 407 | `n`                  | In Zahl umgewandelter Rohwert           |     |

## `frontend/app/positioning/hooks/useFileUrl.ts`


| #   | Alt          | Bedeutung                                    | NEU |
| --- | ------------ | -------------------------------------------- | --- |
| 408 | `useFileUrl` | Hook: liest die STL-URL aus dem localStorage |     |
| 409 | `fileUrl`    | URL der konvertierten STL ↔                 |     |
| 410 | `storedUrl`  | Rohwert aus dem localStorage                 |     |

## `frontend/app/positioning/hooks/useGridPositions.ts`


| #   | Alt                | Bedeutung                                          | NEU |
| --- | ------------------ | -------------------------------------------------- | --- |
| 411 | `useGridPositions` | Hook: erzeugt das 2×2×2-Startraster ↔           |     |
| 412 | `Params`           | Parametertyp des Hooks                             |     |
| 413 | `gridSize`         | Artikel je Achse in einer Ebene ↔                 |     |
| 414 | `layers`           | Anzahl Ebenen ↔                                   |     |
| 415 | `spacingX`         | Mitte-zu-Mitte-Abstand in x ↔                     |     |
| 416 | `spacingY`         | Mitte-zu-Mitte-Abstand in z (Name irreführend) ↔ |     |
| 417 | `layerGap`         | Mitte-zu-Mitte-Abstand der Ebenen (y) ↔           |     |
| 418 | `pos`              | Erzeugte Positionsliste                            |     |

## `frontend/components/ui/button.tsx`


| #   | Alt                                          | Bedeutung                         | NEU |
| --- | -------------------------------------------- | --------------------------------- | --- |
| 419 | `Variant`                                    | Bootstrap-Farbvariante            |     |
| 420 | `Size`                                       | Bootstrap-Größe                 |     |
| 421 | `Props`                                      | Props des Buttons                 |     |
| 422 | `variant` / `size` / `outline` / `className` | Einzelne Button-Props ↔          |     |
| 423 | `classes`                                    | Zusammengesetzte CSS-Klassenliste |     |

## `frontend/components/ui/navBar.tsx`, `app/layout.tsx`, `app/page.tsx`


| #   | Alt          | Bedeutung                     | NEU |
| --- | ------------ | ----------------------------- | --- |
| 424 | `SiteNavbar` | Navigationsleiste             |     |
| 425 | `RootLayout` | 🔒 Next.js Root-Layout        |     |
| 426 | `children`   | 🔒 Eingebettete Seiteninhalte |     |
| 427 | `Home`       | Startseite                    |     |

## `frontend/app/formular/page.tsx`


| #   | Alt                        | Bedeutung                                  | NEU |
| --- | -------------------------- | ------------------------------------------ | --- |
| 428 | `ItemObject`               | Artikelmaße aus dem Upload 🔗             |     |
| 429 | `UploadResult`             | Antwort des Upload-Endpunkts 🔗            |     |
| 430 | `errorBadgeStyle`          | Inline-Style der roten Fehlermeldung       |     |
| 431 | `FormPage`                 | Formularseite                              |     |
| 432 | `router`                   | Next.js-Router ↔                          |     |
| 433 | `formData` / `setFormData` | Zustand aller Formularfelder               |     |
| 434 | `itemQuantity`             | Artikelmenge je VPE (Eingabe) 🔗 ↔        |     |
| 435 | `bulkGoods`                | Schüttgut-Schalter 🔗 ↔                  |     |
| 436 | `scalable`                 | Schalter „andere Polzahl / andere Länge" |     |
| 437 | `formData.stability`       | Gewählte Stabilitätsklasse 🔗 ↔         |     |
| 438 | `formData.scaled_length`   | Eingegebene Ziel-Artikellänge 🔗 ↔       |     |
| 439 | `fillResidual`             | Resträume auffüllen ja/nein 🔗 ↔        |     |
| 440 | `errors` / `setErrors`     | Validierungsfehler je Feld                 |     |
| 441 | `cadFileUploaded`          | Wurde eine gültige CAD-Datei hochgeladen? |     |
| 442 | `uploadedItem`             | Vom Backend gemeldete Artikelmaße         |     |
| 443 | `uploadedStlFile`          | Serverpfad der erzeugten STL               |     |
| 444 | `isSimulating`             | Läuft gerade eine Simulation?             |     |
| 445 | `simulationError`          | Fehlermeldung der Simulation               |     |
| 446 | `handleFileChange`         | Handler für die Dateiauswahl              |     |
| 447 | `handleFileChange.file`    | Ausgewählte Datei                         |     |
| 448 | `fileName`                 | Dateiname in Kleinschreibung               |     |
| 449 | `isValidFile`              | Endet der Name auf`.stp`/`.stl`?           |     |
| 450 | `uploadResult`             | Antwort des Upload-Endpunkts               |     |
| 451 | `runSimulation`            | Startet den Schüttgut-Pfad                |     |
| 452 | `hasScaling`               | Ist eine Längenskalierung aktiv?          |     |
| 453 | `scaleFactor`              | Ziel-Länge / Ist-Länge ↔                |     |
| 454 | `runSimulation.item`       | Artikelmaße nach Skalierung               |     |
| 455 | `payload`                  | Request-Body für`/simulation/run`         |     |
| 456 | `errorText`                | Rohtext einer Fehlerantwort                |     |
| 457 | `runSimulation.result`     | Simulationsergebnis                        |     |
| 458 | `validateForm`             | Prüft alle Formularfelder                 |     |
| 459 | `newErrors`                | Frisch erhobene Validierungsfehler         |     |
| 460 | `handleRender`             | Handler „Verpackung suchen"               |     |
| 461 | `isValid`                  | Ergebnis der Formularprüfung              |     |

### localStorage-Schlüssel 🔗


| #   | Alt                   | Bedeutung                                                | NEU |
| --- | --------------------- | -------------------------------------------------------- | --- |
| 462 | `"convertedStlUrl"`   | URL der konvertierten STL ↔                             |     |
| 463 | `"simulationRequest"` | Ursprünglicher Simulations-Request (für das Replay) ↔ |     |
| 464 | `"simulationResult"`  | Simulationsergebnis für die Ergebnisseite ↔            |     |
| 465 | `"itemQuantity"`      | Artikelmenge je VPE ↔                                   |     |
| 466 | `"bulkGoods"`         | Schüttgut-Schalter                                      |     |
| 467 | `"scaled_length"`     | Ziel-Artikellänge ↔                                    |     |
| 468 | `"stability"`         | Stabilitätsklasse ↔                                    |     |
| 469 | `"fillResidual"`      | Resträume auffüllen ↔                                 |     |
| 470 | `"packingResults"`    | Ergebnis der Packmustersuche ↔                          |     |

## `frontend/app/positioning/page.tsx`


| #   | Alt                                                 | Bedeutung                                    | NEU |
| --- | --------------------------------------------------- | -------------------------------------------- | --- |
| 471 | `GRID_SIZE`                                         | Artikel je Achse im Startraster (2)          |     |
| 472 | `LAYERS`                                            | Ebenen im Startraster (2)                    |     |
| 473 | `RenderingContent`                                  | Inhalt der Positionierungsseite              |     |
| 474 | `activeUrl`                                         | Tatsächlich geladene STL-URL                |     |
| 475 | `color`                                             | Artikelfarbe in der 3D-Ansicht ↔            |     |
| 476 | `castShadow`                                        | Artikel wirft Schatten ↔                    |     |
| 477 | `receiveShadow`                                     | Artikel empfängt Schatten ↔                |     |
| 478 | `positioning.spacingX`                              | Slider: Lücke zwischen Artikeln in x        |     |
| 479 | `positioning.spacingY`                              | Slider: Lücke zwischen Artikeln in z        |     |
| 480 | `positioning.layerGap`                              | Slider: Lücke zwischen den Ebenen           |     |
| 481 | `rotationMode`                                      | Auf welche Artikel wirkt die Rotation ↔     |     |
| 482 | `resetKey`                                          | Zähler, der die 3D-Szene neu aufbaut ↔     |     |
| 483 | `boundingBox`                                       | Artikelmaße aus der geladenen STL ↔        |     |
| 484 | `loadingPacking`                                    | Läuft die Verpackungssuche?                 |     |
| 485 | `packingError`                                      | Fehlermeldung der Verpackungssuche           |     |
| 486 | `artX` / `artY` / `artZ`                            | Artikelmaße je Achse (Fallback 50)          |     |
| 487 | `basePositions`                                     | Rasterpositionen ohne Nutzeränderung        |     |
| 488 | `scaledLength`                                      | Ziel-Artikellänge aus dem localStorage ↔   |     |
| 489 | `storedScaledLength`                                | Rohwert aus dem localStorage                 |     |
| 490 | `parsedScaledLength`                                | Als Zahl geparste Ziel-Länge                |     |
| 491 | `scenePositions`                                    | Aktuell dargestellte Artikelpositionen       |     |
| 492 | `hasNegativeSpacing`                                | Überlappen sich die Hüllgeometrien?        |     |
| 493 | `hasScaledLength`                                   | Ist eine Skalierung aktiv? (Warnhinweis)     |     |
| 494 | `rotationsZ` / `rotationsX` / `rotationsY`          | Rotationswinkel je Artikel und Achse ↔      |     |
| 495 | `getPatternPayload`                                 | Baut das Packmuster für den Request         |     |
| 496 | `sizeX` / `sizeY` / `sizeZ`                         | Artikelmaße im Musterelement                |     |
| 497 | `handleSearchPackaging`                             | Handler „Verpackung suchen"                 |     |
| 498 | `itemLength` / `itemWidth` / `itemHeight`           | Artikelmaße aus der Bounding-Box            |     |
| 499 | `handleSearchPackaging.scaled_length`               | Effektive Ziel-Länge (Fallback: Ist-Länge) |     |
| 500 | `handleSearchPackaging.pattern`                     | Zusammengebautes Packmuster                  |     |
| 501 | `handleSearchPackaging.data`                        | Antwort von`/packing/top20` ↔               |     |
| 502 | `edgeIndicesPerLayer`                               | Indizes der Randartikel je Ebene             |     |
| 503 | `edgeIndicesPerLayer.axis`                          | Achse, auf die sich „Rand" bezieht          |     |
| 504 | `pick`                                              | `"min"` oder `"max"` — welcher Rand         |     |
| 505 | `byLayer`                                           | Zuordnung Ebenenhöhe → Artikelindizes      |     |
| 506 | `edgeIndicesPerLayer.indices`                       | Gefundene Randindizes                        |     |
| 507 | `values`                                            | Achswerte aller Artikel einer Ebene          |     |
| 508 | `target`                                            | Kleinster bzw. größter Achswert            |     |
| 509 | `getTargetIndices`                                  | Indizes der zu drehenden Artikel             |     |
| 510 | `maxY`                                              | Höhe der obersten Ebene                     |     |
| 511 | `rotate`                                            | Dreht die Zielartikel um 90° weiter         |     |
| 512 | `rotate.setter`                                     | Setter des betroffenen Rotationszustands     |     |
| 513 | `next`                                              | Neuer Rotationszustand                       |     |
| 514 | `targets`                                           | Indizes der zu drehenden Artikel             |     |
| 515 | `handleRotateZ` / `handleRotateX` / `handleRotateY` | Handler der drei Drehknöpfe ↔              |     |
| 516 | `resetPosition`                                     | Setzt Abstände und Rotationen zurück ↔    |     |

## `frontend/components/rendering/ControlPanel.tsx`


| #   | Alt                                                          | Bedeutung                            | NEU    |
| --- | ------------------------------------------------------------ | ------------------------------------ | ------ |
| 517 | `SliderProps`                                                | Props eines Schiebereglers           |        |
| 518 | `Slider.label`                                               | Beschriftung des Reglers ↔          |        |
| 519 | `Slider.value`                                               | Aktueller Wert ↔                    |        |
| 520 | `onChange`                                                   | Änderungs-Callback ↔               |        |
| 521 | `Slider.min` / `.max` / `.step`                              | Grenzen und Schrittweite des Reglers |        |
| 522 | `RotationMode`                                               | Typ:`"right"                         | "back" |
| 523 | `ControlPanelProps`                                          | Props des Bedienfelds                |        |
| 524 | `onSpacingXChange` / `onSpacingYChange` / `onLayerGapChange` | Callbacks der drei Regler ↔         |        |
| 525 | `onRotationModeChange`                                       | Callback der Modus-Auswahl ↔        |        |
| 526 | `onRotateZ` / `onRotateX` / `onRotateY`                      | Callbacks der Drehknöpfe ↔         |        |
| 527 | `ControlPanel`                                               | Das Bedienfeld selbst ↔             |        |

## `frontend/components/rendering/Scene.tsx`


| #   | Alt                   | Bedeutung                                       | NEU |
| --- | --------------------- | ----------------------------------------------- | --- |
| 528 | `SceneProps`          | Props der 3D-Szene                              |     |
| 529 | `Scene.url`           | URL des Artikel-Meshes ↔                       |     |
| 530 | `Scene.positions`     | Artikelpositionen ↔                            |     |
| 531 | `onBoundingBoxChange` | Callback, wenn die Artikelmaße bekannt sind ↔ |     |
| 532 | `Scene`               | Die 3D-Szene ↔                                 |     |

## `frontend/components/rendering/STLModel.tsx`


| #   | Alt                                     | Bedeutung                             | NEU |
| --- | --------------------------------------- | ------------------------------------- | --- |
| 533 | `StlModelProps`                         | Props des Artikel-Meshes              |     |
| 534 | `StlModel`                              | Ein gerendertes Artikel-Mesh ↔       |     |
| 535 | `position`                              | Position des Artikels ↔              |     |
| 536 | `rotationZ` / `rotationX` / `rotationY` | Rotation je Achse ↔                  |     |
| 537 | `StlModel.scaled_length`                | Ziel-Länge zum Strecken in x ↔      |     |
| 538 | `showLocalAxes`                         | Lokales Achsenkreuz einblenden        |     |
| 539 | `axesSize`                              | Länge des Achsenkreuzes              |     |
| 540 | `geometry`                              | Geladene STL-Geometrie                |     |
| 541 | `StlModel.scaleFactor`                  | Streckfaktor in x                     |     |
| 542 | `mounted`                               | Ist die Komponente noch eingehängt?  |     |
| 543 | `geom`                                  | Frisch geladene Geometrie im Callback |     |
| 544 | `StlModel.size`                         | Maße der Bounding-Box                |     |
| 545 | `factor`                                | Berechneter Streckfaktor              |     |
| 546 | `err`                                   | Ladefehler der STL                    |     |

## `frontend/app/packing-results/page.tsx`


| #   | Alt                                  | Bedeutung                                     | NEU       |
| --- | ------------------------------------ | --------------------------------------------- | --------- |
| 547 | `ArticleMesh`                        | Ein Artikel in der Ergebnisvorschau           |           |
| 548 | `ArticleMesh.item`                   | Der darzustellende platzierte Artikel         |           |
| 549 | `modelUrl`                           | URL des Artikel-Meshes ↔                     |           |
| 550 | `ArticleMesh.scaledLength`           | Ziel-Länge des Artikels                      |           |
| 551 | `fallbackRotation`                   | Grundrotation aus dem`rotation_key`           |           |
| 552 | `baseEuler`                          | Grundrotation als Euler-Winkel                |           |
| 553 | `localEuler`                         | Zusatzrotation aus dem Packmuster             |           |
| 554 | `baseQuaternion` / `localQuaternion` | Beide Rotationen als Quaternion               |           |
| 555 | `finalQuaternion`                    | Verkettete Gesamtrotation                     |           |
| 556 | `finalEuler`                         | Gesamtrotation als Euler-Winkel               |           |
| 557 | `BoxPreview`                         | 3D-Vorschau einer Verpackung                  |           |
| 558 | `BoxPreview.result`                  | Darzustelltes Verpackungsergebnis             |           |
| 559 | `effectiveScaledLength`              | Wirksame Artikellänge (Fallback: Ist-Länge) |           |
| 560 | `SortMode` (packing)                 | Sortierung`"size"                             | "lhm"` ↔ |
| 561 | `PackingResultsPage`                 | Ergebnisseite der Packmustersuche ↔          |           |
| 562 | `data`                               | Geladene Ergebnisdaten ↔                     |           |
| 563 | `activeIndex`                        | Index des angezeigten Ergebnisses             |           |
| 564 | `sortMode`                           | Aktive Sortierung ↔                          |           |
| 565 | `raw`                                | Rohwert aus dem localStorage ↔               |           |
| 566 | `storedModelUrl`                     | Mesh-URL aus dem localStorage                 |           |
| 567 | `parsed`                             | Deserialisierte Ergebnisdaten ↔              |           |
| 568 | `results`                            | Sortierte Ergebnisliste ↔                    |           |
| 569 | `list`                               | Arbeitskopie beim Sortieren ↔                |           |
| 570 | `boxVolume`                          | Hilfsfunktion: Volumen einer Verpackung       |           |
| 571 | `current`                            | Gerade angezeigtes Ergebnis                   |           |
| 572 | `handleSortChange`                   | Handler der Sortierauswahl                    |           |
| 573 | `handlePrev` / `handleNext`          | Blättern durch die Ergebnisse                |           |

## `frontend/app/simulation-results/page.tsx`


| #   | Alt                               | Bedeutung                                                                                     | NEU            |
| --- | --------------------------------- | --------------------------------------------------------------------------------------------- | -------------- |
| 574 | `SimulationBox`                   | Verpackung im Simulationsergebnis 🔗                                                          |                |
| 575 | `SimulationResult`                | Ergebnis einer simulierten Verpackung 🔗                                                      |                |
| 576 | `SimulationResponse`              | Gesamte Antwort von`/simulation/run` 🔗                                                       |                |
| 577 | `SortMode` (simulation)           | Sortierung`"filling"                                                                          |                |
| 578 | `PackingResultsPage` (simulation) | Ergebnisseite der Simulation —**gleicher Name wie #561, obwohl es die Simulationsseite ist** | SimResultsPage |
| 579 | `rerunBoxName`                    | Name der Box, deren Replay gerade läuft                                                      |                |
| 580 | `handleRerun`                     | Startet die GUI-Wiederholung einer Box                                                        |                |
| 581 | `rawRequest`                      | Ursprünglicher Request aus dem localStorage                                                  |                |
| 582 | `simulationRequest`               | Deserialisierter Ursprungs-Request                                                            |                |
| 583 | `errorData`                       | Fehlerdetails aus der Backend-Antwort                                                         |                |

---

## Namen, die mir beim Lesen aufgefallen sind

Kein Zwang — nur Stellen, an denen der aktuelle Name etwas anderes sagt als der Code tut:


| #         | Name                                  | Warum auffällig                                                                                                     |
| --------- | ------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| 416 / 479 | `spacingY`                            | Steuert im 3D-Editor den Abstand entlang**z**, nicht y. Der Ebenenabstand heißt separat `layerGap`.                 |
| 578       | `PackingResultsPage`                  | Die Simulations-Ergebnisseite trägt denselben Komponentennamen wie die Packmuster-Ergebnisseite.                    |
| 64        | `_toleranz`                           | Einziger deutscher Bezeichner im sonst englischen Backend.                                                           |
| 208       | `pressing_gravity`                    | Docstring und Bachelorarbeit sprechen von „Verdichtungsgravitation" /`COMPACTION_GRAVITY`; der Code-Name weicht ab. |
| 335       | `box_utilization`                     | Wird als`fill_rate_percent` ausgeliefert — zwei Namen für dieselbe Größe.                                        |
| 329 / 338 | `settled_height` vs. `filling_height` | Vor bzw. nach dem Deckelandruck. Der Unterschied ist für Messungen entscheidend, aus den Namen aber nicht ablesbar. |
| 293–295  | `safety_wall_*`                       | Werden berechnet, aber nirgends im MJCF verwendet — toter Code.                                                     |
| 337       | `filling_height_m`                    | Nur im Abbruch-Dict enthalten, im Normalfall fehlt der Key.                                                          |
| 45 / 569  | `entry`, `list`                       | Sehr generisch;`list` verdeckt zusätzlich den JS-Typnamen.                                                          |

---

## Wenn du fertig bist

Sag Bescheid — ich benenne dann alle ausgefüllten Zeilen im ganzen Projekt um (Backend + Frontend gemeinsam, damit die 🔗-Namen auf beiden Seiten passen).
Zeilen mit 🔒 lasse ich unabhängig davon unangetastet und melde es dir, falls du dort etwas eingetragen hast.
