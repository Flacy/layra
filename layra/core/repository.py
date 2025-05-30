import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from layra.core import git
from layra.core.storage import Storage, TemplateType
from layra.models.source import Source

TRUSTED_SOURCES: list[Source] = [
    Source(url="github.com", repository="flacy/layra-profiles", branch="main", type="profile"),
]


class Repository:
    def __init__(self) -> None:
        self._storage: Storage = Storage()

    def install(self, url: str, *, type_: TemplateType, branch: str = "main", ) -> None:
        dir_type = "profiles" if type_ == "profile" else "components"
        (dest_path := Path(self._storage.templates_dir / dir_type)).mkdir(parents=True, exist_ok=True)

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            git.clone(url, temp_path, branch=branch)

            for item in temp_path.iterdir():  # type: Path
                if item.is_dir() and not item.name.startswith("."):
                    shutil.copytree(item, (dest_path / item.name), dirs_exist_ok=True)
