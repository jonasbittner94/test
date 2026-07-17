'''Geometrie-Helfer: Volumenberechnung aus einem STL-Mesh.'''

import hashlib
from pathlib import Path

import trimesh

from app.core.config import CONVERTED_DIR


def resolve_converted_stl(file_url: str) -> Path:
    filename = Path(file_url).name  # nur der Dateiname, verwirft Host/Pfad
    path = CONVERTED_DIR / filename
    if not path.is_file():
        raise FileNotFoundError(f"STL-Datei nicht gefunden: {filename}")
    return path


# Grobheit der VHACD-Zerlegung. Benchmark (60 Artikel, 400 Steps):
#   konvexe Huelle 12.1s | 5 Teile 12.6s | 19 Teile (PyBullet-Defaults) 78.4s
# -> diese Parameter liefern ~5 Teile: formtreue Konkavitaet zu praktisch
#    denselben Step-Kosten wie eine einzelne konvexe Huelle.
VHACD_PARAMS = {
    "resolution": 300_000,
    "concavity": 0.0015,
    "gamma": 0.00075,
    "maxNumVerticesPerCH": 32,
    "minVolumePerCH": 0.0002,
}


def _vhacd_params_tag() -> str:
    """Kurzer Fingerprint der Parameter -> Cache wird bei Aenderung ungueltig."""
    raw = repr(sorted(VHACD_PARAMS.items())).encode()
    return hashlib.md5(raw).hexdigest()[:8]


def ensure_vhacd_collision_mesh(stl_path: str | Path) -> Path:
    """Erzeugt (einmalig) eine konvexe Zerlegung (VHACD) der STL für die Physik.

    PyBullet behandelt dynamische GEOM_MESH-Körper immer als konvexe Hülle --
    konkave Artikel (Vertiefungen, Löcher, L-Formen) kollidieren damit falsch.
    Erst die Zerlegung in konvexe Teile macht die Kollision formtreu.

    Das Ergebnis wird neben der STL gecacht (<name>.vhacd-<tag>.obj) und nur
    neu berechnet, wenn die STL neuer ist oder VHACD_PARAMS geändert wurden.
    """
    stl_path = Path(stl_path)
    tag = _vhacd_params_tag()
    obj_in = stl_path.with_suffix(".obj")
    obj_out = stl_path.with_name(f"{stl_path.stem}.vhacd-{tag}.obj")
    log_file = stl_path.with_name(f"{stl_path.stem}.vhacd-{tag}.log.txt")

    if obj_out.is_file() and obj_out.stat().st_mtime >= stl_path.stat().st_mtime:
        return obj_out

    # VHACD liest nur Wavefront OBJ -> STL einmal konvertieren
    mesh = trimesh.load(str(stl_path), force="mesh")
    mesh.export(str(obj_in))

    import pybullet as p

    client = p.connect(p.DIRECT)
    try:
        p.vhacd(str(obj_in), str(obj_out), str(log_file), **VHACD_PARAMS)
    finally:
        p.disconnect(client)

    if not obj_out.is_file():
        raise RuntimeError(f"VHACD-Zerlegung fehlgeschlagen für {stl_path.name}")

    return obj_out


# Berechnung des Volumens der konvexen Hülle des Meshes (wie im Frontend).
def compute_scaled_volume_mm3(stl_file: str | Path, scaled_length: float | None = None) -> float:
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
