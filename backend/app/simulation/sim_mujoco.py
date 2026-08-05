'''MuJoCo-Variante der Schuettgut-Simulation.

Bewusst minimal gehalten: Artikel fallen lassen, unter erhoehter Schwerkraft
ruetteln, ausruhen lassen, Oberkante messen. Mehr braucht es nicht -- die
Verdichtungsphase (COMPACTION_GRAVITY) erzeugt praktisch die gesamte Dichte.

Kalibrierung (28.07.2026) am Referenzfall 1754449 (100 Stk in 85x96x60,
real an der Kapazitaetsgrenze -> ~60 mm Fuellhoehe, ~46 % Dichte):
    ohne Verdichtung   155 mm / 18 % Dichte   (viel zu locker)
    Verdichtung  30 g   80 mm / 35 %
    Verdichtung  60 g   57 mm / 49 %
    Verdichtung 200 g   61 mm / 46 %          <- getroffen, +0,7 %
Alle vier Referenzfaelle liefern damit das richtige passt/passt-nicht-Urteil.

Config und Ergebnis-Keys sind identisch zu sim.py (PyBullet), die Szene wird
aber als MJCF-XML aufgebaut, weil MuJoCo ein Modell kompiliert statt Koerper
imperativ anzulegen.

Engine-bedingte Abweichungen zu sim.py:
- Reibung kombiniert MuJoCo per Maximum (PyBullet: Produkt) -> Boden und
  Waende bekommen denselben Wert wie die Artikel.
- Integrator implicitfast gegen die Spin-Instabilitaet kleiner Traegheiten.
- collision_margin entfaellt (MuJoCo kennt keinen Phantom-Margin).
- Daempfung sitzt am Free-Joint statt als linear/angularDamping.
'''

import math
import os
import random
import time
import zlib
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path

import mujoco
import numpy as np
import trimesh

from app.packing.models import Box
from app.simulation.common import (
    SimulationConfig,
    _build_dynamic_reference_boxes,
    _get_best_valid_results,
)

# Pendant zu lateralFriction / spinningFriction / rollingFriction in sim.py
object_friction = 0.2
spinning_friction = 0.01
rolling_friction = 0.01
joint_damping = 0.08

# Ersatz-Schwerkraft waehrend des Ruettelns; entspricht dem Aufstossen der
# Kiste beim Befuellen. Am Fall 1754449 kalibriert -- siehe Modul-Docstring.
pressing_gravity = -60.0


def _box_seed_offset(box: Box) -> int:
    """Seed-Versatz aus den Boxmassen statt aus der Position im Kandidatenfeld.

    Wird der Versatz aus dem Listenindex gebildet, haengt das Ergebnis einer
    Verpackung davon ab, welche ANDEREN Verpackungen im selben Lauf sind: ein
    anderer Stabilitaetsfilter oder ein erweiterter Katalog verschiebt die
    Position und damit die Schuettung. Die Abmessungen sind dagegen eine
    Eigenschaft der Verpackung selbst.

    crc32 statt hash(), weil hash() fuer str je Prozess randomisiert ist und
    damit ausgerechnet die Reproduzierbarkeit zerstoeren wuerde.
    """
    key = f"{box.length:.3f}x{box.width:.3f}x{box.height:.3f}".encode()
    return zlib.crc32(key) % 1_000_000


