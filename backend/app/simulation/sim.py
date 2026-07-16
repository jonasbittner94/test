import pybullet as p
import pybullet_data
import random
import math
from concurrent.futures import ProcessPoolExecutor
import os
from typing import List, Optional, Dict
from app.packing.models import Item, Box
from dataclasses import dataclass, replace

@dataclass
class SimulationConfig:
    item: Item
    item_quantity: int
    boxes: List[Box]

    stl_file: str = "ausgabe.stl"
    item_mass: float = 0.006

    mesh_scale: tuple[float, float, float] = (0.001, 0.001, 0.001)
    
    wall_thickness: float = 0.005

    # Performance / Genauigkeit
    use_box_collision: bool = True
    fixed_time_step: float = 1 / 240
    solver_iterations: int = 80
    max_simulation_steps: int = 1200
    min_simulation_steps: int = 120
    settle_check_interval: int = 20
    linear_sleep_threshold: float = 0.015
    angular_sleep_threshold: float = 0.15
    random_seed: Optional[int] = 42
    verbose: bool = False

    # Parallelisierung
    parallel_simulations: bool = True
    max_workers: Optional[int] = None
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

        random_seed = (
            None
            if config.random_seed is None
            else config.random_seed + box_index
        )

        single_box_config = replace(
            config,
            boxes=[box],
            random_seed=random_seed,
        )

        simulation = PackagingSimulation(single_box_config)
        result = simulation._run_single()

        result["box"] = {
            "name": box.name,
            "length": box.length,
            "width": box.width,
            "height": box.height,
            "capacityLHM": box.capacityLHM,
        }

        return result

def _get_best_valid_results(simulation_results: list[dict], limit: int = 5) -> list[dict]:
    valid_results = [
        result
        for result in simulation_results
        if result.get("packing_density_percent", 0) <= 100
    ]

    valid_results.sort(
        key=lambda result: result.get("packing_density_percent", 0),
        reverse=True,
    )

    return valid_results[:limit]





