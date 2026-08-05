# Umbenennungs-Vorlage 2 — Funktionen, Klassen, Typen, Komponenten, Endpunkte, Dateien

Gleiches Prinzip wie [RENAME.md](RENAME.md): Spalte **NEU** ausfüllen, leer = bleibt.
Eigene Nummerierung mit `F`-Präfix, damit sich nichts mit der Variablenliste beißt.

## Legende


| Symbol   | Bedeutung                                                                                                                                       |
| -------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| 🔗       | **Schnittstelle.** Route-Pfad, Response-Modell oder exportierter Typ, der über die Grenze Backend ↔ Frontend geht. Umbenennen nur beidseitig. |
| 🔒       | **Fremdvorgabe.** Von FastAPI, Next.js, React oder Python vorgegeben — bitte nicht ändern.                                                    |
| ↔       | Name kommt in mehreren Dateien vor.                                                                                                             |
| **#nnn** | Steht**auch schon** in RENAME.md unter dieser Nummer. Bitte nur an *einer* Stelle ausfüllen — ich nehme dann den Eintrag, der gefüllt ist.   |

---

# BACKEND

## Klassen


| #   | Alt                          | Datei                      | Bedeutung                                               | NEU                |
| --- | ---------------------------- | -------------------------- | ------------------------------------------------------- | ------------------ |
| F1  | `Item`                       | `packing/models.py`        | Geometrie eines Artikels (L×B×H) ↔                   |                    |
| F2  | `Box`                        | `packing/models.py`        | Eine Verpackung aus dem Katalog ↔                      |                    |
| F3  | `PackingOptimizer`           | `packing/optimizer.py`     | Packmuster-Pfad: sucht Verpackungen per Rasterlogik ↔  |                    |
| F4  | `SimulationConfig`           | `simulation/common.py`     | Alle Parameter eines Simulationslaufs 🔗 ↔             |                    |
| F5  | `PackagingSimulation`        | `simulation/sim_mujoco.py` | Schüttgut-Pfad: baut und rechnet die MuJoCo-Szene ↔   |                    |
| F6  | `Vec3`                       | `api/routes/packing.py`    | 3D-Vektor im Request 🔗**#362**                         |                    |
| F7  | `PatternElementRequest`      | `api/routes/packing.py`    | Ein Element des Packmusters 🔗**#363**                  | GridElementRequest |
| F8  | `PatternRequest`             | `api/routes/packing.py`    | Das gesamte Packmuster 🔗**#364**                       | GridRequest        |
| F9  | `PackingRequest`             | `api/routes/packing.py`    | Request-Modell von`/packing/top20` 🔗 **#365**          |                    |
| F10 | `RequestedBox`               | `api/routes/simulation.py` | Vom Client fürs Replay gewählte Verpackung 🔗**#349** |                    |
| F11 | `SingleBoxSimulationRequest` | `api/routes/simulation.py` | Request-Modell des Replay-Endpunkts 🔗**#350**          |                    |

## Methoden von `Item` / `Box`


| #   | Alt                 | Bedeutung                                           | NEU |
| --- | ------------------- | --------------------------------------------------- | --- |
| F12 | `Item.orientations` | Liefert alle 6 Achsen-Permutationen des Artikels ↔ |     |
| F13 | `Box.volume`        | Innenvolumen in mm³ (Property) ↔**#19**           |     |

## Methoden von `PackingOptimizer`


| #   | Alt                        | Bedeutung                                                             | NEU                  |
| --- | -------------------------- | --------------------------------------------------------------------- | -------------------- |
| F14 | `_fill_remaining_space`    | Füllt einen Restraum neben dem Hauptraster maximal auf               |                      |
| F15 | `_unique_orientations`     | Orientierungen ohne doppelte Kantenlängen-Tripel                     |                      |
| F16 | `_normalized_elements`     | Packmuster ausgedreht und in den Ursprung verschoben                  |                      |
| F17 | `effective_article_volume` | Artikelvolumen für den Box-Vorfilter (Mesh vs. Rasterquader)         |                      |
| F18 | `_pattern_step`            | Kleinster Positionsabstand entlang einer Achse = Schrittweite         | _grid_step           |
| F19 | `_fits_overlap`            | Passt der Artikel an diesen Punkt ohne Box-Überschreitung/Kollision? |                      |
| F20 | `_build_pattern_lookup`    | Zuordnung Rasterzelle → Rotation + Musterindex                       | `_build_grid_lookup` |
| F21 | `_find_best_orientation`   | Orientierung mit der geringsten Überkapazität                       |                      |
| F22 | `_place_articles`          | Greedy Extreme-Point-Packing der Artikel                              |                      |
| F23 | `_build_result`            | Baut das Ergebnis-Dict einer Verpackung 🔗                            |                      |
| F24 | `_rotated_size`            | Achsparallele Maße nach 90°-Rotationen                              |                      |
| F25 | `_pack_pattern`            | Kompletter Packversuch für genau eine Verpackung                     | _pack_grid           |
| F26 | `find_top_boxes`           | Öffentlicher Einstieg: Ranking der passenden Verpackungen ↔         |                      |

