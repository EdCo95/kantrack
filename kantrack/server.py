import importlib.resources as resources
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
    data: dict[str, list[dict[str, str]]]


def _get_all_task_names(data: KanbanData) -> list[str]:
    """Get all task names from the Kanban board data."""
    return [task["title"] for column in data.data.values() for task in column]


def _all_task_names_are_unique(data: KanbanData) -> bool:
    """Check if all task names in the Kanban board data are unique."""
    all_task_names = _get_all_task_names(data)
    return len(all_task_names) == len(set(all_task_names))


@app.post("/api/save")
def save_kanban(data: KanbanData):
    """Saves the Kanban board data to a local file."""
    if not _all_task_names_are_unique(data):
        raise HTTPException(
            status_code=400, detail="All task names must be unique within the board."
        )
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
try:
    static_dir = str(resources.files("kantrack").joinpath("static"))
    if not Path(static_dir).exists():
        raise RuntimeError(f"Static directory '{static_dir}' does not exist")
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
except RuntimeError as e:
    print(f"Warning: {e}")
