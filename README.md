# PackagingOptimizer

Bachelorarbeitsprojekt: Tool zum Finden der optimalen Verpackung.
Besteht aus einem **Python/FastAPI-Backend** und einem **Next.js/React-Frontend**.

## Voraussetzungen

- Python 3.12
- Node.js 20+ (getestet mit Node 24)

## Backend starten

```bash
cd backend

# Virtuelle Umgebung anlegen (nur beim ersten Mal)
py -3.12 -m venv .venv

# Aktivieren
#   Windows (PowerShell):
.venv\Scripts\Activate.ps1
#   Windows (Git Bash):
source .venv/Scripts/activate

# Abhängigkeiten installieren (nur beim ersten Mal)
pip install -r requirements.txt

# Server starten (API auf http://localhost:8000)
uvicorn app.api.main:app --reload --port 8000
```

Wichtig: Der Server muss aus dem `backend/`-Ordner gestartet werden, damit
der Import-Pfad `app...` funktioniert. Interaktive API-Doku: http://localhost:8000/docs

## Frontend starten

```bash
cd frontend

# Abhängigkeiten installieren (nur beim ersten Mal)
npm install

# Dev-Server starten (http://localhost:3000)
npm run dev
```

Das Frontend erwartet das Backend unter `http://localhost:8000` (in
`lib/api/uploads.ts` fest verdrahtet). Beide Server müssen parallel laufen.

## Projektstruktur

```
backend/
  app/
    api/          FastAPI App + Routen (uploads, packing, simulation)
    core/         Konfiguration/Pfade (config.py)
    packing/      Optimierungs-Logik (optimizer, models, box_loader)
    services/     STP -> STL Konverter
    simulation/   PyBullet-Simulation
  data/           CSV-Daten (Verpackungen) + Beispiel-STL
frontend/
  app/            Next.js App-Router Seiten
  components/     UI- und Rendering-Komponenten (Three.js)
  context/        React Context (FileContext)
  lib/            API-Client
```
