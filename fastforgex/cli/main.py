"""CLI entry point for FastForgeX."""

from __future__ import annotations

from pathlib import Path

import click

from fastforgex import __version__
from fastforgex.engine.config import ProjectConfig, validate_project_name
from fastforgex.engine.generator import generate
from fastforgex.engine.resolver import ResolutionError, resolve

PRESETS: dict[str, dict[str, object]] = {
    "minimal": {
        "db": "none",
        "orm": "none",
        "docker": False,
        "tests": True,
        "lint": True,
        "ci": False,
        "makefile": False,
    },
    "api": {
        "db": "postgresql",
        "orm": "sqlalchemy",
        "docker": True,
        "tests": True,
        "lint": True,
        "ci": True,
        "makefile": True,
    },
    "full": {
        "db": "postgresql",
        "orm": "sqlalchemy",
        "docker": True,
        "tests": True,
        "lint": True,
        "ci": True,
        "makefile": True,
    },
}


@click.group()
@click.version_option(__version__, prog_name="fastforgex")
def cli() -> None:
    """FastForgeX — FastAPI project scaffolding CLI.

    \b
    Quickstart:
      fastforgex new                          interactive mode
      fastforgex new myapi --preset api       postgresql + docker + ci
      fastforgex new myapi --db sqlite --tests --lint
    """


@cli.command()
@click.argument("project_name", required=False)
@click.option(
    "--db",
    type=click.Choice(["none", "sqlite", "postgresql"]),
    default=None,
    help="Database backend.",
)
@click.option(
    "--orm",
    type=click.Choice(["none", "sqlalchemy"]),
    default=None,
    help="ORM (auto-selected when DB is chosen).",
)
@click.option(
    "--docker",
    is_flag=True,
    default=False,
    help="Add Dockerfile and entrypoint.",
)
@click.option(
    "--tests", is_flag=True, default=False, help="Add pytest scaffold."
)
@click.option(
    "--lint",
    is_flag=True,
    default=False,
    help="Add ruff, black, and pre-commit config.",
)
@click.option(
    "--ci",
    is_flag=True,
    default=False,
    help="Add GitHub Actions CI workflow.",
)
@click.option(
    "--makefile",
    is_flag=True,
    default=False,
    help="Add Makefile with common targets.",
)
@click.option(
    "--preset",
    type=click.Choice(["minimal", "api", "full"]),
    default=None,
    help="Use a predefined configuration.",
)
@click.option(
    "--output",
    "-o",
    default=".",
    show_default=True,
    help="Directory to generate the project in.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would be generated without writing files.",
)
def new(
    project_name: str | None,
    db: str | None,
    orm: str | None,
    docker: bool,
    tests: bool,
    lint: bool,
    ci: bool,
    makefile: bool,
    preset: str | None,
    output: str,
    dry_run: bool,
) -> None:
    """Generate a new FastAPI project."""
    if preset:
        if not project_name:
            project_name = click.prompt("Project name")
        try:
            project_name = validate_project_name(project_name)
        except ValueError as exc:
            raise click.ClickException(str(exc)) from exc
        raw = ProjectConfig(project_name=project_name, **PRESETS[preset])  # type: ignore[arg-type]

    elif project_name and db is not None:
        try:
            project_name = validate_project_name(project_name)
        except ValueError as exc:
            raise click.ClickException(str(exc)) from exc
        raw = ProjectConfig(
            project_name=project_name,
            db=db,  # type: ignore[arg-type]
            orm=orm or "none",  # type: ignore[arg-type]
            docker=docker,
            tests=tests,
            lint=lint,
            ci=ci,
            makefile=makefile,
        )

    else:
        from fastforgex.cli.prompts import run_interactive
        raw = run_interactive(project_name)

    try:
        config = resolve(raw)
    except ResolutionError as exc:
        raise click.ClickException(str(exc)) from exc

    if dry_run:
        _print_dry_run(config)
        return

    out = Path(output).resolve()

    try:
        root = generate(config, out)
    except FileExistsError as exc:
        raise click.ClickException(
            f"Directory '{config.project_name}' already exists in {out}."
        ) from exc

    _print_success(config, root)


def _print_dry_run(config: ProjectConfig) -> None:
    click.echo(f"\nDry run for project '{config.project_name}':\n")
    files = _predict_files(config)
    for f in sorted(files):
        click.echo(f"  {f}")
    click.echo(f"\n{len(files)} files would be created.")


def _predict_files(config: ProjectConfig) -> list[str]:
    files = [
        "app/__init__.py",
        "app/api/__init__.py",
        "app/api/routes.py",
        "app/core/config.py",
        "app/core/exceptions.py",
        "app/core/logger.py",
        "app/services/__init__.py",
        "app/main.py",
        ".env.example",
        ".gitignore",
        "README.md",
        "requirements.txt",
    ]
    if config.use_db:
        files += [
            "app/db/__init__.py",
            "app/db/base.py",
            "app/db/models/__init__.py",
            "app/db/session.py",
            "alembic.ini",
            "alembic/env.py",
            "alembic/script.py.mako",
            "alembic/versions/.gitkeep",
        ]
    if config.docker:
        files += ["Dockerfile", ".dockerignore", "entrypoint.sh"]
        if config.db == "postgresql":
            files.append("docker-compose.yml")
    if config.tests:
        files += ["tests/__init__.py", "tests/conftest.py", "tests/test_health.py"]
    if config.lint:
        files += ["pyproject.toml", ".pre-commit-config.yaml"]
    if config.ci:
        files.append(".github/workflows/ci.yml")
    if config.makefile:
        files.append("Makefile")
    return files


def _print_success(config: ProjectConfig, root: Path) -> None:
    click.echo(f"\nProject '{config.project_name}' created at {root}\n")
    click.echo("Next steps:")
    click.echo(f"  cd {config.project_name}")
    click.echo("  python -m venv .venv")

    if click.get_current_context().info_name:
        click.echo("  source .venv/bin/activate   # Windows: .venv\\Scripts\\activate")

    click.echo("  pip install -r requirements.txt")
    click.echo("  cp .env.example .env")

    if config.use_db:
        click.echo("  # Edit .env and set DATABASE_URL")
        click.echo("  alembic upgrade head")

    click.echo("  uvicorn app.main:app --reload")

    if config.lint:
        click.echo("\n  pre-commit install          # optional: enable git hooks")
