from dataclasses import dataclass


@dataclass(frozen=True)
class ProfileComponent:
    name: str
    required: bool = False
    default: bool = True


@dataclass
class Profile:
    name: str
    version: str
    description: str
    author: str | None = None

    # Base template.
    base: str = "base"

    # Profile components
    components: list[ProfileComponent] = None

    # Variables by default
    default_variables: dict[str, str] = None

    prompts: list[dict[str, str]] = None

    def __post_init__(self) -> None:
        if self.components is None:
            self.components = []
        if self.default_variables is None:
            self.default_variables = {}
        if self.prompts is None:
            self.prompts = []
