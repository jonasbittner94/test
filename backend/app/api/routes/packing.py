'''Zusammenführung der PackingLogik für die Packmusterartikel'''

from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from app.packing.optimizer import Item, PackingOptimizer
from app.packing.box_loader import load_boxes_from_csv
from app.core.config import BOXES_CSV
from app.geometry import compute_scaled_volume_mm3, resolve_converted_stl


class OverlapRequest(BaseModel):
    x: float = 0
    y: float = 0
    z: float = 0


class PositionRequest(BaseModel):
    x: float
    y: float
    z: float


class RotationRequest(BaseModel):
    x: float
    y: float
    z: float


class SizeRequest(BaseModel):
    x: float
    y: float
    z: float


class PatternElementRequest(BaseModel):
    index: int
    position: PositionRequest
    rotation: RotationRequest
    size: SizeRequest


class PatternRequest(BaseModel):
    length: float
    width: float
    height: float
    count: int
    elements: List[PatternElementRequest]


class PackingRequest(BaseModel):
    item_length: float
    item_width: float
    item_height: float
    file_url:str
    quantity: int
    scaledLength: float
    pattern: Optional[PatternRequest] = None
    mesh_volume:Optional[float] = None

router = APIRouter()


@router.post("/packing/top20")
def get_top_20_packing_results(data: PackingRequest):
    item = Item(
        length=data.scaledLength,
        width=data.item_width,
        height=data.item_height,
    )
    
    #Patternobject in dict umwandeln
    pattern = data.pattern.model_dump() if data.pattern else None

    try:
        stl_path = resolve_converted_stl(data.file_url)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))

    mesh_volume = compute_scaled_volume_mm3(stl_path, data.scaledLength)

    effective_volume = mesh_volume
    if pattern:
        helper = PackingOptimizer(
            item=item, quantity=data.quantity, boxes=[], pattern=pattern
        )
        pattern_data = helper._get_pattern_data()
        if pattern_data:
            elements = pattern_data["elements"]
            step_x = helper._pattern_step(elements, "x", item.length)
            step_y = helper._pattern_step(elements, "y", item.width)
            step_z = helper._pattern_step(elements, "z", item.height)
            effective_volume = min(mesh_volume, step_x * step_y * step_z)

    boxes = load_boxes_from_csv(
        str(BOXES_CSV),
        data.quantity,
        bulk=False,
        mesh_volume=mesh_volume
    )

    optimizer = PackingOptimizer(
        item=item,
        quantity=data.quantity,
        boxes=boxes,
        pattern=pattern,
        mesh_volume=effective_volume
    )

    results = optimizer.find_top_boxes(limit=200)

    if not results:
        return {"message": "Keine passende Verpackung gefunden", "results": []}

    return {
        "message": "Folgende Verpackungen kommen für Ihre Konfiguration in Frage:",
        "results": results,
    }
