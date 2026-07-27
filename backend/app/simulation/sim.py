import pybullet as p
import pybullet_data
import random
import math
import time
from concurrent.futures import ProcessPoolExecutor
import os
from typing import List, Optional
from app.packing.models import Item, Box
from dataclasses import dataclass, field, replace
from statistics import median


@dataclass
class SimulationConfig:
    item: Item
    item_quantity: int
    boxes: List[Box] = field(default_factory=list)    
    mesh_volume: float = 0.0
    stl_file: str = "ausgabe.stl"
    stability: str | None = None
    # VHACD-Zerlegung der STL, in Teilkörper
    collision_file: Optional[str] = None


    item_mass: float = 0.01

    #Scale auf mm und verwendung der skallierten x komponente
    mesh_scale: tuple[float, float, float] = (0.001, 0.001, 0.001)
    wall_thickness: float = 0.1

    # Performance / Genauigkeit
    use_box_collision: bool = True
    fixed_time_step: float = 1 / 480
    solver_iterations: int = 80

    # max/min Steps gelten PRO Phase (Fall / Settling nach den Impulsen)
    max_simulation_steps: int = 1000
    min_simulation_steps: int = 100
    settle_check_interval: int = 30

    #Abbruchkriterium: Höhe ändert sich weniger als das
    height_change_mm: float = 0.2

    #Sofortiger Abbruch, wenn die Füllhöhe nach dem Einfüllen zu hoch ist
    early_validation_factor: float = 2

    # Verdichtung durch Rütteln der Artikel
    settle_duration: float = 1.2
    settle_force_scale: float = 0.8
    settle_frequency: float = 20
    collision_margin: float = 0.00002
    fit_height_tolerance: float = 0.015
    random_seed: Optional[int] = 42
    runs_per_box: int = 1

    #Graphische Anzeige zum Debugging
    use_gui: bool = False

    # Parallelisierung
    parallel_simulations: bool = True
    max_workers: Optional[int] = None

    # Stabile Box-Vorfilterung
    packing_density_fallback: float = 0.30
    packing_density_min: float = 0.12
    packing_density_max: float = 0.8
    prefilter_safety_factor: float = 1.25
    prefilter_fallback_candidates: int = 5

    # Wenn keine Box laut Simulation passt, trotzdem beste Alternative liefern
    return_best_invalid_if_no_valid: bool = True


    @property
    def box_x(self) -> float:
        return self.boxes[0].length / 1000
    @property
    def box_y(self) -> float:
        return self.boxes[0].width / 1000
    @property
    def box_z(self) -> float:
        return self.boxes[0].height / 1000

def run_single_box_simulation(args: tuple[SimulationConfig, Box, int]) -> dict:
        config, box, box_index = args

        n_runs = max(1, config.runs_per_box)
        runs: list[dict] = []

        #jede Simulation mit einem anderen Random-Seed, der aber gleich berechenbar ist (für Reproduzierbarkeit)
        for run_index in range(n_runs):
            random_seed = (
                None
                if config.random_seed is None
                else config.random_seed + box_index * 1000 + run_index
            )

            single_box_config = replace(
                config,
                boxes=[box],
                random_seed=random_seed,
            )

            simulation = PackagingSimulation(single_box_config)
            runs.append(simulation._run_single())

        # Numerische Kennzahlen ueber die Laeufe mitteln
        result = {
            key: sum(run[key] for run in runs) / n_runs
            for key in runs[0]
            if key != "fits_in_box"
        }

        mean_height = result["filling_height_mm"]
        heights = [run["filling_height_mm"] for run in runs]
        variance = sum((h - mean_height) ** 2 for h in heights) / n_runs

        result["fits_in_box"] = mean_height <= box.height * (
            1 + config.fit_height_tolerance
        )
        result["filling_height_std_mm"] = variance**0.5
        result["runs_per_box"] = n_runs

        # Effektiver Seed des ERSTEN Laufs (run_index=0). Erlaubt es, im GUI-Re-Run
        # exakt dieselbe Schuettung zu reproduzieren, die zu diesen Kennwerten gehoert.
        result["random_seed"] = (
            None
            if config.random_seed is None
            else config.random_seed + box_index * 1000
        )

        # Artikel pro Ladehilfsmittel: die komplette VPE-Menge passt in die
        # Box, also Menge x Boxen pro LHM (Spalte "Amount per bin box")
        result["articles_per_lhm"] = config.item_quantity * box.lhm_capacity

        result["box"] = {
            "name": box.name,
            "length": box.length,
            "width": box.width,
            "height": box.height,
            "lhm_capacity": box.lhm_capacity*config.item_quantity,
        }

        return result

