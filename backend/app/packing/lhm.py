from itertools import permutations
from math import floor
from app.packing.models import Box

LHM_LENGTH = 570.0
LHM_WIDTH = 370.0
LHM_HEIGHT = 190.0
EPS = 1e-9


def get_lhm_capacity(box: Box) -> int:
    # 0 = Box passt in keiner Orientierung auf das LHM
    best = 0

    for L, W, H in set(permutations((box.length, box.width, box.height))):
        if (
            L > LHM_LENGTH + EPS
            or W > LHM_WIDTH + EPS
            or H > LHM_HEIGHT + EPS
        ):
            continue

        count = (
            floor((LHM_LENGTH + EPS) / L)
            * floor((LHM_WIDTH + EPS) / W)
            * floor((LHM_HEIGHT + EPS) / H)
        )
        best = max(best, count)

    return best

def resolve_lhm_capacity(box: Box, csv_value: float | None = None) -> int:
    """Boxen pro LHM C. Wenn Wert aus SAP vorhanden ist diesen nehmen, sonst selbst berechnen."""
    if csv_value and csv_value > 0:
        return int(csv_value)
    return get_lhm_capacity(box)
