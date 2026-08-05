"""Erstellung der Pfade für die CAD-Dateien und Verpackungen"""

import os
from pathlib import Path

# backend
base_directory = Path(__file__).resolve().parents[2]

data_directory = base_directory / "data"
storage_directory = base_directory / "storage"
upload_directory = storage_directory / "uploads"
convert_directory = storage_directory / "converted"

# Standard-CSV mit den verfuegbaren Faltschachteln/Verpackungen
boxes_data = data_directory / "Verpackungskatalog.csv"

allowed_origins = [
    origin.strip()
    for origin in os.getenv("allowed_origins", "http://localhost:3000").split(",")
    if origin.strip()
]
