"""Dependency resolution and pip requirements generation."""

from __future__ import annotations

from fastforgex.engine.config import ProjectConfig


class ResolutionError(Exception):
    """Raised when the selected module combination cannot be resolved."""


def resolve(config: ProjectConfig) -> ProjectConfig:
    """Validate and auto-complete module dependencies, returning a corrected config."""
    db = config.db
    orm = config.orm

    if orm != "none" and db == "none":
        raise ResolutionError(
            f"ORM '{orm}' requires a database. Use --db sqlite or --db postgresql."
        )

    if db != "none" and orm == "none":
        orm = "sqlalchemy"

    return ProjectConfig(
        project_name=config.project_name,
        db=db,
        orm=orm,
        docker=config.docker,
        tests=config.tests,
        lint=config.lint,
        ci=config.ci,
        makefile=config.makefile,
    )


def get_requirements(config: ProjectConfig) -> list[str]:
    """Return the ordered list of pip dependencies for the given config."""
    deps: list[str] = [
        "fastapi>=0.111.0",
        "pydantic-settings>=2.4.0",
        "uvicorn[standard]>=0.30.0",
    ]

    if config.db == "postgresql":
        deps += [
            "sqlalchemy[asyncio]>=2.0.30",
            "asyncpg>=0.29.0",
            "alembic>=1.13.0",
        ]
    elif config.db == "sqlite":
        deps += [
            "sqlalchemy[asyncio]>=2.0.30",
            "aiosqlite>=0.20.0",
            "alembic>=1.13.0",
        ]

    if config.tests:
        deps += [
            "pytest>=8.2.0",
            "pytest-asyncio>=0.23.0",
            "httpx>=0.27.0",
        ]

    if config.lint:
        deps += [
            "ruff>=0.5.0",
            "black>=24.4.0",
        ]

    return deps
