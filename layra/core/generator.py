import shutil
from pathlib import Path
from typing import Any

import rtoml
import tomli_w

from layra import __version__
from layra.core.exceptions import ProjectError
from layra.core.templates import TemplateManager
from layra.core.variables import substitute
from layra.models.component import Component
from layra.models.profile import Profile

DEFAULT_PYTHON_VERSION: str = "3.12"


def _copy_component_files(
    component: Component,
    output_dir: Path,
    variables: dict[str, str]
) -> None:
    """Копирует файлы компонента"""

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
    def __init__(self) -> None:
        self._template_manager = TemplateManager()

    def _copy_base_template(self, output_dir: Path, *, variables: dict[str, str]) -> None:
        _copy_template_files(self._template_manager.base_template_path, output_dir, variables=variables)

    def _prepare_variables(
        self,
        project_name: str,
        *,
        profile: Profile,
        components: list[Component],
        user_variables: dict[str, str] | None = None,
    ) -> dict[str, str]:
        variables = {
            "project_name": project_name,
            "package_name": project_name.lower().replace("-", "_"),
            "project_description": "A python project generated with Layra",
        } | profile.default_variables

        for component in components:
            variables.update(component.default_variables)

        if user_variables:
            variables.update(user_variables)

        return variables

    def _generate_pyproject(
        self,
        *,
        output_dir: Path,
        project_name: str,
        profile: Profile,
        components: list[Component],
        variables: dict[str, str],
    ) -> None:
        config = {
            "project": {
                "name": project_name,
                "version": "0.0.1",
                "description": variables.get("project_description", ""),
                "authors": [{"name": variables.get("author_name", ""), "email": variables.get("author_email", "")}],
                "readme": "README.md",
                "requires-python": ">={}".format(variables.get("python_version", DEFAULT_PYTHON_VERSION)),
                "dependencies": [],
            }
        }

        all_dependencies = []
        for component in components:
            all_dependencies.extend(component.dependencies.get("packages", []))

        if all_dependencies:
            config["project"]["dependencies"] = sorted(set(all_dependencies))

        for component in components:
            _deep_merge(config, component.pyproject_additions)

        config["tool"] = config.get("tool", {})
        config["tool"]["layra"] = {
            "version": __version__,
            "profile": profile.name,
            "components": [c.name for c in components],
        }

        with open(output_dir / "pyproject.toml", "wb") as f:
            tomli_w.dump(config, f)

    def create_project(
        self,
        name: str,
        *,
        profile: str,
        output_dir: Path,
        variables: dict[str, str] | None = None,
    ) -> Path:
        try:
            obj = self._template_manager.load_profile(profile)
            components = self._template_manager.resolve_components(obj)
            all_variables = self._prepare_variables(name, profile=obj, components=components, user_variables=variables)

            output_dir.mkdir(parents=True, exist_ok=True)
            self._copy_base_template(output_dir, variables=variables)

            for component in components:
                _copy_component_files(component, output_dir, all_variables)

            (source_dir := output_dir / name).mkdir()
            (source_dir / "__init__.py").touch(0o777)

            self._generate_pyproject(
                output_dir=output_dir,
                project_name=name,
                profile=obj,
                components=components,
                variables=all_variables,
            )
            return output_dir
        except Exception as e:
            if output_dir.exists():
                shutil.rmtree(output_dir, ignore_errors=True)
            raise ProjectError("Failed to create project: {}".format(e)) from e
