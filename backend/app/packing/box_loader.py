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


def _load_bulk_boxes(
    rows,
    total_article_volume: float,
    stability: str,
    estimated_packing_density: float | None,
) -> list[Box]:
    """schuettgut-pfad: zusaetzlich ueber die geforderte packdichte filtern.
    zufallsschuettung erreicht real nur ~35-55 % dichte -- boxen, die eine
    zu hohe oder eine sehr niedrige dichte verlangen, koennen nie sinnvoll passen."""
    if estimated_packing_density is not None:
        upper_density_limit = estimated_packing_density * 1.3
    else:
        upper_density_limit = 0.40
    lower_density_limit = 0.15

    boxes: list[Box] = []
    for row in rows:
        if not _matches_stability(row, stability):
            continue
        box = _box_from_row(row)
        required_density = total_article_volume / box.volume if box.volume > 0 else 0
        if (
            total_article_volume <= box.volume
            and lower_density_limit < required_density < upper_density_limit
        ):
            boxes.append(box)
    return boxes


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

    boxes.sort(key=lambda box: box.volume)
    return boxes[:limit]
