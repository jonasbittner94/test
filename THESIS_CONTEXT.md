# Kontext für Bachelorarbeit – Anwendung zur Verpackungsauswahl

> Dieses Dokument fasst **den kompletten technischen Stand** der Anwendung zusammen, die in dieser Bachelorarbeit entwickelt wird. Ein Chat, der beim Schreiben der Arbeit hilft, hat mit diesem Dokument alle relevanten Informationen über den Code, ohne den Code selbst lesen zu müssen. Stand: Juli 2026.

---

## 1. Thema, Kontext und Ziel

**Unternehmen:** Phoenix Contact. **Produkt:** Leiterplattenklemmen (elektrische Anschlussklemmen), gefertigt in hoher Stückzahl.

**Problem:** Die Auswahl der passenden Verpackung (Pappfaltschachtel aus einem festen Katalog) erfolgt aktuell manuell und erfahrungsbasiert. Das führt zu Inkonsistenz, schlechter Materialausnutzung (im Zweifel wird zu groß gewählt), Wissensverlust und hohem Einarbeitungsaufwand.

**Ziel der Arbeit:** Konzeption, Entwicklung und Evaluation einer **prototypischen Webanwendung**, die für eine gegebene Artikelmenge geeignete Verpackungen aus dem Katalog ermittelt und als **bewertete Rangliste** ausgibt. Die Entscheidung bleibt beim Nutzer; die Anwendung liefert die Kennzahlen. Es wird **kein** mathematisch optimales neues Verfahren beansprucht, sondern eine praxisorientierte Unterstützung.

**Zwei Verpackungsarten, zwei Verfahren:**
- **Packmusterartikel** – werden geordnet in einem reproduzierbaren Muster gepackt → **deterministischer Greedy-Algorithmus** (Extreme-Point-Verfahren).
- **Schüttgut** – wird ungeordnet eingefüllt → **physikbasierte Starrkörpersimulation** (PyBullet).

**Zwei Packungsstufen (Hierarchie):**
1. n gleiche Artikel → eine **Verpackung** (VPE, Verpackungseinheit).
2. Mehrere Verpackungen → ein **Ladehilfsmittel** (LHM), genormter Träger (hier 600 × 400 × 220 mm).

**Fachbegriffe:**
- **VPE** = Verpackungseinheit = kleinste verkaufte Menge gleichartiger Artikel + ihre Verpackung.
- **LHM** = Ladehilfsmittel = genormter Träger für mehrere VPE (Lagerung/Transport).

---

## 2. Technologie-Stack und Architektur

**Client-Server-Architektur.** Grund: Beide Berechnungsverfahren nutzen Python-Bibliotheken, die nicht im Browser laufen; außerdem ist die Rechenzeit nicht vernachlässigbar (Serverausführung sinnvoll).

| Schicht | Technologie |
|---|---|
| Frontend | Next.js (React, TypeScript), Three.js / react-three-fiber (3D), react-bootstrap |
| Backend | FastAPI (Python), Pydantic (Validierung), dataclasses |
| Geometrie | `trimesh` (Laden, Volumen, konvexe Hülle), CadQuery (STP→STL-Konvertierung) |
| Physik | PyBullet (Bullet Physics Engine) |
| Konvexe Zerlegung | V-HACD (in PyBullet integriert, `p.vhacd`) |
| Parallelisierung | `concurrent.futures.ProcessPoolExecutor` (eine Box pro Prozess/Kern) |
| Datenhaltung | CSV-Katalog der Verpackungen; hochgeladene/konvertierte STL im Dateisystem |

**Kommunikation:** REST über HTTP. Backend auf `http://localhost:8000`, Frontend auf `http://localhost:3000` (CORS entsprechend freigegeben). Zwischen den Seiten wird State über `localStorage` übergeben (kein globales State-Management).

---

## 3. Repository-Struktur (Backend)