## Funktionen `packing/box_loader.py`


| #   | Alt                           | Bedeutung                                                  | NEU |
| --- | ----------------------------- | ---------------------------------------------------------- | --- |
| F27 | `_matches_stability`          | Passt die CSV-Zeile zum Stabilitätsfilter?                |     |
| F28 | `_box_from_row`               | Baut aus einer CSV-Zeile eine`Box` inkl. LHM-Kapazität    |     |
| F29 | `_load_pattern_boxes`         | Vorfilter des Packmuster-Pfads (rein volumetrisch)         |     |
| F30 | `_clamp`                      | Begrenzt einen Wert auf ein Intervall                      |     |
| F31 | `_load_bulk_boxes`            | Vorfilter des Schüttgut-Pfads (Überlaufquote + Fallback) |     |
| F32 | `_unique_boxes_by_dimensions` | Entfernt maßgleiche Verpackungen                          |     |
| F33 | `load_boxes_from_csv`         | Öffentlicher Einstieg: gefiltertes Kandidatenfeld ↔      |     |

## Funktionen `packing/lhm.py`, `geometry.py`, `services/…/converter.py`


| #   | Alt                           | Bedeutung                                                         | NEU                   |
| --- | ----------------------------- | ----------------------------------------------------------------- | --------------------- |
| F34 | `get_lhm_capacity`            | Verpackungen je Ladehilfsmittel, geometrisch berechnet ↔         |                       |
| F35 | `resolve_converted_stl`       | Löst eine STL-URL zum Pfad im`converted`-Ordner auf ↔           |                       |
| F36 | `_vhacd_params_tag`           | Fingerprint der V-HACD-Parameter für den Cache                   |                       |
| F37 | `ensure_vhacd_collision_mesh` | Erzeugt/cacht die konvexe Zerlegung als npz ↔                    |                       |
| F38 | `compute_scaled_volume_mm3`   | Volumen der konvexen Hülle, optional auf Ziel-Länge normiert ↔ | compute_convex_volume |
| F39 | `step_to_stl_cq`              | Konvertiert STP → STL über CadQuery                             | convert_to_stl        |

## Funktionen `simulation/common.py`


| #   | Alt                                            | Bedeutung                                              | NEU                        |
| --- | ---------------------------------------------- | ------------------------------------------------------ | -------------------------- |
| F40 | `_get_best_valid_results`                      | Filtert und sortiert die Ergebnisse nach Füllgrad ↔  |                            |
| F41 | `_get_single_article_volume_m3`                | Volumen eines Artikels in m³                          | _get_single_article_volume |
| F42 | `_build_dynamic_reference_boxes`               | Erzeugt die drei Referenzboxen der Dichteschätzung ↔ |                            |
| F43 | `SimulationConfig.box_x` / `.box_y` / `.box_z` | Innenmaße der ersten Box in m (Properties)**#193**    |                            |

## Funktionen `simulation/sim_mujoco.py` (Modulebene)


| #   | Alt                             | Bedeutung                                                                                                | NEU |
| --- | ------------------------------- | -------------------------------------------------------------------------------------------------------- | --- |
| F44 | `_box_seed_offset`              | Seed-Versatz aus den Boxmaßen (CRC32)                                                                   |     |
| F45 | `run_single_box_simulation`     | **Worker:** simuliert eine Verpackung <br />über alle Läufe und mittelt ↔ ⚠️ *Namensgleich mit F60* |     |
| F46 | `_reference_box_density`        | Packdichte einer Referenzbox inkl. Nachvergrößerung                                                    |     |
| F47 | `estimate_bulk_packing_density` | Geschätzte Schüttdichte aus den drei Referenzboxen ↔                                                  |     |
| F48 | `_euler_to_quaternion_wxyz`     | XYZ-Euler → Quaternion in MuJoCo-Reihenfolge                                                            |     |
| F49 | `_parse_obj_groups`             | Zerlegt eine V-HACD-OBJ in ihre Teilkörper                                                              |     |

