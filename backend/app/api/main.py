"""FastAPI App Erstellung"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.uploads import router as uploads_router
from app.api.routes.packing import router as packing_router
from app.api.routes.simulation import router as simulation_router
from app.core.config import CONVERTED_DIR


app = FastAPI()

#Middleware um Zugriff auf Api durch Frontend zu erlauben
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#converted Ordner in storage erstellen, für die stl dateien
CONVERTED_DIR.mkdir(parents=True, exist_ok=True)
#verknüpfung mit FastApi route
app.mount("/files", StaticFiles(directory=CONVERTED_DIR), name="files")


app.include_router(uploads_router)
app.include_router(packing_router)
app.include_router(simulation_router)
