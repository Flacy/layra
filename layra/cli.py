from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from typer import Typer, Argument, Option

from layra import __version__
from layra.core.generator import ProjectGenerator
from layra.core.templates import TemplateManager

app = Typer(
    name="layra",
    help="build smarter, start faster",
    rich_markup_mode="rich",
)
console = Console()


@app.command()
def new(
    project_name: str = Argument(..., help="Name of the project to create"),
    profile: str = Option("web-api", "--profile", "-p", help="Project profile"),
    output_dir: Path | None = Option(None, "--output", "-o", help="Output directory"),
) -> None:
    """
    Create a new Python project.
    """
    generator = ProjectGenerator()

    if output_dir is None:
        output_dir = Path.cwd() / project_name
    else:
        output_dir = output_dir / project_name

    if output_dir.exists():
        console.print("Directory [bold]{}[/bold] already exist".format(output_dir), style="red")
        raise typer.Exit(1)

    with console.status("[bold green]Creating project.."):
        project_path = generator.create_project(
            name=project_name,
            profile=profile,
            output_dir=output_dir,
        )

    console.print("Project created successfully at [bold green]{}[/bold green]".format(project_path))


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