## Methoden von `PackagingSimulation`


| #   | Alt                          | Bedeutung                                                     | NEU              |
| --- | ---------------------------- | ------------------------------------------------------------- | ---------------- |
| F50 | `__init__`                   | 🔒 Python-Konstruktor                                         |                  |
| F51 | `run`                        | Öffentlicher Einstieg: alle Boxen (ggf. parallel) ↔         |                  |
| F52 | `_run_single`                | Ein kompletter Lauf: Modell bauen, simulieren, auswerten ↔   |                  |
| F53 | `_build_model`               | Kompiliert das MJCF und legt die MuJoCo-Daten an              |                  |
| F54 | `_count_escaped_articles`    | Zählt Artikel, die die Box seitlich/unten verlassen haben    |                  |
| F55 | `_plan_spawn_positions`      | Würfelt Startpositionen und -rotationen aus                  |                  |
| F56 | `_spawn_grid`                | Rasterauslegung fürs Spawnen (Spalten + nutzbare Fläche) ↔ |                  |
| F57 | `_get_spawn_wall_height`     | Nötige Wandhöhe, damit nichts über die Wand spawnt         | _get_wall_height |
| F58 | `_collision_part_vertices`   | Lädt die Vertices der Kollisionsteile aus der npz            |                  |
| F59 | `_build_scene_xml`           | Baut die komplette MJCF-Szene als XML-String                  | `_build_scene    |
| F60 | `_collect_article_handles`   | Sammelt Body-/Geom-IDs und Vertices nach dem Kompilieren      |                  |
| F61 | `_step`                      | Ein Zeitschritt inkl. Viewer-Sync und Echtzeitbremse ↔       |                  |
| F62 | `_simulate`                  | Ablauf: fallen → verdichten → abstreifen → Deckel absetzen |                  |
| F63 | `_current_max_z`             | Oberkante der Schüttung über alle Kollisionsvertices ↔     |                  |
| F64 | `_step_until_settled`        | Läuft bis zur Ruhelage (`max                                 | qvel             |
| F65 | `_settle_items_with_impulse` | Rüttelphase: umlaufende Horizontalkraft auf alle Artikel ↔  |                  |
| F66 | `_evaluate`                  | Berechnet Füllhöhe, Dichte, Füllgrad, Passt-Urteil         |                  |
| F67 | `_print_results`             | Konsolenausgabe der Kennzahlen                                |                  |
| F68 | `_hold_gui_open`             | Hält das Viewer-Fenster nach dem Lauf offen                  |                  |
| F69 | `_close_viewer`              | Schließt den Viewer im`finally`-Zweig                        |                  |

## API-Endpunkte (Handler-Funktionen)


| #   | Alt                          | Datei                  | Bedeutung                                                                         | NEU                          |
| --- | ---------------------------- | ---------------------- | --------------------------------------------------------------------------------- | ---------------------------- |
| F70 | `convert_stp_to_stl`         | `routes/uploads.py`    | Handler`POST /convert-stp-to-stl`                                                 |                              |
| F71 | `upload_stl`                 | `routes/uploads.py`    | Handler`POST /upload-stl`                                                         |                              |
| F72 | `get_item_from_stl`          | `routes/uploads.py`    | Liest die Bounding-Box-Maße aus einer STL ↔                                     |                              |
| F73 | `get_top_20_packing_results` | `routes/packing.py`    | Handler`POST /packing/top20` — ⚠️ liefert tatsächlich **50** Ergebnisse       | `get_top_50_packing_results` |
| F74 | `run_simulation`             | `routes/simulation.py` | Handler`POST /simulation/run` (Hauptpfad Schüttgut)                              |                              |
| F75 | `run_single_box_simulation`  | `routes/simulation.py` | Handler`POST /simulation/run-single-box` (GUI-Replay) ⚠️ *Namensgleich mit F45* |                              |

## API-Routen-Pfade 🔗

