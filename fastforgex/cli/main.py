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

_CLI_HELP = """\
FastForgeX generates production-ready FastAPI projects in seconds.

\b
MODES
  interactive   Run `fastforgex new` (no flags) for a guided prompt wizard.
  preset        Use --preset for a one-shot stack with sensible defaults.
  explicit      Pass --db and any combination of flags for full control.

\b
QUICK EXAMPLES
  fastforgex new                              # interactive wizard
  fastforgex new myapi --preset api           # PostgreSQL + tests + lint + CI
  fastforgex new myapi --preset full          # above + Docker
  fastforgex new myapi --db sqlite --tests    # custom: SQLite + pytest
  fastforgex new myapi --preset full --dry-run  # preview files, nothing written
"""

_NEW_HELP = """\
Bootstrap a new FastAPI project scaffold.

\b
MODES — three ways to invoke this command:
  1. INTERACTIVE   fastforgex new
                   Guided prompt wizard; ideal for exploring options.
  2. PRESET        fastforgex new <name> --preset [minimal|api|full]
                   One-shot curated stack, no individual flags needed.
  3. EXPLICIT      fastforgex new <name> --db <engine> [flags...]
                   Full control. --db is always required in this mode.

\b
PRESETS
  minimal   no DB · tests · lint                                    (17 files)
  api       PostgreSQL · SQLAlchemy · tests · lint · CI · Makefile  (27 files)
  full      api preset + Docker + docker-compose                    (31 files)

\b
EXAMPLES
  fastforgex new myapi --preset full
  fastforgex new myapi --preset full --dry-run
  fastforgex new myapi --preset full -o ~/projects
  fastforgex new myapi --db postgresql --docker --tests --lint --ci --makefile
  fastforgex new myapi --db sqlite --tests --lint
  fastforgex new myapi --db none --tests --lint
"""

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
        "docker": False,
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
    try:
        return package_version("fastforgex")
    except PackageNotFoundError:
        return __version__


@click.group(context_settings=CONTEXT_SETTINGS, help=_CLI_HELP)
@click.version_option(version=_resolve_cli_version(), prog_name="fastforgex")
def cli() -> None:
    pass


@cli.command(
    context_settings=CONTEXT_SETTINGS,
    short_help="Scaffold a new FastAPI project.",
    help=_NEW_HELP,
)
@click.argument("project_name", required=False, metavar="PROJECT_NAME")
@click.option(
    "--db",
    type=click.Choice(["none", "sqlite", "postgresql"]),
    default=None,
    help=(
        "Database engine.  none = no DB layer,  sqlite = lightweight local DB,"
        "  postgresql = production-grade async Postgres."
        " SQLAlchemy + Alembic are added automatically when a DB is chosen."
    ),
)
@click.option(
    "--orm",
    type=click.Choice(["none", "sqlalchemy"]),
    default=None,
    help=(
        "ORM layer. Automatically set to 'sqlalchemy' when --db is sqlite or postgresql."
        " Only override this if you want to skip the ORM despite having a DB."
    ),
)
@click.option(
    "--docker",
    is_flag=True,
    default=False,
    help=(
        "Add Docker support: multi-stage Dockerfile, .dockerignore, and entrypoint.sh."
        " docker-compose.yml is also generated for PostgreSQL projects."
    ),
)
@click.option(
    "--tests",
    is_flag=True,
    default=False,
    help=(
        "Add a pytest suite with an async HTTP client fixture (httpx + pytest-asyncio)."
        " Includes tests/conftest.py and a health-endpoint smoke test."
    ),
)
@click.option(
    "--lint",
    is_flag=True,
    default=False,
    help=(
        "Add code-quality tooling: Ruff (linting), Black (formatting), mypy (types),"
        " and a pre-commit config. Also generates pyproject.toml with tool settings."
    ),
)
@click.option(
    "--ci",
    is_flag=True,
    default=False,
    help=(
        "Add a GitHub Actions CI workflow (.github/workflows/ci.yml)."
        " Runs lint, type-check, and tests. Includes a Postgres service for pg projects."
    ),
)
@click.option(
    "--makefile",
    is_flag=True,
    default=False,
    help=(
        "Add a Makefile with shortcuts: install, run, test, test-cov, lint, format,"
        " migrate, migration, rollback, build, up, down, and a formatted help target."
    ),
)
@click.option(
    "--preset",
    type=click.Choice(["minimal", "api", "full"]),
    default=None,
    help=(
        "Apply a curated stack: minimal (no DB + tests + lint), "
        "api (PostgreSQL + SQLAlchemy + tests + lint + CI + Makefile), "
        "full (api + Docker + docker-compose). Overrides all individual flags."
    ),
)
@click.option(
    "--output",
    "-o",
    default=".",
    show_default=True,
    help="Directory where the project folder will be created. Defaults to current directory.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Print the list of files that would be created without writing anything to disk.",
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
    """Bootstrap a new FastAPI project with best practices."""
    if preset:
        if not project_name:
            project_name = click.prompt("Project name")
        assert isinstance(project_name, str)
        try:
            project_name = validate_project_name(project_name)
        except ValueError as exc:
            raise click.ClickException(str(exc)) from exc
        raw = ProjectConfig(project_name=project_name, **PRESETS[preset])  # type: ignore[arg-type]

    elif project_name is not None and db is not None:
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

    elif orm is not None and orm != "none" and db is None:
        raise click.ClickException("--orm requires --db. Use --db sqlite or --db postgresql.")

    elif project_name is not None and db is None and any([docker, tests, lint, ci, makefile]):
        raise click.ClickException(
            "Specify --db (or use --preset) when providing flags in non-interactive mode."
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
    if config.tests or config.lint:
        files.append("pyproject.toml")
    if config.lint:
        files.append(".pre-commit-config.yaml")
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
    click.echo("  source .venv/bin/activate   # Windows: .venv\\Scripts\\activate")
    click.echo("  pip install -r requirements.txt")
    click.echo("  cp .env.example .env")
    if config.use_db:
        click.echo("  # Edit .env with your DATABASE_URL")
        click.echo("  alembic upgrade head")
    click.echo("  uvicorn app.main:app --reload")
    if config.lint:
        click.echo("  pre-commit install")
