'''Engine-unabhaengige Bausteine der Simulation.

Hier liegt alles, was nichts ueber die Physik-Engine weiss: die Konfiguration,
die Auswahl der besten Box und die Referenzboxen fuer die Dichteschaetzung.
Gerechnet wird in sim_mujoco.py.

Bis 07/2026 stand das zusammen mit der PyBullet-Engine in sim.py. Seit der
Umstellung auf MuJoCo gibt es nur noch eine Engine; die gemeinsamen Teile
stehen deshalb hier, statt aus einem Engine-Modul importiert zu werden.
'''

import math
from dataclasses import dataclass, field
from typing import List, Optional

from app.packing.models import Box, Item


@dataclass
class SimulationConfig:
    item: Item
    item_quantity: int
    boxes: List[Box] = field(default_factory=list)
    mesh_volume: float = 0.0
    stl_file: str = "ausgabe.stl"
    stability: str | None = None
    # VHACD-Zerlegung der STL, in Teilkoerper
    collision_file: Optional[str] = None

    item_mass: float = 0.01

    # Scale auf mm und Verwendung der skalierten x-Komponente
    mesh_scale: tuple[float, float, float] = (0.001, 0.001, 0.001)
    wall_thickness: float = 0.01

    # Performance / Genauigkeit
    fixed_time_step: float = 1 / 480
    solver_iterations: int = 30

    # max/min Steps gelten PRO Phase (Fall / Settling nach den Impulsen)
    max_simulation_steps: int = 1000
    min_simulation_steps: int = 100
    settle_check_interval: int = 60

    # Abbruchkriterium: Hoehe aendert sich weniger als das
    height_change_mm: float = 0.2

    # Sofortiger Abbruch, wenn die Fuellhoehe nach dem Einfuellen zu hoch ist
    early_validation_factor: float = 2

    # Verdichtung durch Ruetteln der Artikel
    settle_duration: float = 1
    settle_force_scale: float = 0.3
    settle_frequency: float = 10
    fit_height_tolerance: float = 0.02
    random_seed: Optional[int] = 42
    runs_per_box: int = 1

    # Graphische Anzeige zum Debugging
    use_gui: bool = False

    # Parallelisierung
    parallel_simulations: bool = True
    max_workers: Optional[int] = None

    # Stabile Box-Vorfilterung
    packing_density_fallback: float = 0.30
    packing_density_min: float = 0.12
    packing_density_max: float = 0.8
    prefilter_safety_factor: float = 1.5
    prefilter_fallback_candidates: int = 5

    # Wenn keine Box laut Simulation passt, trotzdem beste Alternative liefern
    return_best_invalid_if_no_valid: bool = True
    diagnostic_tolerance_mm: float = 1.0

    @property
    def box_x(self) -> float:
        return self.boxes[0].length / 1000

    @property
    def box_y(self) -> float:
        return self.boxes[0].width / 1000

    @property
    def box_z(self) -> float:
        return self.boxes[0].height / 1000


def _get_best_valid_results(
    simulation_results: list[dict],
    limit: int | None = None,
) -> list[dict]:
    valid_results = [
        result
        for result in simulation_results
        if result.get("fits_in_box", False)
    ]

    # Beste Box = hoechster Fuellgrad = kleinste Box, in die alle Artikel passen
    valid_results.sort(
        key=lambda result: result.get("fill_rate_percent", 0),
        reverse=True,
    )

    return valid_results if limit is None else valid_results[:limit]


def _get_single_article_volume_m3(config: SimulationConfig) -> float:
    if config.mesh_volume > 0:
        volume_scale = (
            config.mesh_scale[0]
            * config.mesh_scale[1]
            * config.mesh_scale[2]
        ) / 0.001**3
        return config.mesh_volume * volume_scale * 1e-9

    return (
        config.item.length / 1000
        * config.item.width / 1000
        * config.item.height / 1000
    )


def _build_dynamic_reference_boxes(config: SimulationConfig) -> list[Box]:
    """Drei Referenzboxen unterschiedlicher Grundflaeche, in denen die
    Schuettdichte des Artikels gemessen wird."""
    total_article_volume = (
        _get_single_article_volume_m3(config) * config.item_quantity
    )

    # konservative Annahme fuer lockere Schuettung
    estimated_bulk_volume = total_article_volume / 0.30

    boxes: list[Box] = []
    for name, length_m, width_m in (
        ("ref_small", 0.12, 0.08),
        ("ref_medium", 0.18, 0.12),
        ("ref_large", 0.28, 0.20),
    ):
        # Sicherheitsaufschlag und Begrenzung
        height_m = estimated_bulk_volume / (length_m * width_m) * 1.15
        height_m = max(0.12, min(height_m, 1.2))

        boxes.append(
            Box(
                name=name,
                length=math.ceil(length_m * 1000),
                width=math.ceil(width_m * 1000),
                height=math.ceil(height_m * 1000),
                lhm_capacity=1,
            )
        )

    return boxes
