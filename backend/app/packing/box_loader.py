'''Logik zum Einlesen der Verpackungen aus der CSV.'''

import csv
from pathlib import Path
from app.packing.models import Box
from app.packing.lhm import get_lhm_capacity


def _matches_stability(row, stability: str) -> bool:
    """true, wenn die box zur gewuenschten stabilitaet passt (oder egal ist)."""
    if stability in ("", "Beliebig"):
        return True
    return row.get("Stabilität", "") == stability


def _box_from_row(row) -> Box:
    box = Box(
        name=row["Object Name"],
        length=float(row["length"]),
        width=float(row["width"]),
        height=float(row["height"]),
        lhm_capacity=0,
    )
    # Einzige Stelle, an der die LHM-Kapazitaet bestimmt wird: immer geometrisch
    # berechnet, der SAP-Wert aus der CSV wird bewusst ignoriert.
    # Alle Aufrufer lesen nur box.lhm_capacity.
    box.lhm_capacity = get_lhm_capacity(box)
    return box


def _load_pattern_boxes(rows, article_volume_sum: float, stability: str) -> list[Box]:
    """packmuster-pfad: nur boxen, in die die artikel volumenmaessig passen."""
    boxes: list[Box] = []
    for row in rows:
        if not _matches_stability(row, stability):
            continue
        box = _box_from_row(row)
        if article_volume_sum <= box.volume:
            boxes.append(box)
    return boxes


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(value, upper))

def _load_bulk_boxes(
    rows,
    article_volume_sum: float,
    stability: str,
    expected_fillrate: float | None,
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
    if expected_fillrate is None or expected_fillrate <= 0:
        fillrate = 0.4
    else:
        fillrate = _clamp(expected_fillrate, 0.40, 0.80)

    fitting_boxes: list[tuple[float, Box]] = []
    fallback_boxes: list[tuple[float, Box]] = []

    for row in rows:
        if not _matches_stability(row, stability):
            continue

        box = _box_from_row(row)

        if box.volume <= 0:
            continue

        required_density = article_volume_sum / box.volume

        # fitting_ratio <= 1 bedeutet:
        # Box ist nach konservativer Packdichte gross genug.
        fitting_ratio = required_density / fillrate

        if fitting_ratio <= 1.0:
            fitting_boxes.append((fitting_ratio, box))
        else:
            fallback_boxes.append((fitting_ratio, box))

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
    existing_dims: set[tuple[float, float, float]] = set()

    for box in boxes:
        base_a, base_b = sorted((box.length, box.width), reverse=True)
        dimensions = (base_a, base_b, box.height)

        if dimensions in existing_dims:
            continue

        existing_dims.add(dimensions)
        unique.append(box)

    return unique


def load_boxes_from_csv(
    box_data_path: str,
    quantity: int,
    bulk: bool,
    mesh_volume: float,
    stability: str,
    expected_fillrate: float | None = None,
) -> list[Box]:
    path = Path(box_data_path)

    # gesamtvolumen aller artikel einer vpe -> grober vorfilter fuer die boxen
    article_volume_sum = mesh_volume * quantity

    with path.open(newline="", encoding="utf-8") as box_data:
        rows = list(csv.DictReader(box_data))

    if bulk:
        boxes = _load_bulk_boxes(rows, article_volume_sum, stability, expected_fillrate)
        limit = 10
    else:
        boxes = _load_pattern_boxes(rows, article_volume_sum, stability)
        limit = 200

    boxes = _unique_boxes_by_dimensions(boxes)
    boxes.sort(key=lambda box: box.volume)
    return boxes[:limit]
