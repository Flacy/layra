from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table
from typer import Typer, Argument, Option

from layra import __version__
from layra.core.exceptions import ParseError
from layra.core.generator import ProjectGenerator
from layra.core.repository import Repository, TRUSTED_SOURCES
from layra.core.templates import TemplateManager

app = Typer(
    name="layra",
    help="build smarter, start faster",
    rich_markup_mode="rich",
)
console = Console()


def _resolve_output_path(project_name: str, output_dir: Path | None) -> Path:
    if output_dir is None:
        return Path.cwd() / project_name
    elif output_dir.is_absolute():
        return output_dir / project_name
    else:
        return Path.cwd() / output_dir / project_name


def _parse_variables(variables: list[str]) -> dict[str, Any]:
    result = {}

    for var in variables:
        if "=" not in var:
            raise ParseError("Missing '=' in variable '{}'".format(var.strip()))
        else:
            key, value = var.strip().split("=")
            result[key] = value

    return result


@app.command()
def new(
    project_name: str = Argument(..., help="Name of the project to create"),
    profile: str = Option("web-fastapi", "--profile", "-p", help="Project profile"),
    output_dir: Path | None = Option(None, "--output", "-o", help="Output directory"),
    components: list[str] | None = Option(None, "--component", "-c", help="Include component"),
    variables: list[str] | None = Option(None, "--arg", "-a", help="Define argument")
) -> None:
    """
    Create a new Python project.
    """
    output_dir = _resolve_output_path(project_name, output_dir)

    if output_dir.exists():
        console.print("Directory [bold]{}[/bold] already exist".format(output_dir), style="red")
        raise typer.Exit(1)

    generator = ProjectGenerator(
        name=project_name,
        profile=profile,
        output_dir=output_dir,
        variables=_parse_variables(variables or []),
        components=components or [],
    )

    with console.status("[bold green]Creating project.."):
        project_path = generator.create()

    console.print("Project created successfully at [bold green]{}[/bold green]".format(project_path))


@app.command()
def setup(
    skip_templates: bool = Option(False, "--skip-templates", help="Skip templates installation")
) -> None:
    if not skip_templates:
        repository = Repository()
        for source in TRUSTED_SOURCES:
            console.print("Installing templates from '{}'".format(source.repository))
            repository.install(source.https, branch=source.branch, type_=source.type)


@app.command()
def profiles() -> None:
    """
    List available profiles.
    """
    template_manager = TemplateManager()
    available_profiles = template_manager.list_profiles()

    table = Table(title="Available profiles")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="green")
    table.add_column("Version", style="yellow")

    for profile in available_profiles:
        table.add_row(profile.name, profile.description, profile.version)

    console.print(table)

@app.command()
def version() -> None:
    """
    Show version information.
    """
    console.print("Layra version is [bold green]{}[/bold green]".format(__version__))


if __name__ == "__main__":
    app()