def run_single_box_simulation(args: tuple[SimulationConfig, Box, int]) -> dict:
    # box_index bleibt in der Signatur, weil executor.map 3-Tupel uebergibt;
    # fuer den Seed wird er bewusst nicht mehr verwendet.
    config, box, box_index = args

    n_runs = max(1, config.runs_per_box)
    runs: list[dict] = []

    #jede Simulation mit einem anderen, aber reproduzierbaren Random-Seed
    seed_offset = _box_seed_offset(box)
    for run_index in range(n_runs):
        random_seed = (
            None
            if config.random_seed is None
            else config.random_seed + seed_offset + run_index
        )

        single_box_config = replace(config, boxes=[box], random_seed=random_seed)
        runs.append(PackagingSimulation(single_box_config)._run_single())

    # Numerische Kennzahlen ueber die Laeufe mitteln
    result = {
        key: sum(run[key] for run in runs) / n_runs
        for key in runs[0]
        if key not in ("fits_in_box", "aborted")
    }

    mean_height = result["filling_height_mm"]
    heights = [run["filling_height_mm"] for run in runs]
    variance = sum((h - mean_height) ** 2 for h in heights) / n_runs

    result["fits_in_box"] = mean_height <= box.height * (1 + config.fit_height_tolerance)
    result["filling_height_std_mm"] = variance**0.5
    result["runs_per_box"] = n_runs
    result["aborted"] = any(run["aborted"] for run in runs)


    # BASIS-Seed des Laufs (ohne Box-Offset). Das GUI-Replay schickt ihn
    # unveraendert zurueck und diese Funktion addiert den maessebasierten
    # Offset erneut -> dadurch entsteht exakt der Seed von Lauf 0.
    result["random_seed"] = config.random_seed

    result["articles_per_lhm"] = config.item_quantity * box.lhm_capacity

    result["box"] = {
        "name": box.name,
        "length": box.length,
        "width": box.width,
        "height": box.height,
    }

    return result

def _reference_box_density(args: tuple[SimulationConfig, Box, int]) -> float | None:
    """Eine Referenzbox inkl. adaptiver Nachvergroesserung. Liefert die
    Packdichte oder None, wenn auch die groesste Variante nicht passt."""
    config, box, index = args
    current_box = box

    for attempt in range(4):
        single_config = replace(
            config,
            boxes=[current_box],
            runs_per_box=1,
            use_gui=False,
            parallel_simulations=False,
            random_seed=(
                None
                if config.random_seed is None
                else config.random_seed + 10_000 + index
            ),
        )

        result = run_single_box_simulation((single_config, current_box, index))

        if result["fits_in_box"]:
            return result["packing_density_percent"] / 100.0

        scale = 1.25
        current_box = Box(
            name=f"{box.name}_scaled_{attempt + 1}",
            length=math.ceil(current_box.length * scale),
            width=math.ceil(current_box.width * scale),
            height=math.ceil(current_box.height * scale),
            lhm_capacity=1,
        )

    return None


def estimate_bulk_packing_density(config: SimulationConfig) -> float:
    """Simuliert dynamisch abgeleitete Referenzboxen und liefert die
    geschaetzte Packdichte im Bereich [0, 1]."""
    reference_boxes = _build_dynamic_reference_boxes(config)
    args = [(config, box, index) for index, box in enumerate(reference_boxes)]

    with ProcessPoolExecutor(
        max_workers=min(len(args), os.cpu_count() or 1)
    ) as executor:
        densities = [
            density
            for density in executor.map(_reference_box_density, args)
            if density is not None
        ]

    return max(densities) if densities else 0.35


def _euler_to_quaternion_wxyz(roll: float, pitch: float, yaw: float) -> tuple:
    """XYZ-Euler zu Quaternion wie p.getQuaternionFromEuler, aber in
    MuJoCo-Reihenfolge (w, x, y, z)."""
    cr, sr = math.cos(roll / 2), math.sin(roll / 2)
    cp, sp = math.cos(pitch / 2), math.sin(pitch / 2)
    cy, sy = math.cos(yaw / 2), math.sin(yaw / 2)

    return (
        cr * cp * cy + sr * sp * sy,
        sr * cp * cy - cr * sp * sy,
        cr * sp * cy + sr * cp * sy,
        cr * cp * sy - sr * sp * cy,
    )


def _parse_obj_groups(obj_path: Path) -> list[np.ndarray]:
    """Zerlegt eine (VHACD-)OBJ in ihre Gruppen und liefert je Gruppe die
    Vertices. Noetig, weil MuJoCo eine mehrteilige OBJ sonst zu EINEM Mesh
    verschmilzt und damit die Konkavitaet wieder verliert."""
    vertices: list[list[float]] = []
    groups: list[list[int]] = []
    current: list[int] = []

    for line in obj_path.read_text().splitlines():
        if line.startswith("v "):
            vertices.append([float(v) for v in line.split()[1:4]])
        elif line.startswith(("g ", "o ")):
            if current:
                groups.append(current)
            current = []
        elif line.startswith("f "):
            for token in line.split()[1:]:
                current.append(int(token.split("/")[0]) - 1)
    if current:
        groups.append(current)

    vertex_array = np.array(vertices)
    if not groups:
        return [vertex_array]
    return [vertex_array[sorted(set(indices))] for indices in groups]