class PackagingSimulation:
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.item = config.item

        self.physics_client: int | None = None

        self.article_ids: list[int] = []
        self.collision_shape_id: int | None = None

        # Artikelmaße von mm auf m
        self.article_x = self.item.length / 1000
        self.article_y = self.item.width / 1000
        self.article_z = self.item.height / 1000

    

    def run(self) -> dict:
        boxes = self.config.boxes

        if not boxes:
            return {"results": []}

        if self.config.verbose:
            print("Anzahl Boxen:", len(boxes))
            print("Boxnamen:", [box.name for box in boxes])

        simulation_args = [
            (self.config, box, index)
            for index, box in enumerate(boxes)
        ]

        if not self.config.parallel_simulations or len(boxes) == 1:
            simulation_results = [
                run_single_box_simulation(args)
                for args in simulation_args
            ]

            return {
                "results": simulation_results,
            }

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
            "results": _get_best_valid_results(simulation_results, limit=5),
        }

    def _run_single(self) -> dict:
        self.article_ids = []
        self.collision_shape_id = None

        try:
            self._connect()
            self._create_box()
            self._create_article_shapes()
            self._spawn_articles()
            self._simulate()
            results = self._evaluate()

            return results
        finally:
            self._disconnect()





    def _connect(self) -> None:
        self.physics_client = p.connect(p.DIRECT)

        p.setAdditionalSearchPath(pybullet_data.getDataPath())
        p.resetSimulation(physicsClientId=self.physics_client)

        p.setGravity(0, 0, -9.81, physicsClientId=self.physics_client)
        p.setTimeStep(
            self.config.fixed_time_step,
            physicsClientId=self.physics_client,
        )

        p.setPhysicsEngineParameter(
            fixedTimeStep=self.config.fixed_time_step,
            numSolverIterations=self.config.solver_iterations,
            deterministicOverlappingPairs=1,
            enableConeFriction=1,
            contactBreakingThreshold=0.001,
            physicsClientId=self.physics_client,
        )

        if self.config.random_seed is not None:
            random.seed(self.config.random_seed)

    def _disconnect(self) -> None:
        if self.physics_client is not None:
            p.disconnect(self.physics_client)
            self.physics_client = None



    def _create_box(self) -> None:
        cfg = self.config

        # Boden
        collision_shape = p.createCollisionShape(
            p.GEOM_BOX,
            halfExtents=[cfg.box_x / 2, cfg.box_y / 2, cfg.wall_thickness / 2],
        )

        p.createMultiBody(
            baseMass=0,
            baseCollisionShapeIndex=collision_shape,
            basePosition=[0, 0, cfg.wall_thickness / 2],
        )

        # Wände X-Richtung

        wall_collision_x = p.createCollisionShape(
            p.GEOM_BOX,
            halfExtents=[cfg.wall_thickness / 2, cfg.box_y / 2, cfg.box_z],
        )

        p.createMultiBody(
            baseMass=0,
            baseCollisionShapeIndex=wall_collision_x,
            basePosition=[cfg.box_x / 2 + cfg.wall_thickness / 2, 0, cfg.box_z],
        )
        p.createMultiBody(
            baseMass=0,
            baseCollisionShapeIndex=wall_collision_x,
            basePosition=[-cfg.box_x / 2 - cfg.wall_thickness / 2, 0, cfg.box_z],
        )

        # Wände Y-Richtung

        
        wall_collision_y = p.createCollisionShape(
            p.GEOM_BOX,
            halfExtents=[cfg.box_x / 2, cfg.wall_thickness / 2, cfg.box_z],
        )

        p.createMultiBody(
            baseMass=0,
            baseCollisionShapeIndex=wall_collision_y,
            basePosition=[0, cfg.box_y / 2 + cfg.wall_thickness / 2, cfg.box_z],
        )
        p.createMultiBody(
            baseMass=0,
            baseCollisionShapeIndex=wall_collision_y,
            basePosition=[0, -cfg.box_y / 2 - cfg.wall_thickness / 2, cfg.box_z],
        )

    def _create_article_shapes(self) -> None:
        cfg = self.config

        self.collision_shape_id = p.createCollisionShape(
            p.GEOM_MESH,
            fileName=cfg.stl_file,
            meshScale=cfg.mesh_scale,
        )


    def _spawn_articles(self) -> None:
        cfg = self.config

        print(f"Spawne {cfg.item_quantity} Artikel...")

        for i in range(cfg.item_quantity):
            x_pos = random.uniform(-cfg.box_x / 4, cfg.box_x / 4)
            y_pos = random.uniform(-cfg.box_y / 4, cfg.box_y / 4)

            layer = i % 10
            stack = i // 10
            z_pos = cfg.box_z + 0.02 + layer * (self.article_z + 0.002) + stack * 0.002

            random_orientation = p.getQuaternionFromEuler(
                [
                    random.uniform(-0.5, 0.5),
                    random.uniform(-0.5, 0.5),
                    random.uniform(0, 2 * math.pi),
                ]
            )

            body_id = p.createMultiBody(
                baseMass=cfg.item_mass,
                baseCollisionShapeIndex=self.collision_shape_id,
                basePosition=[x_pos, y_pos, z_pos],
                baseOrientation=random_orientation,
            )

            p.changeDynamics(
                body_id,
                -1,
                lateralFriction=0.2,
                spinningFriction=0.0005,
                rollingFriction=0.0005,
                linearDamping=0.0,
                angularDamping=0.0,
                restitution=0.0,
            )

            self.article_ids.append(body_id)

    def _simulate(self) -> None:
        print("Simuliere physikalischen Fall...")

        for _ in range(200):
            p.stepSimulation()

        p.setGravity(0, 0, -50)

        self._settle_items_with_impulse(
            duration=0.02,
            force_scale=0.04,
            frequency=10.0,
        )

        for _ in range(200):
            p.stepSimulation()

        p.setGravity(0, 0, -9.81)

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

            p.stepSimulation()

    def _evaluate(self) -> dict:
        cfg = self.config

        max_z = 0

        for article_id in self.article_ids:
            position, _ = p.getBasePositionAndOrientation(article_id)
            top_edge = position[2] + self.article_z / 2
            max_z = max(max_z, top_edge)

        filling_height = max_z - cfg.wall_thickness

        single_article_volume = self.article_x * self.article_y * self.article_z
        total_article_volume = cfg.item_quantity * single_article_volume
        used_box_volume = cfg.box_x * cfg.box_y * filling_height

        packing_density = (
            total_article_volume / used_box_volume
            if used_box_volume > 0
            else 0
        )

        results = {
            "filling_height_m": filling_height,
            "filling_height_mm": filling_height * 1000,
            "relative_filling_height_percent": filling_height / cfg.box_z * 100,
            "total_article_volume_cm3": total_article_volume * 1_000_000,
            "used_box_volume_cm3": used_box_volume * 1_000_000,
            "packing_density_percent": packing_density * 100,
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
            f"Erreichte Packdichte: "
            f"{results['packing_density_percent']:.2f} %"
        )



