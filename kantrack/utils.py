import subprocess
from pathlib import Path

import click


def get_git_root(fallback: bool = True) -> Path:
    """Returns the root directory of the current Git repository.

    If not inside a Git repo:
    - If `fallback=True`, return the current directory.
    - Otherwise, exit with an error message.
    """
    try:
        root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], stderr=subprocess.DEVNULL
        )
        return Path(root.decode().strip())
    except subprocess.CalledProcessError:
        if fallback:
            click.echo(
                "Warning: Not inside a Git repository. Using current directory instead.",
                err=True,
            )
            return Path.cwd()
        else:
            click.echo(
                "Error: This command must be run inside a Git repository.", err=True
            )
            exit(1)
