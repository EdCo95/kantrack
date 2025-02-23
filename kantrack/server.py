import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from kantrack.utils import get_git_root

# Environment variable for storage location
KANBAN_WRITE_DIR = Path(os.getenv("KANTRACK_WRITE_DIR", get_git_root(fallback=True)))
KANBAN_FILE = KANBAN_WRITE_DIR / "kantrack_data.json"

# Ensure the directory exists
KANBAN_WRITE_DIR.mkdir(parents=True, exist_ok=True)

# FastAPI app
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class KanbanData(BaseModel):
    data: dict


@app.post("/api/save")
def save_kanban(data: KanbanData):
    """Saves the Kanban board data to a local file."""
    try:
        with open(KANBAN_FILE, "w", encoding="utf-8") as f:
            json.dump(data.model_dump(), f, indent=4)
        return {"message": "Kanban board saved successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error saving Kanban board: {str(e)}"
        )


@app.get("/api/load")
def load_kanban():
    """Loads the Kanban board data from a local file."""
    if not KANBAN_FILE.exists():
        return {"data": {}}  # Return empty board if no file exists

    try:
        with open(KANBAN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error loading Kanban board: {str(e)}"
        )


# Serve the static files
app.mount("/", StaticFiles(directory="kantrack/static", html=True), name="static")
