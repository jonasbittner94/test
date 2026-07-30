'''Aufrufen der Simulation durch die API.'''

from fastapi import APIRouter, HTTPException
import traceback
from pydantic import BaseModel
from app.simulation.common import SimulationConfig
from app.simulation.sim_mujoco import (
    PackagingSimulation,
    estimate_bulk_packing_density,
)
from app.packing.models import Box
from app.packing.box_loader import load_boxes_from_csv
from app.packing.lhm import get_lhm_capacity
from app.core.config import BOXES_CSV
from dataclasses import replace
from app.geometry import (
    compute_scaled_volume_mm3,
    ensure_vhacd_collision_mesh,
    resolve_converted_stl,
)
class RequestedBox(BaseModel):
    name: str
    length: int
    width: int
    height: int
    lhm_capacity: int | None = None

class SingleBoxSimulationRequest(BaseModel):
    config: SimulationConfig
    box_name: str
    estimated_density: float | None = None
    box: RequestedBox
    # Effektiver Seed des urspruenglichen Laufs -> exakte Reproduktion im GUI.
    random_seed: int | None = None


router = APIRouter(
    prefix="/simulation",
    tags=["simulation"],
)


@router.post("/run")
def run_simulation(config: SimulationConfig):

    try:
        stl_path = resolve_converted_stl(config.stl_file)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))

    # config.item.length ist bereits die (ggf. skalierte) Ziel-Länge -> entspricht
    # scaled_length im Frontend; damit skaliert compute_scaled_volume_mm3 das Volumen.
    mesh_volume = compute_scaled_volume_mm3(stl_path, config.item.length)
    # Konvexe Zerlegung fuer formtreue Kollision (gecacht, einmalig pro STL).
    collision_path = ensure_vhacd_collision_mesh(stl_path)
    stability = config.stability

    reference_config = replace(
        config,
        mesh_volume=mesh_volume,
        stl_file=str(stl_path),
        collision_file=str(collision_path),
    )

    estimated_packing_density = estimate_bulk_packing_density(reference_config)


    boxes = load_boxes_from_csv(str(BOXES_CSV), config.item_quantity, bulk=True, mesh_volume=mesh_volume,stability=stability,estimated_packing_density=estimated_packing_density,)

    print("mögliche Verpackungen", boxes)

    for box in boxes:
        lhm_capacity = get_lhm_capacity(box)
        box.lhm_capacity = int(lhm_capacity)



    config = replace(
        config,
        boxes=boxes,
        mesh_volume=mesh_volume,
        stl_file=str(stl_path),
        collision_file=str(collision_path),
    )

    try:
        simulation = PackagingSimulation(config)
        return simulation.run()
    except Exception as error:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )
    

@router.post("/run-single-box")
def run_single_box_simulation(request: SingleBoxSimulationRequest):
    config = request.config
    requested_box = request.box

    try:
        stl_path = resolve_converted_stl(config.stl_file)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))

    mesh_volume = compute_scaled_volume_mm3(stl_path, config.item.length)
    collision_path = ensure_vhacd_collision_mesh(stl_path)

    selected_box = Box(
        name=requested_box.name,
        length=requested_box.length,
        width=requested_box.width,
        height=requested_box.height,
        lhm_capacity=requested_box.lhm_capacity or 0,
    )


    if not selected_box.lhm_capacity:
        selected_box.lhm_capacity = int(get_lhm_capacity(selected_box))

    single_box_config = replace(
        config,
        boxes=[selected_box],
        mesh_volume=mesh_volume,
        stl_file=str(stl_path),
        collision_file=str(collision_path),
        parallel_simulations=False,
        use_gui=True,
        # Genau ein Lauf mit dem gespeicherten Seed -> reproduziert die Schuettung,
        # die zu den Kennwerten auf der Result-Page gehoert. box_index ist hier 0,
        # daher ist der effektive Seed exakt request.random_seed.
        runs_per_box=1,
        random_seed=(
            request.random_seed
            if request.random_seed is not None
            else config.random_seed
        ),
    )

    try:
        simulation = PackagingSimulation(single_box_config)
        return simulation.run()
    except Exception as error:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )