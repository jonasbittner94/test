from fastapi import APIRouter, HTTPException
import traceback

from app.simulation.sim import PackagingSimulation, SimulationConfig
from app.packing.box_loader import load_boxes_from_csv
from app.packing.optimizer import Item
from app.core.config import BOXES_CSV
from dataclasses import replace



router = APIRouter(
    prefix="/simulation",
    tags=["simulation"],
)


@router.post("/run")
def run_simulation(config: SimulationConfig):
    item = Item(
        length=config.item.length,
        width=config.item.width,
        height=config.item.height,
    )

    boxes = load_boxes_from_csv(str(BOXES_CSV), item, config.item_quantity, bulk=True)
    
    

    config = replace(config, boxes=boxes)

    try:
        simulation = PackagingSimulation(config)
        return simulation.run()
    except Exception as error:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )