from fastapi import APIRouter, File, UploadFile, HTTPException
from pathlib import Path
from uuid import uuid4
import shutil
import trimesh


from app.services.converterStpStl.converter import step_to_stl_cq
from app.core.config import UPLOAD_DIR, CONVERTED_DIR



router = APIRouter()

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CONVERTED_DIR.mkdir(parents=True, exist_ok=True)

def get_item_from_stl(stl_path: Path) -> dict:
    mesh = trimesh.load_mesh(str(stl_path))

    bounds = mesh.bounds
    min_bounds = bounds[0]
    max_bounds = bounds[1]

    dimensions = max_bounds - min_bounds


    return {
        "length": float(dimensions[0]),
        "width": float(dimensions[1]),
        "height": float(dimensions[2]),
    }


@router.post("/convert-stp-to-stl")
async def convert_stp_to_stl(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Keine Datei hochgeladen.")

    if not file.filename.lower().endswith(".stp"):
        raise HTTPException(status_code=400, detail="Nur .stp-Dateien sind erlaubt.")

    file_id = uuid4().hex
    input_path = UPLOAD_DIR / f"{file_id}.stp"
    output_path = CONVERTED_DIR / f"{file_id}.stl"

    try:
        with input_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        step_to_stl_cq(str(input_path), str(output_path))
        item = get_item_from_stl(output_path)


        return {
            "file_id": f"{file_id}.stl",
            "file_url": f"/files/{file_id}.stl",
            "stl_file": str(output_path).replace("\\", "/"),
            "item": item,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Konvertierung fehlgeschlagen: {str(e)}",
        )


@router.post("/upload-stl")
async def upload_stl(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Keine Datei hochgeladen.")

    if not file.filename.lower().endswith(".stl"):
        raise HTTPException(status_code=400, detail="Nur .stl-Dateien sind erlaubt.")

    file_id = uuid4().hex
    output_path = CONVERTED_DIR / f"{file_id}.stl"

    try:
        with output_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        item = get_item_from_stl(output_path)


        return {
            "file_id": f"{file_id}.stl",
            "file_url": f"/files/{file_id}.stl",
            "stl_file": str(output_path).replace("\\", "/"),
            "item": item,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Upload fehlgeschlagen: {str(e)}",
        )