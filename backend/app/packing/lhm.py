from itertools import permutations
from math import floor
from app.packing.models import Box

lhm_length = 570.0
lhm_width = 370.0
lhm_height = 190.0
tolerance = 1e-9


def get_lhm_capacity(box: Box) -> int:
    # 0 = Box passt in keiner Orientierung auf das LHM
    best = 0

    for L, W, H in set(permutations((box.length, box.width, box.height))):
        if (
            L > lhm_length + tolerance
            or W > lhm_width + tolerance
            or H > lhm_height + tolerance
        ):
            continue

        count = (
            floor((lhm_length + tolerance) / L)
            * floor((lhm_width + tolerance) / W)
            * floor((lhm_height + tolerance) / H)
        )
        best = max(best, count)

    return best