# Valide = die Schuettung passt komplett in die Box (Fuellhoehe <= Boxhoehe).
def _get_best_valid_results(simulation_results: list[dict], limit: int | None = None) -> list[dict]:

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
        scale_x = config.mesh_scale[0] / 0.001
        scale_y = config.mesh_scale[1] / 0.001
        scale_z = config.mesh_scale[2] / 0.001
        volume_scale = scale_x * scale_y * scale_z
        return config.mesh_volume * volume_scale * 1e-9

    return (
        config.item.length / 1000
        * config.item.width / 1000
        * config.item.height / 1000
    )


def _build_dynamic_reference_boxes(config: SimulationConfig) -> list[Box]:
    single_article_volume = _get_single_article_volume_m3(config)
    total_article_volume = single_article_volume * config.item_quantity

    # konservative Annahme fuer lockere Schuettung
    assumed_density = 0.30
    estimated_bulk_volume = total_article_volume / assumed_density

    # drei unterschiedliche Grundflaechen-Layouts
    layouts = [
        ("ref_small", 0.12, 0.08),   # 120 x 80 mm
        ("ref_medium", 0.18, 0.12),  # 180 x 120 mm
        ("ref_large", 0.28, 0.20),   # 280 x 200 mm
    ]

    boxes: list[Box] = []

    for name, length_m, width_m in layouts:
        base_area = length_m * width_m
        height_m = estimated_bulk_volume / base_area

        # Sicherheitsaufschlag und Begrenzung
        height_m *= 1.15
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


def estimate_bulk_packing_density(config: SimulationConfig) -> float:
    """
    Simuliert dynamisch abgeleitete Referenzboxen und liefert die geschaetzte
    Packdichte als Median im Bereich [0, 1].
    """
    reference_boxes = _build_dynamic_reference_boxes(config)
    densities: list[float] = []

    for index, box in enumerate(reference_boxes):
        current_box = box

        # adaptive Nachvergroesserung, falls Referenzbox zu klein ist
        for attempt in range(4):
            single_config = replace(
                config,
                boxes=[current_box],
                runs_per_box=1,
                use_gui=False,
                parallel_simulations=False,
                random_seed=None if config.random_seed is None else config.random_seed + 10_000 + index,
            )

            result = run_single_box_simulation((single_config, current_box, index))

            if result["fits_in_box"]:
                densities.append(result["packing_density_percent"] / 100.0)
                break

            scale = 1.25
            current_box = Box(
                name=f"{box.name}_scaled_{attempt + 1}",
                length=math.ceil(current_box.length * scale),
                width=math.ceil(current_box.width * scale),
                height=math.ceil(current_box.height * scale),
                lhm_capacity=1,
            )

    if not densities:
        return 0.35

    return max(densities)
        