```
backend/app/
├── api/
│   ├── main.py                  # FastAPI-App, CORS, Router-Registrierung
│   └── routes/
│       ├── uploads.py           # STP→STL-Konvertierung, STL-Upload; liefert file_url + item-Maße
│       ├── packing.py           # POST /packing/top20  (Packmuster-Flow)
│       └── simulation.py        # POST /simulation/run und /simulation/run-single-box (Schüttgut)
├── packing/
│   ├── models.py                # Dataclasses Item, Box
│   ├── box_loader.py            # CSV einlesen + Vorfilterung der Boxen
│   ├── optimizer.py             # PackingOptimizer (Extreme-Point-Greedy)
│   └── lhm.py                   # get_lhm_capacity: wie viele Boxen auf ein LHM passen
├── simulation/
│   └── sim.py                   # SimulationConfig + PackagingSimulation (PyBullet)
├── geometry.py                  # STL→Volumen, konvexe Hülle, V-HACD-Zerlegung, URL→Pfad
├── core/config.py               # Pfade (DATA_DIR, STORAGE_DIR, CONVERTED_DIR, BOXES_CSV)
└── services/converterStpStl/    # CadQuery-Konvertierung STP→STL
```

**Frontend (Next.js, `frontend/app/`):**
- `formular/page.tsx` – Eingabemaske: CAD-Upload, Menge, Gewicht, Schüttgut-Checkbox, Skalierung. Bei Schüttgut → ruft `/simulation/run`, speichert `simulationRequest` + `simulationResult` in localStorage, leitet zu `/simulation-results`. Sonst → weiter zu `/rendering`.
- `rendering/page.tsx` – 3D-Ansicht (Three.js): Nutzer ordnet Artikel interaktiv an (Abstände, Rotationen, bewusste Überlappung = Verschachtelung), ruft `/packing/top20`, leitet zu `/packing-results`.
- `components/rendering/STLModel.tsx` – lädt STL, rendert Artikel, berechnet dabei **im Frontend** das Volumen der konvexen Hülle über die Summe vorzeichenbehafteter Tetraedervolumina (`signedVolumeOfTriangle`).
- `packing-results/page.tsx` – Rangliste der Packmuster-Ergebnisse + 3D-Visualisierung; Sortier-Dropdown (Verpackungsgröße / LHM-Kapazität).
- `simulation-results/page.tsx` – Rangliste der Schüttgut-Ergebnisse; Sortier-Dropdown (relative Füllhöhe / Artikel pro LHM / Packdichte); pro Box ein **„Simulation erneut starten"-Button**, der über `/simulation/run-single-box` eine GUI-Simulation im Backend öffnet.

---

## 4. Datenmodelle

**`Item`** (`packing/models.py`) – der Artikel:
```python
@dataclass
class Item:
    length: float
    width: float
    height: float
    # .volume = length*width*height (Bounding-Box)
    # .orientations() = die 6 achsparallelen Drehungen mit rotation_key ("xyz", "xzy", ...)
```
> Hinweis: `Item` hat **kein** Gewichtsfeld (mehr). Gewicht wird aktuell nicht durchgängig genutzt.

**`Box`** (`packing/models.py`) – eine Verpackung aus dem Katalog:
```python
@dataclass
class Box:
    name: str
    length: float
    width: float
    height: float      # INNENMASSE in mm
    lhm_capacity: float # wie viele dieser Box auf ein LHM passen (aus CSV oder berechnet)
    # .volume = length*width*height
```

**Verpackungskatalog** (`data/meine_datei.csv`), Spalten:
`Object Name, length, height, width, materialNumber, Amount per bin box (LHM C), Stabilität`
- Maße in mm (Innenmaße). Zuordnung erfolgt per Spaltenname (die CSV-Reihenfolge ist length/height/width!).
- `Amount per bin box (LHM C)` → `lhm_capacity` (kann leer sein → 0).
- `Stabilität` → Materialgüte/Festigkeit; im Filter optional berücksichtigt.

---

## 5. Geometrie-Pipeline (`geometry.py`)

