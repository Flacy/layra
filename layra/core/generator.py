import shutil
from pathlib import Path
from sys import version_info
from typing import Any

import tomli_w

from layra import __version__
from layra.core.exceptions import ProjectError
from layra.core.templates import TemplateManager, MANIFEST_FILE
from layra.core.variables import substitute
from layra.models.component import Component
from layra.models.profile import Profile

DEFAULT_PYTHON_VERSION: str = "{}.{}".format(version_info.major, version_info.minor)
DEFAULT_PROJECT_DESCRIPTION: str = "A python project generated with Layra"
DEFAULT_PROJECT_VERSION: str = "0.0.1"


def _deep_merge(target: dict[str, Any], source: dict[str, Any]) -> None:
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            _deep_merge(target[key], value)
        else:
            target[key] = value


class ProjectGenerator:
    def __init__(
        self,
        *,
        name: str,
        profile: str,
        output_dir: Path,
        variables: dict[str, str] | None = None,
        components: list[str] | None = None
    ) -> None:
        self._template_manager = TemplateManager()

        self._project_name: str = name
        self._selected_profile: Profile = self._template_manager.load_profile(profile)
        self._components: list[Component] = [self._template_manager.load_component(c_name) for c_name in components]
        self._output_directory: Path = output_dir
        self._variables: dict[str, str] = variables or {}

    @property
    def package_name(self) -> str:
        return self._project_name.lower().replace("-", "_")

    def _copy_base_template(self) -> None:
        self._copy_all(self._template_manager.path_to_base_template, inside=False)

    def _copy_profile(self) -> None:
        self._copy_all(self._template_manager.profile_path(self._selected_profile), except_=MANIFEST_FILE)

    def _copy_component(self, component: Component) -> None:
        self._copy_all(component.path, except_=MANIFEST_FILE, inside=False)

    def _copy_all(self, source_dir: Path, *, except_: str | None = None, inside: bool = True) -> None:
        source_dir.mkdir(parents=True, exist_ok=True)

        for item in source_dir.rglob("*"):  # type: Path
            if item.name == except_:
                continue

            relative_path = item.relative_to(source_dir)
            dest_file = self._output_directory / (self.package_name if inside else "") / relative_path

            if item.is_dir():
                dest_file.mkdir(parents=True, exist_ok=True)
            elif item.is_file():
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                try:
                    data = item.read_text(encoding="utf-8")
                    dest_file.write_text(substitute(data, variables=self._variables), encoding="utf-8")
                except UnicodeDecodeError:
                    shutil.copy2(item, dest_file)

    def _prepare_variables(self) -> None:
        if "package_name" not in self._variables:
            self._variables["package_name"] = self.package_name
        if "project_name" not in self._variables:
            self._variables["project_name"] = self._project_name
        if "project_version" not in self._variables:
            self._variables["project_version"] = DEFAULT_PROJECT_VERSION
        if "project_description" not in self._variables:
            self._variables["project_description"] = DEFAULT_PROJECT_DESCRIPTION
        if "python_version" not in self._variables:
            self._variables["python_version"] = DEFAULT_PYTHON_VERSION

        for key, value in self._selected_profile.default_variables.items():
            if key not in self._variables:
                self._variables[key] = value

        for component in self._components:
            for key, value in component.default_variables.items():
                if key not in self._variables:
                    self._variables[key] = value

    def _generate_pyproject(self) -> None:
        config = {
            "project": {
                "name": self._variables["project_name"],
                "version": self._variables["project_version"],
                "description": self._variables["project_description"],
                "authors": [
                    {"name": self._variables.get("author_name", ""), "email": self._variables.get("author_email", "")}
                ],
                "readme": "README.md",
                "requires-python": ">={}".format(self._variables["python_version"]),
            }
        }

        all_dependencies = self._selected_profile.dependencies.copy()
        for component in self._components:
            all_dependencies.extend(component.dependencies)

        if all_dependencies:
            config["project"]["dependencies"] = sorted(set(all_dependencies))

        for component in self._components:
            _deep_merge(config, component.pyproject_additions)

        if not "tool" in config:
            config["tool"] = {}

        config["tool"]["layra"] = {
            "version": __version__,
            "profile": self._selected_profile.name,
            "components": [c.name for c in self._components],
        }

        with open(self._output_directory / "pyproject.toml", "wb") as f:
            tomli_w.dump(config, f)

    def create(self) -> Path:
        try:
            self._output_directory.mkdir(parents=True, exist_ok=True)
            self._prepare_variables()
            self._copy_base_template()
            self._copy_profile()
            self._generate_pyproject()

            for component in self._components:
                self._copy_component(component)

            (source_dir := self._output_directory / self.package_name).mkdir(exist_ok=True)
            (source_dir / "__init__.py").touch(0o777)

            return self._output_directory
        except Exception as e:
            if self._output_directory.exists():
                shutil.rmtree(self._output_directory, ignore_errors=True)
            raise ProjectError("Failed to create project: {}".format(e)) from e
