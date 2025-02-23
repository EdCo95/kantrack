# kantrack

[![PyPI](https://img.shields.io/pypi/v/kantrack)](https://pypi.org/project/kantrack/)
[![Python](https://img.shields.io/pypi/pyversions/kantrack)](https://pypi.org/project/kantrack/)
[![License](https://img.shields.io/github/license/EdCo95/kantrack)](LICENSE)

Kantrack is a lightweight task tracker that lives in your Git repositories, keeping project tasks versioned alongside your code. It features a simple FastAPI backend, a minimal web UI, and a CLI for managing tasks. Kantrack is intended for solo developers who want an easy way to track their projects, keeping the task tracking as close to the code as possible - no need to sign in to 3rd party software, nothing to pay, and no risk of forgetting where all of your plans and notes are when you return to a project after six months.

# Features
* Git-native – Task data is stored in a json file inside your repository.
* Minimal and fast – A FastAPI backend with a simple web interface.
* CLI-first – Manage tasks efficiently with a command-line interface.

# Installation
Install with pip:

```
pip install kantrack
```

Or with poetry:

```
poetry add kantrack
```

# Usage

Set where the board is written. By default, it writes to `kantrack_data.json` in the git root, or the current working directory if the folder isn't a git repo. You can control the write location by setting the `KANTRACK_WRITE_DIR` environment variable:

```
export KANTRACK_WRITE_DIR="board"
```

#### Start the Board
Start the board and open the web UI:

```
kantrack start
```

Runs a FastAPI server on `127.0.0.1:8000`. You can specify the host and port, but you'd need to manually update the front-end code to point at the new host/port if you do so.

#### Add a Task (CLI)
Add a task to the default column ("planned")

```
kantrack add "Implement authentication"
```

Specify the column with `--to "name"`, and the size with `--size "size"`. If you specify a column name that doesn't exist, you'll be asked if you'd like to create it.

#### List Tasks (CLI)
```
kantrack list
```

#### Move a Task Between Columns (CLI)
```
kantrack mv "task name" --to "new column"
```

#### Remove a Task
```
kantrack rm "task name"
```

# Development

Clone and install dependencies:
```
git clone https://github.com/YOUR_GITHUB_USERNAME/kantrack.git
cd kantrack
poetry install
```

Set up pre-commit hooks:
```
pre-commit install
pre-commit run --all-files
```

This ensures that code is formatted with Black and imports are managed with isort.

# Contributing
Bug reports, feature requests, and contributions are welcome. Open an issue or submit a pull request on GitHub.