1. **STP → STL:** Upload-Endpoint konvertiert per CadQuery, speichert unter `storage/converted/<uuid>.stl`, gibt `file_url` (`http://localhost:8000/files/<uuid>.stl`) und die Bounding-Box-Maße zurück.
2. **`resolve_converted_stl(file_url)`** – mappt die vom Frontend gelieferte URL zurück auf den lokalen Pfad (nimmt nur den Dateinamen → kein Path-Traversal).
3. **`compute_scaled_volume_mm3(stl, scaled_length)`** – Volumen der **konvexen Hülle** (`trimesh.mesh.convex_hull.volume`), in mm³. Optional auf eine skalierte Länge normiert (Faktor `scaled_length / bbox_x`). Entspricht der Frontend-Berechnung.
4. **`ensure_vhacd_collision_mesh(stl)`** – erzeugt **einmalig** eine approximative konvexe Zerlegung (V-HACD) der STL als `.obj` und cacht sie (`<name>.vhacd-<param-hash>.obj`). Nötig, weil PyBullet dynamische Mesh-Körper sonst als **eine** konvexe Hülle behandelt → konkave Artikel könnten sich nicht verschachteln. Parameter (`VHACD_PARAMS`) sind bewusst grob gewählt (~5 Teilkörper): Benchmark zeigte, dass die PyBullet-Defaults 19 Teile erzeugen und die Physik-Schritte 6,5× langsamer machen (78 s vs. 12 s für 60 Artikel/400 Steps), während 5 Teile praktisch gleich schnell wie eine einzelne konvexe Hülle sind (12,6 s vs. 12,1 s), aber die konkave Grundform erhalten.

**Drei verschiedene Volumenbegriffe** (bewusst getrennt):
- **Konvexe Hülle** – effektiver Platzbedarf bei Schüttung (Standard von `compute_scaled_volume_mm3`).
- **Rasterzellen-Volumen** (`sx·sy·sz`) – effektiver Platzbedarf im Packmuster inkl. Verschachtelung (in `packing.py` als `effective_volume`).
- **Bounding-Box** – Fallback / grobe Näherung.

---

## 6. Packmuster-Algorithmus (`optimizer.py`)

Klasse `PackingOptimizer(item, quantity, boxes, pattern, mesh_volume)`. Kernmethode `_pack_pattern(box)`.

**Grundprinzip: Greedy mit Extreme Points** (nach Crainic, Perboli, Tadei 2008). Es wird eine Menge von Extrempunkten verwaltet, an denen ein Artikel platziert werden kann; Start = Ursprung der leeren Box. Pro Schritt wird ein Artikel platziert, der belegte Punkt entfernt und an den Ecken drei neue Extrempunkte erzeugt. Ende, wenn `quantity` erreicht oder kein Punkt mehr passt.

**Eingabe „Pattern":** Der Nutzer ordnet in der Rendering-Ansicht Artikel im 3D an. Daraus werden **Rasterschritte** (Mitte-zu-Mitte-Abstand pro Achse) abgeleitet (`_pattern_step`). Ist der Schritt kleiner als die Kantenlänge → **bewusste Verschachtelung**.

**Dual-Dimension-Prinzip (`_fits_overlap`):**
- Box-Grenze wird mit den **vollen** Artikelkanten geprüft (nichts ragt raus).
- Kollision gegen bereits platzierte Artikel wird mit den **reduzierten** (effektiven) Kanten `eff_dims = (sx, sy, sz)` geprüft → erlaubt die gewollte Überlappung.

**Orientierungswahl:** Alle 6 Achspermutationen werden getestet. Für jede wird das Grid `nx·ny·nz` (Anzahl Plätze pro Achse) berechnet.

**Restraum-Füllung (`_fill_residual`):** Nach dem Hauptgrid werden drei überlappungsfreie Restquader (Streifen in x, y, z) mit der jeweils besten Einzel-Orientierung (volle Kanten, keine Verschachtelung) aufgefüllt. `total_capacity = Hauptgrid + Restraum`. Orientierungen, die `quantity` auch mit Restraum nicht fassen, werden verworfen.

**Scoring der Orientierung** (kleinster ist besser, als Tupel):
```python
score = (-excess_capacity, -estimated_used_volume, -capacity)
```
d. h. primär möglichst wenig Überkapazität, dann kleinstes tatsächlich genutztes Volumen, dann kleinste Gesamtkapazität.

