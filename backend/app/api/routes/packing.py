'''Zusammenführung der PackingLogik für die Packmusterartikel'''

from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from app.packing.models import Item
from app.packing.optimizer import PackingOptimizer
from app.packing.box_loader import load_boxes_from_csv
from app.core.config import boxes_data
from app.geometry import compute_convex_volume, resolve_converted_stl


class Vec3(BaseModel):
    x: float
    y: float
    z: float


class GridElementRequest(BaseModel):
    index: int
    position: Vec3
    rotation: Vec3
    size: Vec3


class GridRequest(BaseModel):
    elements: List[GridElementRequest]


class PackingRequest(BaseModel):
    item_width: float
    item_height: float
    file_url: str
    quantity: int
    scaledLength: float
    pattern: Optional[GridRequest] = None
    stability: str
    fill_residual: bool = True


router = APIRouter()


@router.post("/packing/top20")
def get_top_50_packing_results(data: PackingRequest):
    try:
        stl_path = resolve_converted_stl(data.file_url)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))

    optimizer = PackingOptimizer(
        item=Item(
            length=data.scaledLength,
            width=data.item_width,
            height=data.item_height,
        ),
        quantity=data.quantity,
        #Patternobject in dict umwandeln
        packing_grid=data.pattern.model_dump() if data.pattern else None,
        mesh_volume=compute_convex_volume(stl_path, data.scaledLength),
        fill_res=data.fill_residual,
    )

    #Bei starker Überlappung wird das Volumen kleiner, deshalb wird dann die Überlappung
    #vom Boundingboxvolumen abgezogen und damit die Boxen gefiltert
    optimizer.mesh_volume = optimizer.effective_article_volume()
    optimizer.boxes = load_boxes_from_csv(
        str(boxes_data),
        data.quantity,
        bulk=False,
        mesh_volume=optimizer.mesh_volume,
        stability=data.stability,
    )

    results = optimizer.find_top_boxes(limit=50)

    if not results:
        return {"message": "Keine passende Verpackung gefunden", "results": []}

    return {
        "message": "Folgende Verpackungen kommen für Ihre Konfiguration in Frage:",
        "results": results,
    }
