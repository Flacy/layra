from dataclasses import dataclass


@dataclass
class Profile:
    name: str
    version: str
    description: str
    author: str | None = None

    # Base template.
    base: str = "base"

    # Variables by default
    default_variables: dict[str, str] = None

    prompts: list[dict[str, str]] = None

    def __post_init__(self) -> None:
        if self.default_variables is None:
            self.default_variables = {}
        if self.prompts is None:
            self.prompts = []