**Ergebnis pro Box** (Auszug): `box`, `box_dimensions`, `article_dims`, `orientation`, `rotation_key`, `grid`, `capacity`, `lhm_capacity`, `fill_rate`, `empty_volume`, `used_volume`, `positions` (jede Position mit x/y/z-Mittelpunkt, orientation, rotation_key, rotation, pattern_index).
- `fill_rate = single_volume * quantity / box.volume`, wobei `single_volume = mesh_volume` (effektives Volumen inkl. Overlap) falls gesetzt, sonst Bounding-Box.

**Ranking (`find_top_boxes`):** dedupliziert nach Boxmaßen, ruft `get_lhm_capacity(box)`, sortiert die Kandidaten **nach Boxvolumen aufsteigend** (kleinste passende Box zuerst) und gibt die ersten `limit` zurück (Route ruft mit `limit=50`).

> Wichtige Eigenschaft: Bei **fixer Stückzahl** ist das Füllgrad-Ranking äquivalent zu „kleinste Box zuerst", weil der Zähler konstant ist. Deshalb wird direkt nach Boxvolumen sortiert.

---

## 7. Vorfilterung des Katalogs (`box_loader.py`)

`load_boxes_from_csv(csv_path, quantity, bulk, mesh_volume, stability, estimated_packing_density)`.

Gemeinsam: optionaler **Stabilitätsfilter** (nur Boxen der geforderten Güte). `article_volume = mesh_volume * quantity`.

**Packmuster-Pfad (`bulk=False`):** behält Boxen mit `article_volume <= box_volume` (notwendige Volumenbedingung), sortiert nach Volumen, gibt die ersten **200** zurück. `mesh_volume` ist hier das **effektive** Volumen (Rasterzelle inkl. Overlap).

**Schüttgut-Pfad (`bulk=True`):** behält Boxen, deren **theoretische Auslastung** `article_volume/box_volume` in einem Band liegt:
- Untergrenze fest `0.15`.
- Obergrenze `min(0.60, estimated_packing_density * 1.3)`, sonst `0.40`.
Begründung: Eine Zufallsschüttung erreicht real nur ~35–55 % Dichte; Boxen mit zu hoher geforderter Auslastung können nie passen, stark überdimensionierte werden ausgesortiert. Sortiert nach Volumen, erste **20**. `estimated_packing_density` kommt aus einer Vorab-Schätzung (siehe §8).

---

## 8. Schüttgut-Simulation (`sim.py`)

Zwei zentrale Objekte: `SimulationConfig` (dataclass mit allen Parametern) und `PackagingSimulation` (führt die Physik aus).

### Ablauf pro Box (`_run_single`)
`_connect → _create_box → _create_article_shapes → _spawn_articles → _simulate → _evaluate` (und bei GUI: `_hold_gui_open`), am Ende immer `_disconnect`.

### Box-Konstruktion (`_create_box`)
- **Boden:** Quader der Dicke `wall_thickness`, Oberkante bei `z = wall_thickness`.
- **Wände:** Die übergebenen Boxmaße sind **Innenmaße**. Die Wände **setzen auf dem Boden auf** (Start bei `z = wall_thickness`), damit die nutzbare Innenhöhe über dem Boden exakt `box_z` beträgt.
- **Zwei Wandhöhen:** Die **Kollisionswand** ist bewusst hoch (`wall_height = max(box_z, spawn_wall_height)`), damit einfallende Artikel nicht überschwappen. Die **sichtbare (visuelle) Wand** hat die echte Innenhöhe `box_z` (blau, transparent). Damit PyBullet im GUI nicht die hohe Kollisionsgeometrie zeichnet, bekommen die hohen Kollisionswände eine **komplett transparente** Visual-Shape (Alpha 0).

### Artikel-Kollisionsform (`_create_article_shapes`)
Bevorzugt das **V-HACD-OBJ** (konvexe Zerlegung, formtreu für konkave Artikel), Fallback auf die rohe STL. `mesh_scale = (0.001, 0.001, 0.001)` (mm → m).

