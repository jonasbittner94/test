"""Erstellung der Pfade für die CAD-Dateien und Verpackungen"""

import os
from pathlib import Path

# backend
BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data"
STORAGE_DIR = BASE_DIR / "storage"
UPLOAD_DIR = STORAGE_DIR / "uploads"
CONVERTED_DIR = STORAGE_DIR / "converted"

# Standard-CSV mit den verfuegbaren Faltschachteln/Verpackungen
BOXES_CSV = DATA_DIR / "meine_datei.csv"

FRONTEND_ORIGINS = [
    origin.strip()
    for origin in os.getenv("FRONTEND_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]
