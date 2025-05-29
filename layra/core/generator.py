import shutil
from pathlib import Path
from sys import version_info
from typing import Any

import tomli_w

from layra import __version__
from layra.core.exceptions import ProjectError
from layra.core.templates import TemplateManager
from layra.core.variables import substitute
from layra.models.component import Component
from layra.models.profile import Profile

DEFAULT_PYTHON_VERSION: str = "{}.{}".format(version_info.major, version_info.minor)
DEFAULT_PROJECT_DESCRIPTION: str = "A python project generated with Layra"
DEFAULT_PROJECT_VERSION: str = "0.0.1"


def _copy_component_files(
    component: Component,
    output_dir: Path,
    variables: dict[str, str]
) -> None:
    for file_entry in component.files:
        src_path = component.path / file_entry["src"]
        dest_path = output_dir / file_entry["dest"]

        if src_path.is_dir():
            _copy_template_files(src_path, dest_path, variables=variables)
        else:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            content = src_path.read_text(encoding="utf-8")
            processed_content = substitute(content, variables=variables)
            dest_path.write_text(processed_content, encoding="utf-8")


def _copy_template_files(
    source_dir: Path,
    dest_dir: Path,
    *,
    variables: dict[str, str],
) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)

    for item in source_dir.glob("*"):
        if item.is_file():
            relative_path = item.relative_to(source_dir)
            dest_file = dest_dir / relative_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)

            try:
                content = item.read_text(encoding="utf-8")
                processed_content = substitute(content, variables=variables)
                dest_file.write_text(processed_content, encoding="utf-8")
            except UnicodeDecodeError:
                shutil.copy2(item, dest_file)


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
        _copy_template_files(
            self._template_manager.base_template_path,
            self._output_directory,
            variables=self._variables,
        )

    def _prepare_variables(self) -> None:
        for component in self._components:
            for key, value in component.default_variables.items():
                if key not in self._variables:
                    self._variables[key] = value

    def _generate_pyproject(self) -> None:
        config = {
            "project": {
                "name": self._variables.get("project_name", self._project_name),
                "version": self._variables.get("project_version", DEFAULT_PROJECT_VERSION),
                "description": self._variables.get("project_description", DEFAULT_PROJECT_DESCRIPTION),
                "authors": [
                    {"name": self._variables.get("author_name", ""), "email": self._variables.get("author_email", "")}
                ],
                "readme": "README.md",
                "requires-python": ">={}".format(self._variables.get("python_version", DEFAULT_PYTHON_VERSION)),
                "dependencies": [],
            }
        }

        all_dependencies = []
        for component in self._components:
            all_dependencies.extend(component.dependencies.get("packages", []))

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

            for component in self._components:
                _copy_component_files(component, self._output_directory, self._variables)

            (source_dir := self._output_directory / self.package_name).mkdir()
            (source_dir / "__init__.py").touch(0o777)

            self._generate_pyproject()
            return self._output_directory
        except Exception as e:
            if self._output_directory.exists():
                shutil.rmtree(self._output_directory, ignore_errors=True)
            raise ProjectError("Failed to create project: {}".format(e)) from e
