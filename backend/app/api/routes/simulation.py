'''Aufrufen der Simulation durch die API.'''

from fastapi import APIRouter, HTTPException
import traceback

from app.simulation.sim import PackagingSimulation, SimulationConfig
from app.packing.box_loader import load_boxes_from_csv
from app.core.config import BOXES_CSV
from dataclasses import replace
from app.geometry import (
    compute_scaled_volume_mm3,
    ensure_vhacd_collision_mesh,
    resolve_converted_stl,
)




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

    boxes = load_boxes_from_csv(str(BOXES_CSV), config.item_quantity, bulk=True, mesh_volume=mesh_volume)

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