Umbenennen erfordert immer die passende `fetch`-Stelle im Frontend.


| #   | Alt                               | Frontend-Aufrufer                                                         | NEU |
| --- | --------------------------------- | ------------------------------------------------------------------------- | --- |
| F76 | `POST /convert-stp-to-stl`        | `lib/api/uploads.ts` → `uploadStepFile`                                  |     |
| F77 | `POST /upload-stl`                | `lib/api/uploads.ts` → `uploadStlFile`                                   |     |
| F78 | `POST /packing/top20`             | `app/positioning/page.tsx` → `handleSearchPackaging`                     |     |
| F79 | `POST /simulation/run`            | `app/formular/page.tsx` → `runSimulation`                                |     |
| F80 | `POST /simulation/run-single-box` | `app/simulation-results/page.tsx` → `handleRerun`                        |     |
| F81 | `GET /files/<name>`               | Statischer Mount der STL-Dateien; steckt in jeder gespeicherten`file_url` |     |
| F82 | Router-Prefix`"/simulation"`      | Gemeinsames Präfix von F79/F80                                           |     |
| F83 | Router-Tag`"simulation"`          | Gruppenname in der OpenAPI-Doku                                           |     |

---

# FRONTEND

## Typen und Interfaces


| #    | Alt                  | Datei                         | Bedeutung                                                             | NEU |
| ---- | -------------------- | ----------------------------- | --------------------------------------------------------------------- | --- |
| F84  | `RotationKey`        | `lib/packing.ts`              | Die sechs Achsen-Permutationen 🔗**#396**                             |     |
| F85  | `PositionItem`       | `lib/packing.ts`              | Ein platzierter Artikel im Ergebnis 🔗**#397**                        |     |
| F86  | `PackingResult`      | `lib/packing.ts`              | Ergebnis für eine Verpackung 🔗**#398**                              |     |
| F87  | `PackingResponse`    | `lib/packing.ts`              | Antwort von`/packing/top20` 🔗 **#399**                               |     |
| F88  | `Params`             | `hooks/useGridPositions.ts`   | Parametertyp des Raster-Hooks**#412**                                 |     |
| F89  | `Variant`            | `ui/button.tsx`               | Bootstrap-Farbvariante**#419**                                        |     |
| F90  | `Size`               | `ui/button.tsx`               | Bootstrap-Größe**#420**                                             |     |
| F91  | `Props`              | `ui/button.tsx`               | Props des Buttons — sehr generisch**#421**                           |     |
| F92  | `ItemObject`         | `formular/page.tsx`           | Artikelmaße aus dem Upload 🔗**#428**                                |     |
| F93  | `UploadResult`       | `formular/page.tsx`           | Antwort des Upload-Endpunkts 🔗**#429**                               |     |
| F94  | `SliderProps`        | `ControlPanel.tsx`            | Props eines Schiebereglers**#517**                                    |     |
| F95  | `RotationMode`       | `ControlPanel.tsx`            | `"right" | "back" | "top" | "all"` ↔ **#522**                        |     |
| F96  | `ControlPanelProps`  | `ControlPanel.tsx`            | Props des Bedienfelds**#523**                                         |     |
| F97  | `SceneProps`         | `Scene.tsx`                   | Props der 3D-Szene**#528**                                            |     |
| F98  | `StlModelProps`      | `STLModel.tsx`                | Props des Artikel-Meshes**#533**                                      |     |
| F99  | `SortMode`           | `packing-results/page.tsx`    | `"size" | "lhm"` **#560** ⚠️ *Namensgleich mit F100*                |     |
| F100 | `SortMode`           | `simulation-results/page.tsx` | `"filling" | "lhm" | "fillrate"` **#577** ⚠️ *Namensgleich mit F99* |     |
| F101 | `SimulationBox`      | `simulation-results/page.tsx` | Verpackung im Simulationsergebnis 🔗**#574**                          |     |
| F102 | `SimulationResult`   | `simulation-results/page.tsx` | Ergebnis einer simulierten Verpackung 🔗**#575**                      |     |
| F103 | `SimulationResponse` | `simulation-results/page.tsx` | Antwort von`/simulation/run` 🔗 **#576**                              |     |

## React-Komponenten


| #    | Alt                  | Datei                         | Bedeutung                                                     | NEU |
| ---- | -------------------- | ----------------------------- | ------------------------------------------------------------- | --- |
| F104 | `Button`             | `ui/button.tsx`               | Bootstrap-Button, Default-Export ↔                           |     |
| F105 | `SiteNavbar`         | `ui/navBar.tsx`               | Navigationsleiste**#424**                                     |     |
| F106 | `RootLayout`         | `app/layout.tsx`              | 🔒 Next.js Root-Layout**#425**                                |     |
| F107 | `Home`               | `app/page.tsx`                | Startseite**#427**                                            |     |
| F108 | `FormPage`           | `formular/page.tsx`           | Eingabeformular (Seite 1)**#431**                             |     |
| F109 | `RenderingContent`   | `positioning/page.tsx`        | Inhalt der Positionierungsseite**#473**                       |     |
| F110 | `Page`               | `positioning/page.tsx`        | 🔒 Next.js Default-Export, umschließt F109 mit`<Suspense>`   |     |
| F111 | `Slider`             | `ControlPanel.tsx`            | Ein Schieberegler mit +/−-Knöpfen                           |     |
| F112 | `ControlPanel`       | `ControlPanel.tsx`            | Bedienfeld der Positionierung ↔**#527**                      |     |
| F113 | `Scene`              | `Scene.tsx`                   | 3D-Szene der Positionierung ↔**#532**                        |     |
| F114 | `StlModel`           | `STLModel.tsx`                | Ein gerendertes Artikel-Mesh ↔**#534**                       |     |
| F115 | `ArticleMesh`        | `packing-results/page.tsx`    | Ein Artikel in der Ergebnisvorschau**#547**                   |     |
| F116 | `BoxPreview`         | `packing-results/page.tsx`    | 3D-Vorschau einer Verpackung**#557**                          |     |
| F117 | `PackingResultsPage` | `packing-results/page.tsx`    | Ergebnisseite Packmuster**#561** ⚠️ *Namensgleich mit F118* |     |
| F118 | `PackingResultsPage` | `simulation-results/page.tsx` | Ergebnisseite**Simulation** — Name passt nicht **#578** ⚠️ |     |

## Hooks


| #    | Alt                | Datei                                   | Bedeutung                                      | NEU |
| ---- | ------------------ | --------------------------------------- | ---------------------------------------------- | --- |
| F119 | `useFileUrl`       | `positioning/hooks/useFileUrl.ts`       | Liest die STL-URL aus dem localStorage**#408** |     |
| F120 | `useGridPositions` | `positioning/hooks/useGridPositions.ts` | Erzeugt das 2×2×2-Startraster ↔**#411**     |     |

## Sonstige Funktionen


| #    | Alt                                                 | Datei                         | Bedeutung                                                                                                 | NEU |
| ---- | --------------------------------------------------- | ----------------------------- | --------------------------------------------------------------------------------------------------------- | --- |
| F121 | `apiUrl`                                            | `lib/api/clients.ts`          | Baut absolute Backend-URLs ↔**#388**                                                                     |     |
| F122 | `uploadStlFile`                                     | `lib/api/uploads.ts`          | Lädt eine STL hoch**#392**                                                                               |     |
| F123 | `uploadStepFile`                                    | `lib/api/uploads.ts`          | Lädt eine STP hoch und lässt konvertieren**#393**                                                       |     |
| F124 | `getRotationFromKey`                                | `lib/packing.ts`              | `rotation_key` → Rotation in Grad ↔ **#400**                                                            |     |
| F125 | `getNumberParam`                                    | `positioning/utils/params.ts` | Liest einen Zahlenwert aus der Query**#402**                                                              |     |
| F126 | `handleFileChange`                                  | `formular/page.tsx`           | Handler der Dateiauswahl**#446**                                                                          |     |
| F127 | `runSimulation`                                     | `formular/page.tsx`           | Startet den Schüttgut-Pfad**#451**                                                                       |     |
| F128 | `validateForm`                                      | `formular/page.tsx`           | Prüft alle Formularfelder**#458**                                                                        |     |
| F129 | `handleRender`                                      | `formular/page.tsx`           | Handler „Verpackung suchen" — <br />führt je nach Schalter zu Simulation*oder* Positionierung **#460** |     |
| F130 | `getPatternPayload`                                 | `positioning/page.tsx`        | Baut das Packmuster für den Request**#495**                                                              |     |
| F131 | `handleSearchPackaging`                             | `positioning/page.tsx`        | Handler „Verpackung suchen"**#497**                                                                      |     |
| F132 | `edgeIndicesPerLayer`                               | `positioning/page.tsx`        | Indizes der Randartikel je Ebene**#502**                                                                  |     |
| F133 | `getTargetIndices`                                  | `positioning/page.tsx`        | Welche Artikel die Rotation trifft**#509**                                                                |     |
| F134 | `rotate`                                            | `positioning/page.tsx`        | Dreht die Zielartikel um 90° weiter**#511**                                                              |     |
| F135 | `handleRotateZ` / `handleRotateX` / `handleRotateY` | `positioning/page.tsx`        | Handler der drei Drehknöpfe**#515**                                                                      |     |
| F136 | `resetPosition`                                     | `positioning/page.tsx`        | Setzt Abstände und Rotationen zurück ↔**#516**                                                         |     |
| F137 | `boxVolume`                                         | `packing-results/page.tsx`    | Hilfsfunktion: Volumen einer Verpackung**#570**                                                           |     |
| F138 | `handleSortChange`                                  | `packing-results/page.tsx`    | Handler der Sortierauswahl**#572**                                                                        |     |
| F139 | `handlePrev` / `handleNext`                         | `packing-results/page.tsx`    | Blättern durch die Ergebnisse**#573**                                                                    |     |
| F140 | `handleRerun`                                       | `simulation-results/page.tsx` | Startet die GUI-Wiederholung einer Box**#580**                                                            |     |

