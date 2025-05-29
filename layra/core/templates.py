from pathlib import Path
from tkinter.font import names

import yaml

from layra.core.exceptions import TemplateError, ValidationError
from layra.models.component import Component
from layra.models.profile import Profile


def _check_conflicts(components: list[Component]) -> None:
    names = {c.name for c in components}

    for component in components:
        for conflict in component.conflicts:
            if conflict in names:
                raise ValidationError("Components '{}' and '{}' are conflict".format(component.name, conflict))


class TemplateManager:
    def __init__(self) -> None:
        self._templates_dir: Path = Path(__file__).parent.parent / "templates"
        self._profiles_dir = self._templates_dir / "profiles"
        self._components_dir = self._templates_dir / "components"
        self._base_dir = self._templates_dir / "base"

    @property
    def path_to_base_template(self) -> Path:
        return self._base_dir

    def profile_path(self, profile: str | Profile) -> Path:
        profile_name = profile.name if isinstance(profile, Profile) else profile
        return self._profiles_dir / profile_name

    def load_profile(self, name: str) -> Profile:
        """
        Loads profile by name.

        :param name:
        :return:
        """
        path = self._profiles_dir / name / "profile.yaml"

        if not path.exists():
            available = [p.stem for p in self._profiles_dir.glob("*")]
            raise TemplateError("Profile '{}' not found. Available: {}".format(name, ", ".join(available)))

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            return Profile(
                name=data["name"],
                version=data["version"],
                description=data["description"],
                author=data.get("author"),
                dependencies=data.get("dependencies", []),
                default_variables=data.get("default_variables", {}),
                prompts=data.get("prompts", []),
            )
        except Exception as e:
            raise TemplateError("Failed to load profile '{}': {}".format(name, e)) from e

    def load_component(self, name: str) -> Component:
        """
        Loads component by name.

        :param name:
        :return:
        """
        component_path = self._components_dir / name
        config_path = component_path / "component.yaml"

        if not config_path.exists():
            raise TemplateError("Component '{}' not found or missing 'component.yaml'".format(name))

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            return Component(
                name=data["name"],
                version=data["version"],
                description=data["description"],
                author=data.get("author"),
                dependencies=data.get("dependencies", {"packages": []}),
                conflicts=data.get("conflicts", []),
                files=data.get("files", []),
                pyproject_additions=data.get("pyproject_additions", {}),
                default_variables=data.get("default_variables", {}),
                path=component_path,
            )
        except Exception as e:
            raise TemplateError("Failed to load component '{}': {}".format(name, e)) from e

    def list_profiles(self) -> list[Profile]:
        profiles = []

        for file in self._profiles_dir.glob("*.yaml"):
            try:
                profiles.append(self.load_profile(file.stem))
            except Exception:
                continue

        return sorted(profiles, key=lambda p: p.name)
