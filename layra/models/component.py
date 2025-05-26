from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class Component:
    name: str
    version: str
    description: str
    author: str | None = None

    dependencies: dict[str, list[str]] = None
    conflicts: list[str] = None

    files: list[dict[str, str]] = None

    pyproject_additions: dict[str, Any] = None

    default_variables: dict[str, str] = None

    path: Path | None = None

    def __post_init__(self) -> None:
        if self.dependencies is None:
            self.dependencies = {"packages": []}
        if self.conflicts is None:
            self.conflicts = []
        if self.files is None:
            self.files = []
        if self.pyproject_additions is None:
            self.pyproject_additions = {}
        if self.default_variables is None:
            self.default_variables = {}