class PackagingSimulation:
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.item = config.item

        self.physics_client: int | None = None

        self.article_ids: list[int] = []
        self.collision_shape_id: int | None = None
        self.visual_shape_id: int | None = None


        # Artikelmaße von mm auf m
        self.article_x = self.item.length / 1000
        self.article_y = self.item.width / 1000
        self.article_z = self.item.height / 1000

    


    def run(self) -> dict:
        boxes = self.config.boxes

        if not boxes:
            return {"results": []}

        simulation_args = [
            (self.config, box, index)
            for index, box in enumerate(boxes)
        ]

        debug_single_run = self.config.use_gui

        if debug_single_run:
            simulation_results = [
                run_single_box_simulation(simulation_args[0])
            ]
            return {
                "results": _get_best_valid_results(simulation_results),
            }

        if not self.config.parallel_simulations or len(boxes) == 1:
            simulation_results = [
                run_single_box_simulation(args)
                for args in simulation_args
            ]

            return {
                "results": _get_best_valid_results(simulation_results),
            }

        #Parallelisierung der Simulationen mit Max=CPU-Kerne oder Box-Anzahl
        max_workers = self.config.max_workers or min(
            len(boxes),
            os.cpu_count() or 1,
        )

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            simulation_results = list(
                executor.map(
                    run_single_box_simulation,
                    simulation_args,
                )
            )

        return {
            "results": _get_best_valid_results(simulation_results),
        }

    def _run_single(self) -> dict:
        self.article_ids = []
        self.collision_shape_id = None
        self.visual_shape_id = None


        try:
            self._connect()
            self._create_box()
            self._create_article_shapes()
            self._spawn_articles()
            self._simulate()
            results = self._evaluate()

            if self.config.use_gui:
                self._hold_gui_open()

            return results
        finally:
            self._disconnect()

    #Für die Graphische ANzeige der SImulation
    def _hold_gui_open(self) -> None:
        print("\nGUI aktiv -- Fenster schliessen zum Beenden.")
        try:
            while p.isConnected(self.physics_client):
                p.stepSimulation()
                time.sleep(self.config.fixed_time_step)
        except p.error:
            pass  # Fenster wurde geschlossen


    def _connect(self) -> None:
        cfg = self.config

        mode = p.GUI if cfg.use_gui else p.DIRECT
        self.physics_client = p.connect(mode)

        if cfg.use_gui:
            # Seitenpanels ausblenden, Kamera auf die Box ausrichten
            p.configureDebugVisualizer(p.COV_ENABLE_GUI, 0)
            p.resetDebugVisualizerCamera(
                cameraDistance=2.5 * max(cfg.box_x, cfg.box_y, cfg.box_z),
                cameraYaw=45,
                cameraPitch=-30,
                cameraTargetPosition=[0, 0, cfg.box_z / 2],
            )

        p.setAdditionalSearchPath(pybullet_data.getDataPath())
        p.resetSimulation(physicsClientId=self.physics_client)

        p.setGravity(0, 0, -9.81, physicsClientId=self.physics_client)
        p.setTimeStep(
            self.config.fixed_time_step,
            physicsClientId=self.physics_client,
        )

        p.setPhysicsEngineParameter(
            fixedTimeStep=self.config.fixed_time_step,#Berechnungsintervall der SImulation
            numSolverIterations=self.config.solver_iterations,#Wie oft Kräfte berechnen
            deterministicOverlappingPairs=1,#Berechnungsreihenfolge der Kollisionen immer identisch
            enableConeFriction=1,#komplexere Reibung
            contactBreakingThreshold=0.001,#kein Kontakt, wenn die Distanz > 1mm
            physicsClientId=self.physics_client,
        )

        if self.config.random_seed is not None:
            random.seed(self.config.random_seed)

    def _disconnect(self) -> None:
        if self.physics_client is not None:
            # Beim manuellen Schliessen des GUI-Fensters ist der Physik-Server
            # bereits getrennt -> p.disconnect wuerde sonst p.error werfen.
            try:
                if p.isConnected(self.physics_client):
                    p.disconnect(self.physics_client)
            except p.error:
                pass
            self.physics_client = None



    def _create_box(self) -> None:
        cfg = self.config
        wall_height = max(cfg.box_z, self._get_spawn_wall_height())
        visual_height = cfg.box_z

        # Die uebergebenen Boxmasse sind INNENMASSE. Der Boden ist wall_thickness
        # dick, daher sitzen die Waende auf dem Boden auf (Start bei floor_top).
        # So betraegt die nutzbare Innenhoehe UEBER dem Boden exakt box_z; die
        # Fuellhoehen-Bewertung (max_z - wall_thickness) bleibt konsistent.
        floor_top = cfg.wall_thickness
        wall_center_z = floor_top + wall_height / 2
        visual_center_z = floor_top + visual_height / 2

        # Boden
        floor_collision_shape = p.createCollisionShape(
            p.GEOM_BOX,
            halfExtents=[cfg.box_x, cfg.box_y, cfg.wall_thickness / 2],
        )
        floor_visual_shape = p.createVisualShape(
            p.GEOM_BOX,
            halfExtents=[cfg.box_x / 2, cfg.box_y / 2, cfg.wall_thickness / 2],
            rgbaColor=[0.85, 0.85, 0.85, 1.0],
        )

        p.createMultiBody(
            baseMass=0,
            baseCollisionShapeIndex=floor_collision_shape,
            baseVisualShapeIndex=floor_visual_shape,
            basePosition=[0, 0, cfg.wall_thickness / 2],
        )

        # Unsichtbare Visual-Shape (Alpha 0) fuer die hohen Hilfswaende:
        # verhindert, dass PyBullet im GUI die hohe Kollisionsgeometrie rendert
        # (ein Koerper ohne Visual-Shape wird sonst als Kollisionsform gezeichnet).
        hidden_wall_x = p.createVisualShape(
            p.GEOM_BOX,
            halfExtents=[cfg.wall_thickness / 2, cfg.box_y / 2, wall_height / 2],
            rgbaColor=[0, 0, 0, 0],
        )
        hidden_wall_y = p.createVisualShape(
            p.GEOM_BOX,
            halfExtents=[cfg.box_x / 2, cfg.wall_thickness / 2, wall_height / 2],
            rgbaColor=[0, 0, 0, 0],
        )

        # Wände X-Richtung:
        # Kollision = hohe Hilfswand (unsichtbar), Visual = echte Boxhöhe (blau)
        wall_collision_x = p.createCollisionShape(
            p.GEOM_BOX,
            halfExtents=[cfg.wall_thickness / 2, cfg.box_y / 2, wall_height / 2],
        )
        wall_visual_x = p.createVisualShape(
            p.GEOM_BOX,
            halfExtents=[cfg.wall_thickness / 2, cfg.box_y / 2, visual_height / 2],
            rgbaColor=[0.2, 0.6, 1.0, 0.35],
        )

        p.createMultiBody(
            baseMass=0,
            baseCollisionShapeIndex=wall_collision_x,
            baseVisualShapeIndex=hidden_wall_x,
            basePosition=[cfg.box_x / 2 + cfg.wall_thickness / 2, 0, wall_center_z],
        )
        p.createMultiBody(
            baseMass=0,
            baseVisualShapeIndex=wall_visual_x,
            basePosition=[cfg.box_x / 2 + cfg.wall_thickness / 2, 0, visual_center_z],
        )

        p.createMultiBody(
            baseMass=0,
            baseCollisionShapeIndex=wall_collision_x,
            baseVisualShapeIndex=hidden_wall_x,
            basePosition=[-cfg.box_x / 2 - cfg.wall_thickness / 2, 0, wall_center_z],
        )
        p.createMultiBody(
            baseMass=0,
            baseVisualShapeIndex=wall_visual_x,
            basePosition=[-cfg.box_x / 2 - cfg.wall_thickness / 2, 0, visual_center_z],
        )

        # Wände Y-Richtung:
        # Kollision = hohe Hilfswand (unsichtbar), Visual = echte Boxhöhe (blau)
        wall_collision_y = p.createCollisionShape(
            p.GEOM_BOX,
            halfExtents=[cfg.box_x / 2, cfg.wall_thickness / 2, wall_height / 2],
        )
        wall_visual_y = p.createVisualShape(
            p.GEOM_BOX,
            halfExtents=[cfg.box_x / 2, cfg.wall_thickness / 2, visual_height / 2],
            rgbaColor=[0.2, 0.6, 1.0, 0.35],
        )

        p.createMultiBody(
            baseMass=0,
            baseCollisionShapeIndex=wall_collision_y,
            baseVisualShapeIndex=hidden_wall_y,
            basePosition=[0, cfg.box_y / 2 + cfg.wall_thickness / 2, wall_center_z],
        )
        p.createMultiBody(
            baseMass=0,
            baseVisualShapeIndex=wall_visual_y,
            basePosition=[0, cfg.box_y / 2 + cfg.wall_thickness / 2, visual_center_z],
        )

        p.createMultiBody(
            baseMass=0,
            baseCollisionShapeIndex=wall_collision_y,
            baseVisualShapeIndex=hidden_wall_y,
            basePosition=[0, -cfg.box_y / 2 - cfg.wall_thickness / 2, wall_center_z],
        )
        p.createMultiBody(
            baseMass=0,
            baseVisualShapeIndex=wall_visual_y,
            basePosition=[0, -cfg.box_y / 2 - cfg.wall_thickness / 2, visual_center_z],
        )

    def _spawn_grid(self) -> tuple[int, int, float, float]:
        """Raster fuer verteiltes Spawnen ueber die GESAMTE Grundflaeche.

        Der Rand wird um die halbe Artikelgroesse freigehalten, damit die
        Artikel beim Spawnen nicht in die (Kollisions-)Wand ragen.
        Rueckgabe: (cols_x, cols_y, ux, uy) mit ux/uy = nutzbare halbe Ausdehnung.
        """
        cfg = self.config
        gap = 0.005  # 5 mm Luft zwischen den Rasterzellen
        cell = max(self.article_x, self.article_y) + gap
        margin = 0.5 * max(self.article_x, self.article_y)

        ux = max(cell / 2, cfg.box_x / 2 - margin)
        uy = max(cell / 2, cfg.box_y / 2 - margin)
        cols_x = max(1, int((2 * ux) // cell))
        cols_y = max(1, int((2 * uy) // cell))
        return cols_x, cols_y, ux, uy

    def _get_spawn_wall_height(self) -> float:
        cfg = self.config

        cols_x, cols_y, _, _ = self._spawn_grid()
        per_layer = max(1, cols_x * cols_y)
        highest_layer = (cfg.item_quantity - 1) // per_layer
        highest_spawn_z = cfg.box_z + 0.03 + highest_layer * (self.article_z + 0.01)

        return highest_spawn_z + self.article_z + 0.05

    def _create_article_shapes(self) -> None:
        cfg = self.config

        mesh_file = cfg.collision_file
        print(f"Kollisionsmesh: {mesh_file}")
        print(f"Visualmesh:     {cfg.stl_file}")
        print(f"mesh_scale:     {cfg.mesh_scale}")

        self.collision_shape_id = p.createCollisionShape(
            p.GEOM_MESH,
            fileName=mesh_file,
            meshScale=cfg.mesh_scale,
        )

        self.visual_shape_id = p.createVisualShape(
            p.GEOM_MESH,
            fileName=cfg.stl_file,
            meshScale=cfg.mesh_scale,
            rgbaColor=[0.7, 0.7, 0.7, 1.0],)


    def _spawn_articles(self) -> None:
        cfg = self.config

        print(f"Spawne {cfg.item_quantity} Artikel...")

        # Verteiltes Spawnen ueber die gesamte Grundflaeche (verwuerfeltes Raster):
        # jede Rasterzelle bekommt einen Artikel, volle Lagen stapeln nach oben.
        # Vermeidet den zentralen "Huegel" und die Kollisions-Explosion tief
        # gestapelter Saeulen, bleibt aber innerhalb der Kollisionswaende.
        cols_x, cols_y, ux, uy = self._spawn_grid()
        per_layer = cols_x * cols_y
        step_x = 2 * ux / cols_x
        step_y = 2 * uy / cols_y

        # Zellreihenfolge verwuerfeln, damit auch eine TEIL-Lage (weniger Artikel
        # als Zellen) gleichmaessig ueber die ganze Flaeche verteilt wird statt
        # zeilenweise in einer Ecke. Nutzt den geseedeten RNG -> reproduzierbar.
        cells = [(cx, cy) for cy in range(cols_y) for cx in range(cols_x)]
        random.shuffle(cells)

        for i in range(cfg.item_quantity):
            layer = i // per_layer
            cx, cy = cells[i % per_layer]

            # Zellmittelpunkt + kleiner Jitter, geklemmt auf die nutzbare Flaeche
            jitter_x = random.uniform(-0.25 * step_x, 0.25 * step_x)
            jitter_y = random.uniform(-0.25 * step_y, 0.25 * step_y)
            x_pos = max(-ux, min(ux, -ux + (cx + 0.5) * step_x + jitter_x))
            y_pos = max(-uy, min(uy, -uy + (cy + 0.5) * step_y + jitter_y))

            z_pos = cfg.box_z + 0.03 + layer * (self.article_z + 0.01)

            random_orientation = p.getQuaternionFromEuler(
                [
                    random.uniform(-math.pi/10, math.pi/10),
                    random.uniform(-math.pi/10, math.pi/10),
                    random.uniform(-math.pi/10, math.pi/10),
                ]
            )

            body_id = p.createMultiBody(
                baseMass=cfg.item_mass,
                baseCollisionShapeIndex=self.collision_shape_id,
                baseVisualShapeIndex=self.visual_shape_id,
                basePosition=[x_pos, y_pos, z_pos],
                baseOrientation=random_orientation,
            )

            #Materialeigenschaften: Reibung, Luftwiederstand,...
            p.changeDynamics(
                body_id,
                -1,
                lateralFriction=0.005,
                spinningFriction=0.0005,
                rollingFriction=0.0005,
                linearDamping=0.04,
                angularDamping=0.04,
                restitution=0.0,
                collisionMargin=cfg.collision_margin,
            )

            self.article_ids.append(body_id)

    def _step(self) -> None:
        p.stepSimulation()
        # Im GUI-Modus auf Echtzeit bremsen, sonst ist nichts zu sehen
        if self.config.use_gui:
            time.sleep(self.config.fixed_time_step)

    def _simulate(self) -> None:
        cfg = self.config
        print("Simuliere physikalischen Fall...")

        # Phase 1: freier Fall, bis alle Artikel zur Ruhe gekommen sind
        self._step_until_settled()

        # Abbruch bei zu hoher Füllhöhe, nach dem Fall
        filling_height = self._current_max_z() - cfg.wall_thickness
        if filling_height > cfg.box_z * cfg.early_validation_factor:
            return

        p.setGravity(0, 0, -120)

        self._settle_items_with_impulse(
            duration=cfg.settle_duration,
            force_scale=cfg.settle_force_scale,
            frequency=cfg.settle_frequency,
        )

        # Phase 2: nach den Verdichtungs-Impulsen erneut ausruhen lassen
        self._step_until_settled()

        p.setGravity(0, 0, -9.81)

    #Füllhöhe bestimmen 
    def _current_max_z(self) -> float:
        """Oberkante der Schuettung ueber die AABBs aller Artikel."""
        max_z = 0.0
        for article_id in self.article_ids:
            _, aabb_max = p.getAABB(article_id)
            max_z = max(max_z, aabb_max[2])
        return max_z

    #Simulation läuft, bis die Füllhöhe sich nicht mehr signifikant ändert
    def _step_until_settled(self) -> None:
        cfg = self.config
        last_height: float | None = None

        for step in range(1, cfg.max_simulation_steps + 1):
            self._step()

            if step % cfg.settle_check_interval != 0:
                continue

            height = self._current_max_z()
            height_converged = (
                last_height is not None
                and abs(height - last_height) < cfg.height_change_mm / 1000
            )
            last_height = height

            if step >= cfg.min_simulation_steps and height_converged:
                break

    def _settle_items_with_impulse(
        self,
        duration: float,
        force_scale: float,
        frequency: float,
    ) -> None:
        steps = max(1, int(duration * 240))

        for step in range(steps):
            force_direction = math.sin(step * frequency)

            for article_id in self.article_ids:
                p.applyExternalForce(
                    objectUniqueId=article_id,
                    linkIndex=-1,
                    forceObj=[
                        force_scale * force_direction,
                        force_scale * random.uniform(-1, 1),
                        0,
                    ],
                    posObj=[0, 0, 0],
                    flags=p.WORLD_FRAME,
                )

            self._step()

    def _evaluate(self) -> dict:
        cfg = self.config

        # Tatsaechliche Oberkante ueber die AABB: gilt auch fuer gekippte/
        # rotierte Artikel (Position + halbe Hoehe stimmt nur aufrecht).
        filling_height = self._current_max_z() - cfg.wall_thickness

        # Echtes Mesh-Volumen (mm^3 -> m^3) statt Bounding-Box-Quader;
        # Fallback auf den Quader, falls kein Mesh-Volumen berechnet wurde.
        if cfg.mesh_volume > 0:
            scale_x = cfg.mesh_scale[0] / 0.001
            scale_y = cfg.mesh_scale[1] / 0.001
            scale_z = cfg.mesh_scale[2] / 0.001
            volume_scale = scale_x * scale_y * scale_z
            single_article_volume = cfg.mesh_volume * volume_scale * 1e-9
        else:
            single_article_volume = self.article_x * self.article_y * self.article_z


        total_article_volume = cfg.item_quantity * single_article_volume
        used_box_volume = cfg.box_x * cfg.box_y * filling_height
        box_volume = cfg.box_x * cfg.box_y * cfg.box_z

        # Packdichte = wie dicht die Schuettung IN SICH ist -> Artikelvolumen
        # geteilt durch das bis zur Fuellhoehe tatsaechlich beanspruchte Volumen.
        # WICHTIG: nicht durch box_volume teilen -- estimate_bulk_packing_density
        # nutzt diesen Wert fuer den Box-Vorfilter (Referenzboxen sind 500 mm hoch).
        packing_density = (
            total_article_volume / used_box_volume
            if used_box_volume > 0
            else 0
        )

        # Valide = Schuettung liegt (bis auf die Deckel-Toleranz) in der Box
        fits_in_box = filling_height <= cfg.box_z * (1 + cfg.fit_height_tolerance)

        # Auslastung der GESAMTEN Box (Ranking: hoch = wenig verschenkter Platz)
        box_utilization = (
            total_article_volume / box_volume if box_volume > 0 else 0
        )

        results = {
            "filling_height_m": filling_height,
            "filling_height_mm": filling_height * 1000,
            "relative_filling_height_percent": filling_height / cfg.box_z * 100,
            "total_article_volume_cm3": total_article_volume * 1_000_000,
            "used_box_volume_cm3": used_box_volume * 1_000_000,
            "packing_density_percent": packing_density * 100,
            "fits_in_box": fits_in_box,
            "fill_rate_percent": box_utilization * 100,
        }

        self._print_results(results)

        return results

    def _print_results(self, results: dict) -> None:
        print("\nErgebnisse")
        print(f"Füllhöhe in der Kiste: {results['filling_height_mm']:.2f} mm")
        print(
            f"Relative Füllhöhe der Kiste: "
            f"{results['relative_filling_height_percent']:.2f} %"
        )
        print(
            f"Theoretisches Artikelvolumen gesamt: "
            f"{results['total_article_volume_cm3']:.2f} cm^3"
        )
        print(
            f"Beanspruchtes Box-Volumen: "
            f"{results['used_box_volume_cm3']:.2f} cm^3"
        )
        print(
            f"Erreichte Fülldichte: "
            f"{results['packing_density_percent']:.2f} %"
        )



