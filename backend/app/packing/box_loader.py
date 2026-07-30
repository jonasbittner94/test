'''Logik zum Einlesen der Verpackungen aus der CSV.'''

import csv
from pathlib import Path
from app.packing.optimizer import Box


def _safe_float(value):
    """float aus der csv lesen; leere oder kaputte zellen werden zu 0.0."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _matches_stability(row, stability: str) -> bool:
    """true, wenn die box zur gewuenschten stabilitaet passt (oder egal ist)."""
    if stability in ("", "beliebig"):
        return True
    return row.get("Stabilität", "") == stability


def _box_from_row(row) -> Box:
    return Box(
        name=row["Object Name"],
        length=float(row["length"]),
        width=float(row["width"]),
        height=float(row["height"]),
        lhm_capacity=_safe_float(row["Amount per bin box (LHM C)"]),
    )


def _load_pattern_boxes(rows, total_article_volume: float, stability: str) -> list[Box]:
    """packmuster-pfad: nur boxen, in die die artikel volumenmaessig passen."""
    boxes: list[Box] = []
    for row in rows:
        if not _matches_stability(row, stability):
            continue
        box = _box_from_row(row)
        if total_article_volume <= box.volume:
            boxes.append(box)
    return boxes


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(value, upper))

def _load_bulk_boxes(
    rows,
    total_article_volume: float,
    stability: str,
    estimated_packing_density: float | None,
) -> list[Box]:
    """
    Schuettgut-Pfad: robuste Vorfilterung.

    Ziel:
    - Boxen bevorzugen, die volumetrisch mit konservativer Packdichte passen.
    - Keine harte Untergrenze fuer required_density verwenden, damit grosse
      Boxen als Fallback erhalten bleiben.
    - Wenn keine Box rechnerisch passt, trotzdem die besten Kandidaten liefern.
    """

    # Fallback/Clamp verhindert, dass eine schlechte Simulation die Vorfilterung
    # komplett leer macht.
    if estimated_packing_density is None or estimated_packing_density <= 0:
        packing_density = 0.35
    else:
        packing_density = _clamp(estimated_packing_density, 0.40, 0.80)

    # Sicherheitsfaktor: rechne konservativer als die geschaetzte Packdichte.
    # Beispiel: 0.35 / 1.25 = 0.28 effektiv nutzbare Dichte.
    safety_factor = 1
    usable_packing_density = packing_density / safety_factor

    fitting_boxes: list[tuple[float, Box]] = []
    fallback_boxes: list[tuple[float, Box]] = []

    for row in rows:
        if not _matches_stability(row, stability):
            continue

        box = _box_from_row(row)

        if box.volume <= 0:
            continue

        required_density = total_article_volume / box.volume

        # overflow_ratio <= 1 bedeutet:
        # Box ist nach konservativer Packdichte gross genug.
        overflow_ratio = required_density / usable_packing_density

        if overflow_ratio <= 1.0:
            fitting_boxes.append((overflow_ratio, box))
        else:
            fallback_boxes.append((overflow_ratio, box))

    if fitting_boxes:
        # Bevorzugt Boxen, die passen, aber nicht riesig ueberdimensioniert sind.
        fitting_boxes.sort(
            key=lambda entry: (
                entry[0],          # knapp passend / geringe Ueberdimensionierung
                entry[1].volume,   # kleinere Box bevorzugen
            ),
            reverse=False,
        )
        return [box for _, box in fitting_boxes]

    # Fallback: Keine Box passt rechnerisch.
    # Trotzdem beste Kandidaten zur Simulation weitergeben.
    fallback_boxes.sort(
        key=lambda entry: (
            entry[0],          # geringste rechnerische Ueberfuellung
            -entry[1].volume,  # bei Gleichstand groessere Box bevorzugen
        )
    )

    return [box for _, box in fallback_boxes]

def _unique_boxes_by_dimensions(boxes: list[Box]) -> list[Box]:
    """Entfernt Boxen mit identischen Abmessungen, unabhaengig von L/W-Reihenfolge."""
    unique: list[Box] = []
    seen_dimensions: set[tuple[float, float, float]] = set()

    for box in boxes:
        base_a, base_b = sorted((box.length, box.width), reverse=True)
        dimensions = (base_a, base_b, box.height)

        if dimensions in seen_dimensions:
            continue

        seen_dimensions.add(dimensions)
        unique.append(box)

    return unique


def load_boxes_from_csv(
    csv_path: str,
    quantity: int,
    bulk: bool,
    mesh_volume: float,
    stability: str,
    estimated_packing_density: float | None = None,
) -> list[Box]:
    path = Path(csv_path)

    # gesamtvolumen aller artikel einer vpe -> grober vorfilter fuer die boxen
    total_article_volume = mesh_volume * quantity

    with path.open(newline="", encoding="utf-8") as csvfile:
        rows = list(csv.DictReader(csvfile))

    if bulk:
        boxes = _load_bulk_boxes(rows, total_article_volume, stability, estimated_packing_density)
        limit = 20
    else:
        boxes = _load_pattern_boxes(rows, total_article_volume, stability)
        limit = 200

    boxes = _unique_boxes_by_dimensions(boxes)

    boxes.sort(key=lambda box: box.volume)
    return boxes[:limit]
