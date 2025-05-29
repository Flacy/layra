from pathlib import Path

import yaml

from layra.core.exceptions import TemplateLoadError, ValidationError
from layra.models.component import Component
from layra.models.profile import Profile

MANIFEST_FILE: str = "layra.yaml"


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
        manifest_path = self._profiles_dir / name / MANIFEST_FILE

        if not manifest_path.exists():
            available = [p.stem for p in self._profiles_dir.glob("*")]
            raise TemplateLoadError("Profile '{}' not found. Available: {}".format(name, ", ".join(available)))

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
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
            raise TemplateLoadError("Failed to load profile '{}': {}".format(name, e)) from e

    def load_component(self, name: str) -> Component:
        """
        Loads component by name.

        :param name:
        :return:
        """
        component_path = self._components_dir / name
        manifest_path = component_path / MANIFEST_FILE

        if not manifest_path.exists():
            raise TemplateLoadError("Component '{}' not found or missing 'component.yaml'".format(name))

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            return Component(
                name=data["name"],
                version=data["version"],
                description=data["description"],
                author=data.get("author"),
                dependencies=data.get("dependencies", {"packages": []}),
                conflicts=data.get("conflicts", []),
                inside=data.get("inside", True),
                pyproject_additions=data.get("pyproject_additions", {}),
                default_variables=data.get("default_variables", {}),
                path=component_path,
            )
        except Exception as e:
            raise TemplateLoadError("Failed to load component '{}': {}".format(name, e)) from e

    def list_profiles(self) -> list[Profile]:
        profiles = []

        for file in self._profiles_dir.glob("*"):
            try:
                profiles.append(self.load_profile(file.stem))
            except TemplateLoadError:
                continue

        return sorted(profiles, key=lambda p: p.name)
