"""Interactive prompt flow using questionary."""

from __future__ import annotations

import questionary
from questionary import Style

from fastforgex.engine.config import ProjectConfig, validate_project_name

_STYLE = Style([
    ("qmark", "fg:#00d7af bold"),
    ("question", "bold"),
    ("answer", "fg:#00d7af bold"),
    ("pointer", "fg:#00d7af bold"),
    ("highlighted", "fg:#00d7af bold"),
    ("selected", "fg:#00d7af"),
    ("separator", "fg:#6c6c6c"),
])


def run_interactive(project_name: str | None = None) -> ProjectConfig:
    """Walk the user through all options interactively and return a ProjectConfig."""
    if not project_name:
        raw = questionary.text(
            "Project name:",
            validate=lambda v: _validate_name(v),
            style=_STYLE,
        ).ask()
        if raw is None:
            raise SystemExit(0)
        project_name = validate_project_name(raw)
    else:
        try:
            project_name = validate_project_name(project_name)
        except ValueError as exc:
            raise SystemExit(f"Error: {exc}") from exc

    db = questionary.select(
        "Database:",
        choices=["none", "sqlite", "postgresql"],
        default="none",
        style=_STYLE,
    ).ask()

    orm = "none"
    if db != "none":
        orm = questionary.select(
            "ORM:",
            choices=["sqlalchemy", "none"],
            default="sqlalchemy",
            style=_STYLE,
        ).ask()

    docker = questionary.confirm("Include Docker?", default=False, style=_STYLE).ask()
    tests = questionary.confirm("Include tests?", default=True, style=_STYLE).ask()
    lint = questionary.confirm("Include linting (ruff + black)?", default=True, style=_STYLE).ask()
    ci = questionary.confirm("Include GitHub Actions CI?", default=False, style=_STYLE).ask()
    makefile = questionary.confirm("Include Makefile?", default=False, style=_STYLE).ask()

    questionary.print("\nConfiguration:", style="bold")
    questionary.print(f"  Project  : {project_name}")
    questionary.print(f"  Database : {db}")
    questionary.print(f"  ORM      : {orm}")
    questionary.print(f"  Docker   : {docker}")
    questionary.print(f"  Tests    : {tests}")
    questionary.print(f"  Lint     : {lint}")
    questionary.print(f"  CI       : {ci}")
    questionary.print(f"  Makefile : {makefile}")

    confirmed = questionary.confirm("\nGenerate project?", default=True, style=_STYLE).ask()
    if not confirmed:
        raise SystemExit(0)

    return ProjectConfig(
        project_name=project_name,
        db=db,
        orm=orm,
        docker=docker,
        tests=tests,
        lint=lint,
        ci=ci,
        makefile=makefile,
    )


def _validate_name(value: str) -> bool | str:
    if not value.strip():
        return "Project name cannot be empty."
    try:
        validate_project_name(value)
        return True
    except ValueError as exc:
        return str(exc)
