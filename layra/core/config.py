import os
from functools import lru_cache
from pathlib import Path

CONFIG_DIRECTORY: str = "layra"
STORAGE_DIRECTORY: str = "storage"
MANIFEST_FILE: str = "layra.yaml"


@lru_cache(maxsize=1)
def _get_path_to_config() -> Path:
    if os.name == "nt":  # Windows.
        base_path = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:  # Unix-Like.
        base_path = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))

    return base_path / CONFIG_DIRECTORY


class Config:
    def __init__(self) -> None:
        self._base_path: Path = _get_path_to_config()

    @property
    def storage_dir(self) -> Path:
        return self._base_path / STORAGE_DIRECTORY
