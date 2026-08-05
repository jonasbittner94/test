'''Geometrie-Helfer: konvexe Zerlegung und Volumenberechnung aus einem STL-Mesh.'''

import hashlib
from pathlib import Path

import numpy as np
import trimesh

from app.core.config import convert_directory


def resolve_converted_stl(stl_url: str) -> Path:
    stl_name = Path(stl_url).name  # nur der Dateiname, verwirft Host/Pfad
    path = convert_directory / stl_name
    if not path.is_file():
        raise FileNotFoundError(f"STL-Datei nicht gefunden: {stl_name}")
    return path


VHACD_PARAMS = {
    # V-HACD 4 (vhacdx, ueber trimesh.convex_decomposition). Anders als bei
    # pybullets V-HACD 2 steuert maxConvexHulls die Teilezahl direkt --
    # frueher musste concavity/gamma indirekt darauf hintrimmen.
    # Benchmark (60 Artikel, 400 Steps): konvexe Huelle 12.1s | 5 Teile 12.6s |
    # 19 Teile 78.4s -> 5 Teile sind der Sweet Spot.
    "maxConvexHulls": 5,
    "resolution": 300_000,
    "maxNumVerticesPerCH": 32,
    "minimumVolumePercentErrorAllowed": 1.0,
}


def _vhacd_params_tag() -> str:
    """Kurzer Fingerprint der Parameter -> Cache wird bei Aenderung ungueltig."""
    raw = repr(sorted(VHACD_PARAMS.items())).encode()
    return hashlib.md5(raw).hexdigest()[:8]


def ensure_vhacd_collision_mesh(stl_path: str | Path) -> Path:
    """Erzeugt (einmalig) eine konvexe Zerlegung der STL für die Physik.

    MuJoCo kollidiert ein Mesh-Geom immer als konvexe Hülle -- konkave Artikel
    (Vertiefungen, Löcher, L-Formen) kollidieren damit falsch und die Schüttung
    wird zu locker. Erst die Zerlegung in mehrere konvexe Teilkörper macht die
    Kollision formtreu. sim_mujoco._collision_part_vertices legt je Teil ein
    eigenes Geom an.

    Gerechnet wird die Zerlegung von vhacdx (V-HACD 4) über
    trimesh.convex_decomposition -- kein pybullet mehr nötig.

    Das Ergebnis wird als npz neben der STL gecacht
    (<name>.vhacd-<tag>.npz) und nur neu berechnet, wenn die STL neuer ist
    oder VHACD_PARAMS geändert wurden.
    """
    stl_path = Path(stl_path)
    cache = stl_path.with_name(f"{stl_path.stem}.vhacd-{_vhacd_params_tag()}.npz")

    if cache.is_file() and cache.stat().st_mtime >= stl_path.stat().st_mtime:
        return cache

    mesh = trimesh.load(str(stl_path), force="mesh")
    parts = mesh.convex_decomposition(**VHACD_PARAMS)
    if not parts:
        raise RuntimeError(f"Konvexe Zerlegung fehlgeschlagen für {stl_path.name}")

    np.savez_compressed(
        cache,
        **{f"part{i:03d}": np.asarray(p.vertices) for i, p in enumerate(parts)},
    )
    return cache


# Berechnung des Volumens der konvexen Hülle des Meshes (wie im Frontend).
def compute_convex_volume(
    stl_file: str | Path, scaled_length: float | None = None
) -> float:
    """Volumen wie im Frontend (konvexe Hülle), in mm^3.

    Optional auf die skalierte Länge normiert (entspricht baseVolume * factor
    im Frontend: factor = scaled_length / size.x).
    """
    mesh = trimesh.load(str(stl_file), force="mesh")
    vol = float(mesh.convex_hull.volume)
    if scaled_length and scaled_length > 0:
        size_x = mesh.bounding_box.extents[0]  # == size.x im Frontend
        if size_x > 0:
            vol *= scaled_length / size_x
    return vol