class PackagingSimulation:
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.item = config.item

        self.model: mujoco.MjModel | None = None
        self.data: mujoco.MjData | None = None
        self._viewer = None
        self._next_frame_time = 0.0
        self._aborted = False


        self.article_body_ids: list[int] = []
        # (geom_id, vertices) je Kollisionsteil, fuer die Fuellhoehe
        self._article_mesh_vertices: list[tuple[int, np.ndarray]] = []

        # Artikelmasse von mm auf m
        self.article_x = self.item.length / 1000
        self.article_y = self.item.width / 1000
        self.article_z = self.item.height / 1000

        self._aborted = False
        self._lid_pos: float | None = None

    def run(self) -> dict:
        boxes = self.config.boxes

        if not boxes:
            return {"results": []}

        simulation_args = [
            (self.config, box, index)
            for index, box in enumerate(boxes)
        ]

        # ACHTUNG: use_gui simuliert bewusst nur die ERSTE Box (Debug-Modus)
        if self.config.use_gui:
            simulation_results = [run_single_box_simulation(simulation_args[0])]
            return {"results": _get_best_valid_results(simulation_results)}

        if not self.config.parallel_simulations or len(boxes) == 1:
            simulation_results = [
                run_single_box_simulation(args)
                for args in simulation_args
            ]
            return {"results": _get_best_valid_results(simulation_results)}

        #Parallelisierung mit Max = CPU-Kerne oder Box-Anzahl
        max_workers = self.config.max_workers or min(
            len(boxes),
            os.cpu_count() or 1,
        )

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            simulation_results = list(
                executor.map(run_single_box_simulation, simulation_args)
            )

        return {"results": _get_best_valid_results(simulation_results)}

    def _run_single(self) -> dict:
        if self.config.random_seed is not None:
            random.seed(self.config.random_seed)

        try:
            self._build_model(self._plan_spawn_positions())
            self._simulate()

            if self._aborted:
                return {
                    "filling_height_m": 0.0,
                    "filling_height_mm": 0.0,
                    "relative_filling_height_percent": 0.0,
                    "total_article_volume_cm3": 0.0,
                    "used_box_volume_cm3": 0.0,
                    "packing_density_percent": 0.0,
                    "fits_in_box": False,
                    "fill_rate_percent": 0.0,
                    "aborted": True,
                }

            results = self._evaluate()

            results["aborted"] = self._aborted
            if self._aborted:
                results["fits_in_box"] = False

            if self.config.use_gui and not self._aborted:
                self._hold_gui_open()

            return results
        finally:
            self._close_viewer()
    #
    # Szenenaufbau (MJCF)
    #

    def _build_model(self, spawn_states: list[dict]) -> None:
        self.model = mujoco.MjModel.from_xml_string(
            self._build_scene(spawn_states)
        )
        self.data = mujoco.MjData(self.model)
        self._collect_article_handles()
        mujoco.mj_forward(self.model, self.data)


    def _count_escaped_articles(self) -> int:
        """Zaehlt Artikel, die die Verpackung seitlich oder nach unten verlassen haben.

        Bei hohen Aufprallgeschwindigkeiten kann ein Artikel eine Wand innerhalb
        eines Zeitschritts durchqueren, ohne dass ein Kontakt erkannt wird. Solche
        Laeufe liefern eine zu geringe Fuellhoehe und sind nicht belastbar.

        Gewertet wird der Schwerpunkt der Kollisionsteile: Einzelne herausragende
        Vertices sind normale Kontaktdurchdringung und kein Fehler. Ein Herausragen
        nach OBEN wird ebenfalls nicht gewertet -- das ist die Fuellhoehe.
        """
        cfg = self.config
        half_x, half_y = cfg.box_x / 2, cfg.box_y / 2
        floor_height = cfg.wall_thickness

        escaped_articles = 0

        for body_id in self.article_body_ids:
            geom_start = self.model.body_geomadr[body_id]
            geom_count = self.model.body_geomnum[body_id]

            weighted_sum = np.zeros(3)
            vertex_total = 0

            for geom_id in range(geom_start, geom_start + geom_count):
                if self.model.geom_contype[geom_id] == 0:
                    continue  # Visual-Geom zaehlt nicht
                mesh_id = self.model.geom_dataid[geom_id]
                start = self.model.mesh_vertadr[mesh_id]
                count = self.model.mesh_vertnum[mesh_id]
                vertices = self.model.mesh_vert[start:start + count]
                rotation = self.data.geom_xmat[geom_id].reshape(3, 3)

                centre = vertices.mean(axis=0) @ rotation.T + self.data.geom_xpos[geom_id]
                weighted_sum += centre * count
                vertex_total += count

            if vertex_total == 0:
                continue

            centre = weighted_sum / vertex_total
            if (
                not -half_x <= centre[0] <= half_x
                or not -half_y <= centre[1] <= half_y
                or centre[2] < floor_height
            ):
                escaped_articles += 1

        return escaped_articles

    def _plan_spawn_positions(self) -> list[dict]:
        """Wuerfelt Positionen und Rotationen VOR dem Modellbau aus.

        Verteiltes Raster ueber die gesamte Grundflaeche, volle Lagen stapeln
        nach oben. Reihenfolge der Zellen verwuerfelt, damit auch eine Teillage
        gleichmaessig verteilt liegt. Gleiche RNG-Reihenfolge wie sim.py ->
        gleicher Seed ergibt dieselbe Schuettung.
        """
        cfg = self.config
        print(f"Spawne {cfg.item_quantity} Artikel...")

        cols_x, cols_y, ux, uy = self._spawn_grid()
        per_layer = cols_x * cols_y
        step_x = 2 * ux / cols_x
        step_y = 2 * uy / cols_y

        cells = [(cx, cy) for cy in range(cols_y) for cx in range(cols_x)]
        random.shuffle(cells)

        states = []
        for i in range(cfg.item_quantity):
            layer = i // per_layer
            cx, cy = cells[i % per_layer]

            jitter_limit_x = max(0.0, (step_x - cx) / 2)
            jitter_limit_y = max(0.0, (step_y - cy) / 2)
            jitter_x = random.uniform(-jitter_limit_x, jitter_limit_x)
            jitter_y = random.uniform(-jitter_limit_y, jitter_limit_y)
            x_pos = max(-ux, min(ux, -ux + (cx + 0.5) * step_x + jitter_x))
            y_pos = max(-uy, min(uy, -uy + (cy + 0.5) * step_y + jitter_y))
            z_pos = cfg.box_z + 0.03 + layer * (self.article_z + 0.005)

            quat = _euler_to_quaternion_wxyz(
                random.uniform(-math.pi / 10, math.pi / 10),
                random.uniform(-math.pi / 10, math.pi / 10),
                random.uniform(-math.pi / 10, math.pi / 10),
            )
            states.append({"pos": (x_pos, y_pos, z_pos), "quat": quat})

        return states

    def _spawn_grid(self) -> tuple[int, int, float, float]:
        """Raster fuers Spawnen. Rand bleibt um die halbe Artikelgroesse frei,
        damit beim Spawnen nichts in der Wand steckt."""
        cfg = self.config
        gap = 0.005  # 5 mm Luft zwischen den Rasterzellen
        cell = max(self.article_x, self.article_y) + gap
        margin = 0.5 * max(self.article_x, self.article_y)

        ux = max(0.0, cfg.box_x / 2 - margin)
        uy = max(0.0, cfg.box_y / 2 - margin)
        cols_x = max(1, int((2 * ux) // cell))
        cols_y = max(1, int((2 * uy) // cell))
        return cols_x, cols_y, ux, uy

    def _get_wall_height(self) -> float:
        """Die Kollisionswaende muessen bis ueber den hoechsten Spawn reichen."""
        cfg = self.config
        cols_x, cols_y, _, _ = self._spawn_grid()
        per_layer = max(1, cols_x * cols_y)
        highest_layer = (cfg.item_quantity - 1) // per_layer
        highest_spawn_z = cfg.box_z + 0.03 + highest_layer * (self.article_z + 0.005)
        return highest_spawn_z + self.article_z + 0.05

    def _collision_part_vertices(self) -> list[np.ndarray]:
        cfg = self.config
        scale = np.array(cfg.mesh_scale)

        if cfg.vhacd_file:
            data = np.load(cfg.vhacd_file)
            parts = [data[k] for k in sorted(data.files)]
        else:
            mesh = trimesh.load(str(cfg.stl_file), force="mesh")
            parts = [np.asarray(mesh.convex_hull.vertices)]

        return [part * scale for part in parts]

    def _build_scene(self, spawn_states: list[dict]) -> str:
        cfg = self.config

        wall_height = max(cfg.box_z, self._get_wall_height())
        visual_height = cfg.box_z
        floor_height = cfg.wall_thickness
        wall_floor_overlap = 0.1
        wall_center_z = floor_height + wall_height / 2 - wall_floor_overlap
        visual_center_z = floor_height + visual_height / 2

        friction = (
            f'condim="6" '
            f'friction="{object_friction} {spinning_friction} {rolling_friction}"'
        )

        stl_path = str(Path(cfg.stl_file).resolve()).replace("\\", "/")

        part_vertices = self._collision_part_vertices()
        mass_per_part = cfg.item_mass / len(part_vertices)

        mesh_assets = "\n    ".join(
            f'<mesh name="part{index}" vertex="'
            + " ".join(f"{v:.6g}" for v in vertices.flatten())
            + '"/>'
            for index, vertices in enumerate(part_vertices)
        )

        collision_geoms = "\n        ".join(
            f'<geom type="mesh" mesh="part{index}" mass="{mass_per_part:.6g}" '
            f'{friction} group="3"/>'
            for index in range(len(part_vertices))
        )

        scale_str = " ".join(str(s) for s in cfg.mesh_scale)

        articles = "".join(
            f'''
      <body name="article_{i}" pos="{s["pos"][0]:.6g} {s["pos"][1]:.6g} {s["pos"][2]:.6g}"
            quat="{s["quat"][0]:.6g} {s["quat"][1]:.6g} {s["quat"][2]:.6g} {s["quat"][3]:.6g}">
        <joint type="free" damping="{joint_damping}"/>
        {collision_geoms}
        <geom type="mesh" mesh="visual" contype="0" conaffinity="0" mass="0" group="1" rgba="0.7 0.7 0.7 1"/>
      </body>'''
            for i, s in enumerate(spawn_states)
        )

        half_x = cfg.box_x / 2
        half_y = cfg.box_y / 2
        half_t = cfg.wall_thickness / 2
        walls = f'''
        
      <!-- Boden -->
      <geom type="box" size="{half_x+cfg.wall_thickness:.6g} {half_y+cfg.wall_thickness:.6g} {half_t:.6g}"
            pos="0 0 {half_t:.6g}" {friction} rgba="0.85 0.85 0.85 1"/>
      <geom type="box" size="{half_t:.6g} {half_y:.6g} {wall_height / 2:.6g}"
            pos="{half_x + half_t:.6g} 0 {wall_center_z:.6g}" {friction} rgba="0 0 0 0"/>
      <geom type="box" size="{half_t:.6g} {half_y:.6g} {wall_height / 2:.6g}"
            pos="{-half_x - half_t:.6g} 0 {wall_center_z:.6g}" {friction} rgba="0 0 0 0"/>
      <geom type="box" size="{half_x+cfg.wall_thickness:.6g} {half_t:.6g} {wall_height / 2:.6g}"
            pos="0 {half_y + half_t:.6g} {wall_center_z:.6g}" {friction} rgba="0 0 0 0"/>
      <geom type="box" size="{half_x+cfg.wall_thickness:.6g} {half_t:.6g} {wall_height / 2:.6g}"
            pos="0 {-half_y - half_t:.6g} {wall_center_z:.6g}" {friction} rgba="0 0 0 0"/>
      <geom type="box" size="{half_t:.6g} {half_y:.6g} {visual_height / 2:.6g}"
            pos="{half_x + half_t:.6g} 0 {visual_center_z:.6g}" contype="0" conaffinity="0" rgba="0.2 0.6 1.0 0.35"/>
      <geom type="box" size="{half_t:.6g} {half_y:.6g} {visual_height / 2:.6g}"
            pos="{-half_x - half_t:.6g} 0 {visual_center_z:.6g}" contype="0" conaffinity="0" rgba="0.2 0.6 1.0 0.35"/>
      <geom type="box" size="{half_x+cfg.wall_thickness:.6g} {half_t:.6g} {visual_height / 2:.6g}"
            pos="0 {half_y + half_t:.6g} {visual_center_z:.6g}" contype="0" conaffinity="0" rgba="0.2 0.6 1.0 0.35"/>
      <geom type="box" size="{half_x+cfg.wall_thickness:.6g} {half_t:.6g} {visual_height / 2:.6g}"
            pos="0 {-half_y - half_t:.6g} {visual_center_z:.6g}" contype="0" conaffinity="0" rgba="0.2 0.6 1.0 0.35"/>'''


        gap = 0.001
        lid = f'''
      <body name="lid" mocap="true" pos="0 0 {floor_height + wall_height + 0.1:.6g}">
        <geom name="lid_geom" type="box"
              size="{half_x - gap:.6g} {half_y - gap:.6g} {half_t:.6g}"
              {friction} rgba="0.9 0.55 0.2 0.45"/>
      </body>'''

        # Ohne <statistic> rahmt MuJoCo die Kamera anhand der hohen (aber
        # unsichtbaren) Hilfswaende -- die Box waere dann ein Fleck am Rand.
        camera_extent = max(cfg.box_x, cfg.box_y, cfg.box_z)

        return f'''
            <mujoco model="packing">
            <option timestep="{cfg.fixed_time_step:.8g}" gravity="0 0 -9.81"
                    iterations="{cfg.solver_iterations}" integrator="implicitfast"/>
            <compiler angle="radian"/>
            <statistic center="0 0 {cfg.box_z / 2:.6g}" extent="{camera_extent:.6g}"/>
            <visual>
                <global azimuth="135" elevation="-20"/>
            </visual>
            <asset>
                <mesh name="visual" file="{stl_path}" scale="{scale_str}"/>
                {mesh_assets}
            </asset>
            <worldbody>
                {walls}
                {lid}
                {articles}
            </worldbody>
            </mujoco>'''

    def _collect_article_handles(self) -> None:
        self.article_body_ids = []
        self._article_mesh_vertices = []

        for i in range(self.config.item_quantity):
            body_id = mujoco.mj_name2id(
                self.model, mujoco.mjtObj.mjOBJ_BODY, f"article_{i}"
            )
            self.article_body_ids.append(body_id)

            geom_start = self.model.body_geomadr[body_id]
            geom_count = self.model.body_geomnum[body_id]

            for geom_id in range(geom_start, geom_start + geom_count):
                if self.model.geom_contype[geom_id] == 0:
                    continue  # Visual-Geom zaehlt nicht zur Fuellhoehe
                mesh_id = self.model.geom_dataid[geom_id]
                vert_start = self.model.mesh_vertadr[mesh_id]
                vert_count = self.model.mesh_vertnum[mesh_id]
                vertices = self.model.mesh_vert[
                    vert_start:vert_start + vert_count
                ].copy()
                self._article_mesh_vertices.append((geom_id, vertices))

    #
    # Simulation: fallen -> verdichten -> ausruhen
    #

    def _step(self) -> None:
        if self._viewer is not None and not self._viewer.is_running():
            self._aborted = True
            return

        mujoco.mj_step(self.model, self.data)

        if not (self.config.use_gui and self._viewer is not None):
            return

        if not self._viewer.is_running():
            self._aborted = True
            return

        self._viewer.sync()

        self._next_frame_time += self.config.fixed_time_step
        remaining = self._next_frame_time - time.perf_counter()
        if remaining > 0:
            time.sleep(remaining)
        else:
            self._next_frame_time = time.perf_counter()

    def _simulate(self) -> None:
        cfg = self.config
        print("Simuliere physikalischen Fall...")

        if cfg.use_gui:
            from mujoco import viewer as mj_viewer
            self._viewer = mj_viewer.launch_passive(self.model, self.data)
            self._next_frame_time = time.perf_counter()

        self._step_until_settled()
        if self._aborted:
            return

        if not cfg.use_gui:
            filling_height = max(0.0, self._current_max_z() - cfg.wall_thickness)
            if filling_height > cfg.box_z * cfg.early_cancel_value:
                return

                # Deckel und Kennwerte einmal vorbereiten
        lid_body = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "lid")
        mocap_id = self.model.body_mocapid[lid_body]
        half_t = cfg.wall_thickness / 2
        box_height = cfg.wall_thickness + cfg.box_z + half_t

        # Phase 2: Deckel auflegen, dann verdichten.
        # Der Deckel sitzt auf Randhoehe -- steht die Schuettung hoeher, legt er
        # sich auf sie auf. So kann waehrend des Ruettelns nichts herausspringen.
        lid_z = max(box_height, self._current_max_z() + half_t + 0.0001)
        self.data.mocap_pos[mocap_id] = (0.0, 0.0, lid_z)

        self.model.opt.gravity[2] = pressing_gravity
        self._settle_items_with_impulse(
            duration=cfg.settle_duration,
            force_scale=cfg.settle_force_scale,
            frequency=cfg.settle_frequency,
        )
        if self._aborted:
            return

        self._step_until_settled()
        self.model.opt.gravity[2] = -9.81
        # Phase 3: Deckel senkt sich stoisch, bis er Widerstand findet
        lid_body = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "lid")
        mocap_id = self.model.body_mocapid[lid_body]
        half_t = cfg.wall_thickness / 2

        # Phase 3a: einmal bis auf Boxhoehe abstreifen. Die leicht ueberstehenden
        # Artikel werden dabei geruettelt und rutschen in Luecken, statt beim
        # spaeteren Absetzen nur zusammengedrueckt zu werden.
        lid_speed = 0.03     # m/s, Absetzen in Phase 3

        box_height = cfg.wall_thickness + cfg.box_z + half_t
        lid_z = self._current_max_z() + half_t + 0.0001

        if lid_z > box_height:
            self.data.mocap_pos[mocap_id] = (0.0, 0.0, lid_z)
            sweep_steps = int((lid_z - box_height) / (lid_speed * cfg.fixed_time_step))


            for _ in range(sweep_steps):
                lid_z -= lid_speed * cfg.fixed_time_step
                self.data.mocap_pos[mocap_id, 2] = lid_z
                self._step()
                if self._aborted:
                    break

            self._settle_items_with_impulse(
                duration=cfg.settle_duration,
                force_scale=0.1,
                frequency=cfg.settle_frequency,
            )
            self.data.mocap_pos[mocap_id, 2] = box_height + lid_speed*2  # Deckel wieder hoch

        lid_z = self._current_max_z() + half_t + 0.0001
        self.data.mocap_pos[mocap_id] = (0.0, 0.0, lid_z)

        for _ in range(cfg.max_simulation_steps):
            #speed
            lid_z -= 0.03 * cfg.fixed_time_step
            self.data.mocap_pos[mocap_id, 2] = lid_z
            self._step()
            if self._aborted:
                break

            # cfrc_ext wird nicht in jedem Fall von mj_step gefuellt
            mujoco.mj_rnePostConstraint(self.model, self.data)
            #end when force is too high
            if abs(self.data.cfrc_ext[lid_body, 5]) > 10.0:
                break

        self._lid_pos = lid_z - half_t


    def _current_max_z(self) -> float:
        """Oberkante der Schuettung ueber die transformierten Vertices aller
        Kollisionsteile."""
        max_z = 0.0
        for geom_id, vertices in self._article_mesh_vertices:
            rotation = self.data.geom_xmat[geom_id].reshape(3, 3)
            top = float(
                (vertices @ rotation[2, :]).max() + self.data.geom_xpos[geom_id][2]
            )
            max_z = max(max_z, top)
        return max_z

    def _step_until_settled(self) -> None:
        """Laeuft, bis sich nichts mehr nennenswert bewegt."""
        cfg = self.config

        for step in range(1, cfg.max_simulation_steps + 1):
            if self._aborted:
                return

            self._step()
            if self._aborted:
                return

            if step % 20 or step < cfg.min_simulation_steps:
                continue

            # Ruhe statt Hoehenkonstanz: billiger (ein numpy-Aufruf statt
            # einer Schleife ueber alle Geoms) und eindeutiger, weil ein
            # einzelner huepfender Artikel die Oberkante dominieren wuerde.
            if np.abs(self.data.qvel).max() < 0.2:
                break

    def _settle_items_with_impulse(
            self,
            duration: float,
            force_scale: float,
            frequency: float,
        ) -> None:
            """Verdichtet die Schuettung durch eine umlaufende Horizontalkraft.

            Die Kraft greift direkt an jedem Artikel an und bildet das Ruetteln der
            Verpackung ab, ohne den Behaelter selbst bewegen zu muessen. Waehrend
            dieser Phase liegt der Deckel auf, sodass keine Artikel herausspringen.
            """
            steps = max(1, int(duration / self.config.fixed_time_step))

            for step in range(steps):
                t = step * self.config.fixed_time_step
                force_x = force_scale * math.sin(2 * math.pi * frequency * t)
                force_y = force_scale * math.cos(2 * math.pi * frequency * t)

                self.data.xfrc_applied[:] = 0
                for body_id in self.article_body_ids:
                    self.data.xfrc_applied[body_id, 0] = force_x
                    self.data.xfrc_applied[body_id, 1] = force_y

                self._step()
                if self._aborted:
                    break

            self.data.xfrc_applied[:] = 0
    #
    # Auswertung (identisch zu sim.py)
    #

    def _evaluate(self) -> dict:
        cfg = self.config

        # Oberkante der Schuettung. Fuer die Kennzahlen zaehlt die Unterkante des
        # abgesetzten Deckels -- ausser die Simulation brach vorher ab.
        settled_height = self._current_max_z() - cfg.wall_thickness
        filling_height = (
            self._lid_pos - cfg.wall_thickness
            if self._lid_pos is not None
            else settled_height
        )

        if cfg.mesh_volume > 0:
        # mesh_volume ist bereits die skalierte Ist-Groesse (mm^3) -> nur Einheiten
            single_article_volume = cfg.mesh_volume * 1e-9
        else:
            single_article_volume = self.article_x * self.article_y * self.article_z

        total_article_volume = cfg.item_quantity * single_article_volume
        used_box_volume = cfg.box_x * cfg.box_y * settled_height
        box_volume = cfg.box_x * cfg.box_y * cfg.box_z

        # Packdichte = wie dicht die Schuettung IN SICH ist. NICHT durch das
        # Boxvolumen teilen -- estimate_bulk_packing_density baut darauf auf.
        packing_density = (
            total_article_volume / used_box_volume if used_box_volume > 0 else 0
        )

        # Auslastung der GESAMTEN Box (Ranking: hoch = wenig verschenkter Platz)
        box_utilization = total_article_volume / box_volume if box_volume > 0 else 0

        results = {
            "filling_height_mm": filling_height * 1000,
            "relative_filling_height_percent": filling_height / cfg.box_z * 100,
            "total_article_volume_cm3": total_article_volume * 1_000_000,
            "used_box_volume_cm3": used_box_volume * 1_000_000,
            "packing_density_percent": packing_density * 100,
            "fits_in_box": settled_height <= cfg.box_z * (1 + cfg.fit_height_tolerance),
            "fill_rate_percent": box_utilization * 100,
        }

        results["escaped_articles"] = self._count_escaped_articles()


        self._print_results(results)

        return results

    def _print_results(self, results: dict) -> None:
        print("\nErgebnisse")
        print(f"Box: {self.config.boxes[0].name}")
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
        print(
                    f"Artikel die Box verlassen"
                    f"{results['escaped_articles']:.2f} %"
                )

    #
    # GUI
    #

    def _hold_gui_open(self) -> None:
        print("\nGUI aktiv -- Fenster schliessen zum Beenden.")
        if self._viewer is None:
            return
        while self._viewer.is_running():
            mujoco.mj_step(self.model, self.data)
            self._viewer.sync()
            time.sleep(self.config.fixed_time_step)

    def _close_viewer(self) -> None:
        if self._viewer is not None:
            try:
                self._viewer.close()
            except Exception:
                pass  # Fenster wurde bereits manuell geschlossen
            self._viewer = None