---

# DATEIEN, MODULE UND ORDNER

Umbenennen zieht immer die `import`-Zeilen mit; bei Next.js-Seitenordnern ändert sich zusätzlich die **URL**.

## Backend


| #    | Alt                                         | Bedeutung                                                                 | NEU                                                     |
| ---- | ------------------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------- |
| F141 | `app/`                                      | Python-Paketwurzel — 🔒 steckt im Startbefehl`uvicorn app.api.main:app`  |                                                         |
| F142 | `app/core/config.py`                        | Pfad- und CORS-Konfiguration                                              |                                                         |
| F143 | `app/geometry.py`                           | V-HACD-Zerlegung und Volumenberechnung                                    |                                                         |
| F144 | `app/packing/`                              | Paket des Packmuster-Pfads                                                |                                                         |
| F145 | `app/packing/models.py`                     | `Item` und `Box`                                                          |                                                         |
| F146 | `app/packing/optimizer.py`                  | Rasterlogik des Packmuster-Pfads                                          |                                                         |
| F147 | `app/packing/box_loader.py`                 | CSV-Einlesen und Vorfilterung                                             |                                                         |
| F148 | `app/packing/lhm.py`                        | Ladehilfsmittel-Kapazität                                                |                                                         |
| F149 | `app/simulation/`                           | Paket des Schüttgut-Pfads                                                |                                                         |
| F150 | `app/simulation/common.py`                  | Engine-unabhängige Bausteine                                             |                                                         |
| F151 | `app/simulation/sim_mujoco.py`              | MuJoCo-Engine — der Suffix`_mujoco` stammt aus der Zeit mit zwei Engines |                                                         |
| F152 | `app/services/converterStpStl/`             | ⚠️ camelCase-Ordner im sonst snake_case-Backend                         |                                                         |
| F153 | `app/services/converterStpStl/converter.py` | STP→STL über CadQuery                                                   |                                                         |
| F154 | `app/api/main.py`                           | FastAPI-App und Router-Einbindung                                         |                                                         |
| F155 | `app/api/routes/uploads.py`                 | Upload-Endpunkte                                                          |                                                         |
| F156 | `app/api/routes/packing.py`                 | Packmuster-Endpunkt                                                       |                                                         |
| F157 | `app/api/routes/simulation.py`              | Simulations-Endpunkte                                                     |                                                         |
| F158 | `data/meine_datei.csv`                      | ⚠️ Verpackungskatalog mit Platzhalternamen                              | Verpackungskatalog.csv<br />Auch die csv umbenenn<br /> |

## Frontend


