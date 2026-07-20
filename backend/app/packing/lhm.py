from itertools import permutations
from math import floor
from app.packing.models import Box

LHM_LENGTH = 600.0
LHM_WIDTH = 400.0
LHM_HEIGHT = 220.0
EPS = 1e-9


def get_lhm_capacity(box: Box) -> int:
    best = None

    for dims in set(permutations((box.length, box.width, box.height))):
        L, W, H = dims

        if (
            L > LHM_LENGTH + EPS
            or W > LHM_WIDTH + EPS
            or H > LHM_HEIGHT + EPS
        ):
            continue

        nx = floor((LHM_LENGTH + EPS) / L)
        ny = floor((LHM_WIDTH + EPS) / W)
        nz = floor((LHM_HEIGHT + EPS) / H)
        count = nx * ny * nz

        if best is None or count > best["capacity"]:
            best = {
                "box": box.name,
                "capacity": count,
            }

    # Box passt in keiner Orientierung auf das LHM -> keine Kapazitaet
    if best is None:
        return 0

    return best["capacity"]