### Spawnen (`_spawn_articles`)
Artikel werden **oberhalb** der Box erzeugt und fallen hinein. Position: `x,y = uniform(-box_x/3, box_x/3)` bzw. `-box_y/3..box_y/3` (zentrales Drittel), in Spalten zu je 6 gestapelt (`layer = i % 6`, `stack = i // 6`). Zufällige Orientierung. Materialparameter pro Artikel: `lateralFriction=0.2`, `spinning/rollingFriction=0.0005`, `linear/angularDamping=0.04`, `restitution=0`, `collisionMargin` aus Config.
> Bekanntes Problem: In **breiten, flachen** Boxen bildet sich durch den zentralen Spawn ein **Hügel** (Schüttwinkel) → hohe Füllhöhe bei schlechter Packdichte (siehe §12).

### Simulation (`_simulate`)
1. **Phase 1 – freier Fall:** `_step_until_settled()` bis Ruhe.
2. **Früh-Abbruch:** liegt die Füllhöhe > `box_z * early_validation_factor` (1,5), wird sofort abgebrochen (Box passt nie).
3. **Verdichtung:** Gravitation kurz auf −100 erhöht, dann `_settle_items_with_impulse` (laterale Sinus-Impulse, „Rütteln"), danach Gravitation zurück auf −9,81.
4. **Phase 2 – erneutes Settling** bis Ruhe.

**Abbruchkriterium (`_step_until_settled`):** läuft bis `max_simulation_steps`, prüft alle `settle_check_interval` Schritte die **Höhen-Konvergenz** – ändert sich die Füllhöhe zwischen zwei Checks um weniger als `height_change_mm` (0,5 mm) und ist `min_simulation_steps` erreicht → Abbruch. Das macht die Simulation deutlich schneller, weil auf das eigentliche Ziel (Füllhöhe) statt auf Ruhe jedes Einzelteils geprüft wird.

**Füllhöhe (`_current_max_z`):** Oberkante der Schüttung = Maximum der **AABB-Oberkanten** aller Artikel (gilt auch für gekippte Artikel). `filling_height = max_z − wall_thickness` (Höhe über dem Boden).

### Mehrere Läufe & Reproduzierbarkeit
- `run_single_box_simulation` führt `runs_per_box` Läufe mit unterschiedlichen, aber deterministischen Seeds aus: `seed = random_seed + box_index*1000 + run_index`. Numerische Kennzahlen werden **gemittelt**; zusätzlich wird `filling_height_std_mm` (Streuung) ausgegeben.
- Der **effektive Seed** des ersten Laufs wird als `random_seed` ins Ergebnis geschrieben → erlaubt exakte Reproduktion im GUI-Re-Run.

### Vorab-Dichteschätzung (`estimate_bulk_packing_density`)
Simuliert 3 feste Referenzboxen (klein/mittel/groß) und liefert die **Median-Packdichte**. Dient nur der Kalibrierung der Vorfilter-Obergrenze im `box_loader`.

### Parallelisierung (`run`)
- `use_gui=True` → genau ein Lauf im GUI-Fenster (Debug/Re-Run).
- sonst sequenziell (bei einer Box) oder über `ProcessPoolExecutor` (eine Box pro Kern).
- Ergebnis wird durch `_get_best_valid_results` gefiltert (nur `fits_in_box`) und sortiert.

### Aktuelle Standard-Parameter (`SimulationConfig`)
```
item_mass=0.01, wall_thickness=0.01 (10 mm), mesh_scale=(0.001,0.001,0.001)
fixed_time_step=1/480, solver_iterations=80
max_simulation_steps=350, min_simulation_steps=60, settle_check_interval=20
height_change_mm=0.5, early_validation_factor=1.5
settle_duration=1, settle_force_scale=0.5, settle_frequency=1
collision_margin=0.00002, fit_height_tolerance=0.02
random_seed=42, runs_per_box=1
```
> **Achtung (siehe §9):** Diese Werte weichen teils von den in der Validierung ermittelten Kalibrierwerten ab – vor Aussagen zur Validierung prüfen.

---

## 9. Kennzahlen (exakte Definitionen)

Alle Sim-Volumina intern in m³, Ausgabe in cm³. Boxmaße in mm.

- **`filling_height_mm`** = (`max_z` − `wall_thickness`) · 1000. Höhe der Schüttung über dem Boden. `max_z` = höchste AABB-Oberkante.
- **`relative_filling_height_percent`** = `filling_height / box_z · 100`. Ausnutzung der Boxhöhe.
- **`packing_density_percent`** = `total_article_volume / used_box_volume · 100`, mit `used_box_volume = box_x·box_y·filling_height`. → Wie **dicht** die Schüttung *in sich* ist (bis zur Füllhöhe). Erreicht real ~38–46 %.
- **`fits_in_box`** = `filling_height ≤ box_z · (1 + fit_height_tolerance)`. Deckel-Toleranz 2 %, weil die Füllhöhe die oberste Ecke *eines* Artikels ist und ein Deckel einzelne herausragende Teile flach drückt.
- **`box_utilization`** = `total_article_volume / box_volume` (Gesamtbox). Wird berechnet, ist aber aktuell **nicht** im Ergebnis-Dict enthalten (siehe §12).
- **`articles_per_lhm`** = `item_quantity · box.lhm_capacity` (wie viele Artikel gesamt auf ein LHM).
- **Artikelvolumen (Schüttung):** echtes Mesh-Volumen (konvexe Hülle) `mesh_volume`, mm³→m³, um die `mesh_scale` korrigiert.

**Packmuster-Kennzahlen:** `fill_rate = effective_volume·quantity / box.volume`, `used_volume`, `empty_volume`, `capacity`, `lhm_capacity`.

---

## 10. LHM-Kapazität (`lhm.py`)

`get_lhm_capacity(box)` – wie viele Exemplare einer Box auf ein LHM (600 × 400 × 220 mm) passen. Testet alle Orientierungen der Box, rechnet `nx·ny·nz` per Ganzzahl-Division und nimmt das Maximum. Passt die Box in **keiner** Orientierung → `return 0` (nicht LHM-fähig). Rückgabe: `int`.

---

## 11. Kalibrierung und Validierung

Die Simulation wurde gegen **reale VPE-Referenzfälle** von Phoenix Contact validiert (STP-Dateien vorhanden):

| Artikel | Reale VPE | Simulationsergebnis |
|---|---|---|
| **1767025** | 50 Stück in 145 × 96 × 90 mm | ~50–51 mm Füllhöhe → **passt** ✅ |
| **1754449** | 100 Stück in 85 × 96 × 60 mm (Kapazitätsgrenze) | ~60,3 ± 0,3 mm bei 60 mm → **passt** (mit 2 % Toleranz) ✅, Abweichung ~0,5 % |

**Kalibrier-Erkenntnisse (Diagnose per Einzelexperiment am Grenzfall 1754449):**
1. **Kollisionsmarge war der dominante Fehler.** Der Bullet-Default erzeugt bei kleinen Artikeln (~10–30 mm) künstliche Spalte → Füllhöhe wurde um ~14 % überschätzt (68,7 → 60,1 mm). Fix: `collisionMargin` klein setzen (in der Validierung **0,0002 m = 0,2 mm**).
2. **VHACD-Feinheit:** kein messbarer Effekt für diesen Artikel (er hat eine innenliegende Konkavität, die VHACD nicht zerlegt → immer 1 Teil, +67 % „Phantom-Volumen").
3. **Rütteldauer:** kleiner Effekt (~1 mm).
4. **Seed-Streuung:** an der Kapazitätsgrenze ±2,4 mm → Mittelung über mehrere Läufe (`runs_per_box`) nötig für belastbare Aussagen.
5. **Deckel-Toleranz 2 %** (`fit_height_tolerance`): begründet über den Deckelandruck.

> **WICHTIGER HONESTY-HINWEIS für die Arbeit:** Die aktuell im Code stehenden Standard-Parameter (§8) weichen teilweise von den validierten Werten ab – u. a. `collision_margin` (jetzt 0,00002 statt 0,0002), `runs_per_box` (jetzt 1 statt 3 bei der Validierung), sowie geänderte Rüttel-Parameter und Verdichtungsgravitation (−100 statt −50). Wer die Validierungszahlen in der Arbeit berichtet, muss sicherstellen, dass die dort beschriebenen Parameter mit denen übereinstimmen, mit denen die Zahlen erzeugt wurden. Am besten die Referenzfälle mit den finalen Parametern erneut laufen lassen und die Ergebnisse frisch dokumentieren.

**Performance-Ergebnisse (gemessen):**
- VHACD grob (5 statt 19 Teile): Physik-Schritte 6,5× schneller.
- Höhen-Konvergenz + Früh-Abbruch: pro Box ~5× schneller (Grenzfall ~30 s → ~6 s).

---

## 12. Bekannte Einschränkungen / offene Punkte

- **Hügelbildung bei breiten Boxen:** Zentraler Spawn (nur mittleres Drittel) + Schüttwinkel → Kegel in der Mitte, leere Ecken → hohe Füllhöhe, schlechte Dichte. Physikalisch plausibel für einen Punkt-/Zentraleinlauf. Verbesserungshebel (noch nicht umgesetzt): Spawn über die volle Grundfläche verteilen (verwürfeltes Raster), lagenweises Befüllen, vertikales Klopfen zum Einebnen, Reibungskalibrierung. Welcher Hebel „richtig" ist, hängt vom realen Einfüllprozess ab.
- **`box_utilization` wird berechnet, aber nicht ins Ergebnis geschrieben.** `_get_best_valid_results` sortiert nach `box_utilization_percent` (Default 0) → die Sortierung ist praktisch wirkungslos; die Ergebnisse behalten die Volumen-Reihenfolge aus dem `box_loader` (kleinste zuerst). Sollte konsolidiert werden.
- **Validierungsstichprobe = 2 Artikel.** Methodik steht, mehr Referenzfälle wären der nächste Schritt.
- **Gewicht** wird nicht durchgängig genutzt (keine Traglastprüfung pro Box, obwohl der Katalog es hergäbe).
- **LHM-Kapazität im Packmuster** kommt aus der CSV-Spalte bzw. `get_lhm_capacity`, nicht aus einem erneuten Packing-Lauf.
- **GUI-Simulation** öffnet ein Fenster **auf dem Server** – für einen entfernten Nutzer nicht sichtbar. Lösungsidee (nicht umgesetzt): Trajektorie headless aufzeichnen und im Frontend (Three.js) abspielen.
- **Einheitliches Lagenlayout für maschinelles Verpacken** ist konzeptionell erwähnt, aber nicht implementiert.

---

## 13. API-Endpunkte (Verträge)

**`POST /packing/top20`** (Packmuster). Request `PackingRequest`: `item_length, item_width, item_height, file_url, quantity, scaledLength, pattern?, mesh_volume?, stability`. Response: `{ message, results: [...] }`.

**`POST /simulation/run`** (Schüttgut, headless). Request = `SimulationConfig` (u. a. `item`, `item_quantity`, `stl_file`, `stability`, …). Ablauf: STL auflösen → Volumen + VHACD → Dichteschätzung → `box_loader(bulk=True)` → LHM-Kapazität je Box → parallele Simulation → gefilterte, sortierte Ergebnisliste.

**`POST /simulation/run-single-box`** (GUI-Re-Run einer bestimmten Box). Request `SingleBoxSimulationRequest`: `config` (SimulationConfig), `box` (name+Maße+lhm_capacity), `box_name`, `estimated_density?`, `random_seed?`. Erzwingt `use_gui=True`, `parallel_simulations=False`, `runs_per_box=1` und den mitgeschickten `random_seed` → **exakte Reproduktion** der Schüttung, die zu den Kennwerten auf der Result-Page gehört. (`box_name`/`estimated_density` werden vom Backend nicht genutzt.)

**`POST /upload-stl` / `/convert-stp-to-stl`** – Datei speichern/konvertieren; liefert `file_id`, `file_url`, `stl_file` (lokaler Pfad), `item` (Bounding-Box-Maße).

---

## 14. Aktuelle Gliederung der Arbeit (4 Kapitel)

Die Arbeit wurde bewusst grob gegliedert (Feedback: nicht zu kleinteilig):
1. **Einleitung** – Problemstellung/Motivation; Ziel, Vorgehensweise und Aufbau.
2. **Theoretische Grundlagen** (nur Fremdwissen): Verpackungslogistik (VPE, LHM, Funktionen); Einflussgrößen; Packungsprobleme (Bin-Packing-Typologie, exakte Verfahren vs. Heuristiken, Greedy, Extreme Points); simulationsbasierte Schüttgutbetrachtung (physikbasierte Simulation, PyBullet, konvexe Zerlegung/V-HACD); Stand der Technik.
3. **Konzeption und Umsetzung** (Eigenleistung): Problemformalisierung + Ist-Analyse + Anforderungen (FA1–FA8, NFA1–NFA5); Systemarchitektur + Benutzeroberfläche; Ermittlung und Bewertung (Vorfilterung, Packmuster-Verfahren, Schüttgut-Verfahren, Bewertung/Rangfolge).
4. **Evaluation:** Testfälle; Kalibrierung/Validierung; Ergebnisse (Füllgrad, Laufzeit gegen NFA1 < 10 s, Nachvollziehbarkeit); Diskussion/Einordnung; Fazit und Ausblick.

**Zentrale Anforderungen (Auszug):** FA4 = Packmuster + Füllgrad pro Box (Verschachtelung, Rotation); FA5 = Schüttgut simulieren (Füllgrad + Freiraum zum Deckel); FA6 = Top-5 mit Kennzahlen ausgeben; FA7 = Packmuster visualisieren; FA8 = beschaffungsstarke Boxen bevorzugen. NFA1 = Berechnung < 10 s; NFA2 = Nachvollziehbarkeit; NFA4 = reproduzierbar (Packmuster deterministisch, Schüttgut per festem Seed).

---

## 15. Zitierfähige Literatur (Grundlagen des Codes)

- **Extreme-Point-Greedy** → Crainic, Perboli, Tadei (2008): *Extreme Point-Based Heuristics for Three-Dimensional Bin Packing*, INFORMS J. Computing 20(3), 368–384. DOI 10.1287/ijoc.1070.0250. (Frei: CIRRELT-2007-41.)
- **Bin-Packing-Typologie/Einordnung** → Wäscher, Haußner, Schumann (2007): *An improved typology of cutting and packing problems*, EJOR 183(3), 1109–1130. DOI 10.1016/j.ejor.2005.12.047.
- **Physik-Engine** → Coumans & Bai (2016–2021): *PyBullet*.
- **Konvexe Zerlegung (V-HACD)** → Mamou & Ghorbel (2009): *A simple and efficient approach for 3D mesh approximate convex decomposition*, ICIP, 3501–3504. DOI 10.1109/ICIP.2009.5414068.
- **Konvexe Hülle (Qhull)** → Barber, Dobkin, Huhdanpaa (1996): *The Quickhull Algorithm for Convex Hulls*, ACM TOMS 22(4), 469–483. DOI 10.1145/235815.235821.
- **Mesh-Volumen (vorzeichenbehaftete Tetraeder)** → Zhang & Chen (2001): *Efficient feature extraction for 2D/3D objects in mesh representation*, ICIP. DOI 10.1109/ICIP.2001.958278.
- **Verpackungslogistik** → Kaßmann (2020), *Grundlagen der Verpackung*; **Logistik** → Muchna et al. (2018), *Grundlagen der Logistik*; **Faltschachtel-Normen** → FEFCO Code (2022).

---

*Ende des Kontextdokuments. Der Code ist die maßgebliche Quelle; bei Widersprüchen zwischen diesem Dokument und dem Code gilt der Code.*
