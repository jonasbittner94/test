"""FastAPI App Erstellung"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.uploads import router as uploads_router
from app.api.routes.packing import router as packing_router
from app.api.routes.simulation import router as simulation_router
from app.core.config import convert_directory, allowed_origins


app = FastAPI()

#Middleware um Zugriff auf Api durch Frontend zu erlauben
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

#converted Ordner in storage erstellen, für die stl dateien
convert_directory.mkdir(parents=True, exist_ok=True)
#verknüpfung mit FastApi route
app.mount("/files", StaticFiles(directory=convert_directory), name="files")


app.include_router(uploads_router)
app.include_router(packing_router)
app.include_router(simulation_router)
