from pathlib import Path
from typing import Literal

from layra.core.config import Config, MANIFEST_FILE
from layra.core.exceptions import ValidationError

TemplateType = Literal["profile", "component"]


class Storage:
    def __init__(self) -> None:
        self._config: Config = Config()
        self._templates_dir: Path = self._config.storage_dir / "templates"

    @property
    def templates_dir(self) -> Path:
        return self._templates_dir

    def path_to_template(self, name: str, type_: TemplateType) -> Path:
        return Path(self._templates_dir / "{}s".format(type_) / name)

    def validate_template(self, name: str, *, type_: TemplateType) -> None:
        template_dir = self.path_to_template(name, type_)

        if not template_dir.exists():
            raise ValidationError("{} directory was not found".format(type_.title()))
        elif not template_dir.is_dir():
            raise ValidationError("'{}' is a file, not a directory".format(template_dir))
        elif not (template_dir / MANIFEST_FILE).exists():
            raise ValidationError("'{}' file doesn't exist".format(MANIFEST_FILE))
