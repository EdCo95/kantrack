import json
import os
import signal
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

import requests
import typer

from kantrack.utils import get_git_root

DEFAULT_KANBAN = {
    "data": {
        "planned": [
            {
                "title": "Task 1",
                "desc": "This is the description for Task 1.",
                "size": "Small",
            },
            {"title": "Task 2", "desc": "Description for Task 2.", "size": "Medium"},
        ],
        "in_progress": [],
        "done": [],
    }
}
KANBAN_WRITE_DIR = Path(os.getenv("KANTRACK_WRITE_DIR", get_git_root(fallback=True)))
KANBAN_FILE = KANBAN_WRITE_DIR / "kantrack_data.json"
STARTUP_WAIT_TIME_SECS = 5
WAIT_TIME_BETWEEN_TRIES = 0.5


app = typer.Typer()


def _wait_for_server_to_start(url: str):
    for _ in range(int(STARTUP_WAIT_TIME_SECS / WAIT_TIME_BETWEEN_TRIES)):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                break
        except requests.exceptions.ConnectionError:
            time.sleep(WAIT_TIME_BETWEEN_TRIES)


def handle_exit(process: subprocess.Popen) -> None:
    """Ensure the subprocess is terminated properly on exit."""
    print("\nStopping server...")
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
    sys.exit(0)


def _maybe_make_column(name: str, data: dict) -> bool:
    """Check if a column exists and ask the user if they want to create it if it doesn't."""
    if name not in data["data"]:
        typer.echo(
            f"❌ Column '{name}' not found. Choose from: {', '.join(data['data'].keys())}"
        )
        add_column = typer.confirm("Do you want to add this column?")
        if add_column:
            data["data"][name] = []
            typer.echo(f"✅ Column '{name}' added.")
            return True
        else:
            return False
    return True


def _load_board() -> dict | None:
    """Loads the board data from the local file."""
    if not KANBAN_FILE.exists():
        typer.echo("📂 No Kanban board found. Start by adding tasks!")
        return None

    with open(KANBAN_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_all_task_names() -> list[str]:
    """Returns a list of all task names in the board."""
    data = _load_board()
    if data is None:
        return []

    task_names = []
    for _, task_list in data["data"].items():
        for task in task_list:
            task_names.append(task["title"])
    return task_names


def _task_autocomplete(incomplete: str) -> list[str]:
    """Autocomplete function for task names."""
    tasks = _get_all_task_names()
    return [task for task in tasks if incomplete.lower() in task.lower()]


def _get_all_column_names() -> list[str]:
    """Returns a list of all column names in the board."""
    data = _load_board()
    if data is None:
        return []
    return list(data["data"].keys())


def _column_autocomplete(incomplete: str) -> list[str]:
    """Autocomplete function for column names."""
    columns = _get_all_column_names()
    return [column for column in columns if incomplete.lower() in column.lower()]


@app.command()
def start(
    host: str = typer.Option("127.0.0.1", help="The host to run the server on"),
    port: int = typer.Option(8000, help="The port to run the server on"),
):
    """Start the Kantrack server and open the board in the browser."""
    if not KANBAN_FILE.exists():
        with open(KANBAN_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_KANBAN, f, indent=4)

    process = subprocess.Popen(
        [
            "uvicorn",
            "kantrack.server:app",
            "--host",
            host,
            "--port",
            str(port),
            "--reload",
        ]
    )

    signal.signal(signal.SIGINT, lambda *_: handle_exit(process))
    signal.signal(signal.SIGTERM, lambda *_: handle_exit(process))

    url = f"http://{host}:{port}"
    _wait_for_server_to_start(url)
    webbrowser.open(url)
    process.wait()


@app.command()
def add(
    task: str,
    column: str = typer.Option(
        "planned",
        help="The column to add the task to",
        autocompletion=_column_autocomplete,
    ),
    size: str = "Medium",
):
    """Add a task to the Kanban board."""
    data = _load_board()

    if not data:
        typer.echo(f"📂 No Kanban board found. Creating a new one at {KANBAN_FILE}...")
        data = DEFAULT_KANBAN

    column = column.lower().strip().replace(" ", "_")

    made_column = _maybe_make_column(column, data)
    if not made_column:
        return

    data["data"][column].append({"title": task, "desc": "", "size": size})

    with open(KANBAN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    typer.echo(f"✅ Added task: {task} to column '{column}'")


@app.command()
def list():
    """List all tasks in the Kanban board."""
    data = _load_board()

    if data is None:
        return

    if not data["data"]:
        typer.echo("✅ No tasks yet! Your Kanban board is empty.")
        return

    typer.echo("\n📌 Current Tasks:")
    for column, task_list in data["data"].items():
        typer.echo(f"\n📂 {column.replace('_', ' ').title()}:")
        for task in task_list:
            typer.echo(f"  - {task['title']} ({task['size']})")


@app.command()
def rm(
    task_name: str = typer.Argument(..., autocompletion=_task_autocomplete),
):
    """Removes the specified task."""
    data = _load_board()

    for column, task_list in data["data"].items():
        for task in task_list:
            title = task["title"].lower().strip()
            if title == task_name.lower().strip():
                task_list.remove(task)
                with open(KANBAN_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
                typer.echo(f"✅ Removed task: {task} from column '{column}'.")
                return

    typer.echo(f"❌ Task '{task}' not found in the Kanban board.")


@app.command()
def mv(
    task_name: str = typer.Argument(..., autocompletion=_task_autocomplete),
    new_column: str = typer.Argument(..., autocompletion=_column_autocomplete),
):
    """Moves the specified task to a new column."""
    data = _load_board()

    new_column = new_column.lower().strip().replace(" ", "_")

    made_column = _maybe_make_column(new_column, data)
    if not made_column:
        return

    for column, task_list in data["data"].items():
        for task in task_list:
            title = task["title"].lower().strip()
            if title == task_name.lower().strip():
                task_list.remove(task)
                data["data"][new_column].append(task)
                with open(KANBAN_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
                typer.echo(
                    f"✅ Moved task '{task_name}' from '{column}' to column '{new_column}'."
                )
                return

    typer.echo(f"❌ Task '{task_name}' not found in the Kanban board.")


if __name__ == "__main__":
    app()
