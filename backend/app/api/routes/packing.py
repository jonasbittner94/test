'''Zusammenführung der PackingLogik für die Packmusterartikel'''

from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter
from app.packing.optimizer import Item, PackingOptimizer
from app.packing.box_loader import load_boxes_from_csv
from app.core.config import BOXES_CSV


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
    quantity: int
    overlap: Optional[OverlapRequest] = None
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

    boxes = load_boxes_from_csv(
        str(BOXES_CSV),
        data.quantity,
        bulk=False,
        mesh_volume=data.mesh_volume

    )

    overlap = {
        "x": data.overlap.x if data.overlap else 0,
        "y": data.overlap.y if data.overlap else 0,
        "z": data.overlap.z if data.overlap else 0,
    }


    optimizer = PackingOptimizer(
        item=item,
        quantity=data.quantity,
        boxes=boxes,
        overlap=overlap,
        pattern=pattern,
        mesh_volume=data.mesh_volume
    )

    results = optimizer.find_top_boxes(limit=100)

    if not results:
        return {"message": "Keine passende Verpackung gefunden", "results": []}

    return {
        "message": "Passende Verpackungen gefunden",
        "results": results,
    }