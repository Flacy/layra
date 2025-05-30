from dataclasses import dataclass


@dataclass
class Profile:
    name: str
    version: str
    description: str
    author: str | None = None

    dependencies: list[str] = None

    # Variables by default
    default_variables: dict[str, str] = None

    prompts: list[dict[str, str]] = None

    def __post_init__(self) -> None:
        if self.dependencies is None:
            self.dependencies = []
        if self.default_variables is None:
            self.default_variables = {}
        if self.prompts is None:
            self.prompts = []
