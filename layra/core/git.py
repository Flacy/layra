import subprocess
from pathlib import Path

from layra.core.exceptions import CloneError

_CLONE_COMMAND: str = "git clone --branch {branch} --single-branch --depth 1 {repo_url} {dest}"


def clone(url: str, destination: Path, *, branch: str = "main") -> None:
    command = _CLONE_COMMAND.format(repo_url=url, dest=destination, branch=branch)

    try:
        subprocess.run(command.split(), check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise CloneError("Failed to clone repository: {}: {}".format(url, e.stderr))
