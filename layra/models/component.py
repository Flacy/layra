from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Component:
    name: str
    version: str
    description: str
    author: str | None = None

    dependencies: list[str] = None
    conflicts: list[str] = None

    inside: bool = True

    pyproject_additions: dict[str, Any] = None

    default_variables: dict[str, str] = None

    path: Path | None = None
