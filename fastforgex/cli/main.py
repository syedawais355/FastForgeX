"""CLI entry point for FastForgeX."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version
from pathlib import Path

import click

from fastforgex import __version__
from fastforgex.engine.config import ProjectConfig, validate_project_name
from fastforgex.engine.generator import generate
from fastforgex.engine.resolver import ResolutionError, resolve

CONTEXT_SETTINGS = {
    "help_option_names": ["-h", "--help"],
    "max_content_width": 100,
}

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


def _resolve_cli_version() -> str:
    """Return installed package version, with source fallback for local runs."""
    try:
        return package_version("fastforgex")
    except PackageNotFoundError:
        return __version__


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version=_resolve_cli_version(), prog_name="fastforgex")
def cli() -> None:
    """Generate production-ready FastAPI project scaffolds.

    \b
    Examples:
      fastforgex new
      fastforgex new myapi --preset api
      fastforgex new myapi --db sqlite --tests --lint
      fastforgex new myapi --db postgresql --docker --ci --makefile
    """


@cli.command(
    context_settings=CONTEXT_SETTINGS,
    short_help="Create a FastAPI project scaffold.",
)
@click.argument("project_name", required=False)
@click.option(
    "--db",
    type=click.Choice(["none", "sqlite", "postgresql"]),
    default=None,
    help="Database backend for non-interactive mode.",
)
@click.option(
    "--orm",
    type=click.Choice(["none", "sqlalchemy"]),
    default=None,
    help="ORM layer. Auto-set to 'sqlalchemy' when --db is sqlite or postgresql.",
)
@click.option(
    "--docker",
    is_flag=True,
    default=False,
    help="Include Dockerfile and runtime entrypoint.",
)
@click.option("--tests", is_flag=True, default=False, help="Include pytest test scaffold.")
@click.option(
    "--lint",
    is_flag=True,
    default=False,
    help="Include ruff, black, and pre-commit configuration.",
)
@click.option(
    "--ci",
    is_flag=True,
    default=False,
    help="Include GitHub Actions CI workflow.",
)
@click.option(
    "--makefile",
    is_flag=True,
    default=False,
    help="Include Makefile with common development targets.",
)
@click.option(
    "--preset",
    type=click.Choice(["minimal", "api", "full"]),
    default=None,
    help="Apply a predefined stack. Overrides individual feature flags.",
)
@click.option(
    "--output",
    "-o",
    default=".",
    show_default=True,
    help="Base directory where the new project folder will be created.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Print generated file list only. No files are written.",
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
    """Create a new FastAPI project.

    If PROJECT_NAME or --db is omitted, interactive prompts are shown.

    \b
    Examples:
      fastforgex new
      fastforgex new myapi --preset api
      fastforgex new myapi --db sqlite --tests --lint
      fastforgex new myapi --db postgresql --docker --ci --makefile
      fastforgex new myapi --db sqlite --dry-run
    """
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