| #    | Alt                                     | Bedeutung / URL                                                    | NEU |
| ---- | --------------------------------------- | ------------------------------------------------------------------ | --- |
| F159 | `app/formular/`                         | Seite 1, URL`/formular` — ⚠️ einziger deutscher Routenname      |     |
| F160 | `app/positioning/`                      | 3D-Positionierung, URL`/positioning`                               |     |
| F161 | `app/packing-results/`                  | Ergebnisse Packmuster, URL`/packing-results`                       |     |
| F162 | `app/simulation-results/`               | Ergebnisse Simulation, URL`/simulation-results`                    |     |
| F163 | `components/rendering/`                 | 3D-Komponenten                                                     |     |
| F164 | `components/rendering/Scene.tsx`        | 3D-Szene                                                           |     |
| F165 | `components/rendering/STLModel.tsx`     | Artikel-Mesh — ⚠️ Datei`STLModel`, Komponente `StlModel`        |     |
| F166 | `components/rendering/ControlPanel.tsx` | Bedienfeld                                                         |     |
| F167 | `components/ui/button.tsx`              | Button — ⚠️ Kleinschreibung                                     |     |
| F168 | `components/ui/navBar.tsx`              | Navigationsleiste — ⚠️ camelCase, Komponente heißt`SiteNavbar` |     |
| F169 | `lib/packing.ts`                        | Gemeinsamer Ergebnisvertrag                                        |     |
| F170 | `lib/api/clients.ts`                    | Basis-URL-Helfer — ⚠️ Plural ohne Grund                         |     |
| F171 | `lib/api/uploads.ts`                    | Upload-Aufrufe                                                     |     |
| F172 | `app/positioning/utils/params.ts`       | Query-Parameter-Helfer                                             |     |

---

## Namen, die mir beim Lesen aufgefallen sind

Kein Zwang — nur Stellen, an denen der Name etwas anderes sagt als der Code tut:


| #                     | Name                                                                                                 | Warum auffällig                                                                                                                                                                                                                   |
| --------------------- | ---------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| F45 / F75             | `run_single_box_simulation`                                                                          | Existiert**zweimal**: als Worker in `sim_mujoco.py` und als Route-Handler in `routes/simulation.py`. Der Handler ruft am Ende `PackagingSimulation.run()` auf, nicht den gleichnamigen Worker — beim Lesen leicht zu verwechseln. |
| F73                   | `get_top_20_packing_results`                                                                         | Route heißt`/packing/top20`, die Funktion ruft aber `find_top_boxes(limit=50)` — es sind 50 Ergebnisse, nicht 20.                                                                                                                |
| F117 / F118           | `PackingResultsPage`                                                                                 | Beide Ergebnisseiten heißen gleich; die Simulationsseite trägt den Packmuster-Namen.                                                                                                                                             |
| F99 / F100            | `SortMode`                                                                                           | Zwei verschiedene Typen mit gleichem Namen und unterschiedlichen Werten.                                                                                                                                                           |
| F151                  | `sim_mujoco.py`                                                                                      | Der Engine-Suffix hatte nur Sinn, solange`sim.py` (PyBullet) daneben lag. Es gibt nur noch eine Engine.                                                                                                                            |
| F91                   | `Props`                                                                                              | Generischster mögliche Typname; in jeder Datei mit Props-Typ ein Kandidat für Verwechslung.                                                                                                                                      |
| F165                  | `STLModel.tsx` → `StlModel`                                                                         | Dateiname und Komponentenname schreiben das Akronym unterschiedlich.                                                                                                                                                               |
| F158                  | `meine_datei.csv`                                                                                    | Der Verpackungskatalog trägt einen Platzhalternamen — in einer Bachelorarbeit vermutlich nicht gewollt.                                                                                                                          |
| F159                  | `app/formular/`                                                                                      | Einzige deutsche Route zwischen`positioning`, `packing-results`, `simulation-results`.                                                                                                                                             |
| F17 / F26 / F33 / F47 | `effective_article_volume`, `find_top_boxes`, `load_boxes_from_csv`, `estimate_bulk_packing_density` | Die vier öffentlichen Einstiegspunkte der beiden Fachpfade — hier lohnt eine einheitliche Verb-Konvention am meisten.                                                                                                            |

---

## Wenn du fertig bist

Sag Bescheid, sobald **beide** Dateien ausgefüllt sind — ich benenne dann alles in einem Durchgang um (Backend + Frontend gemeinsam, damit die 🔗-Namen auf beiden Seiten passen) und lasse 🔒-Zeilen unangetastet.
