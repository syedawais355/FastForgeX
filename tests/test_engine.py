"""Tests for the FastForgeX generation engine."""

from __future__ import annotations

import pytest

from fastforgex.engine.config import ProjectConfig, validate_project_name
from fastforgex.engine.resolver import ResolutionError, get_requirements, resolve


def test_validate_name_clean() -> None:
    assert validate_project_name("myapi") == "myapi"


def test_validate_name_converts_hyphens() -> None:
    assert validate_project_name("my-api") == "my_api"


def test_validate_name_rejects_leading_digit() -> None:
    with pytest.raises(ValueError, match="not a valid project name"):
        validate_project_name("1api")


def test_validate_name_rejects_spaces_after_clean() -> None:
    with pytest.raises(ValueError, match="not a valid project name"):
        validate_project_name("my api!")


def test_resolve_adds_orm_when_db_selected() -> None:
    config = ProjectConfig(project_name="myapi", db="sqlite", orm="none")
    resolved = resolve(config)
    assert resolved.orm == "sqlalchemy"


def test_resolve_raises_when_orm_without_db() -> None:
    config = ProjectConfig(project_name="myapi", db="none", orm="sqlalchemy")
    with pytest.raises(ResolutionError, match="requires a database"):
        resolve(config)


def test_resolve_passthrough_when_valid() -> None:
    config = ProjectConfig(project_name="myapi", db="postgresql", orm="sqlalchemy")
    resolved = resolve(config)
    assert resolved.db == "postgresql"
    assert resolved.orm == "sqlalchemy"


def test_use_db_flag() -> None:
    assert ProjectConfig(project_name="x", db="sqlite").use_db is True
    assert ProjectConfig(project_name="x", db="none").use_db is False


def test_requirements_base() -> None:
    reqs = get_requirements(ProjectConfig(project_name="x"))
    assert any("fastapi" in r for r in reqs)
    assert any("uvicorn" in r for r in reqs)
    assert any("pydantic-settings" in r for r in reqs)


def test_requirements_postgresql() -> None:
    config = ProjectConfig(project_name="x", db="postgresql", orm="sqlalchemy")
    reqs = get_requirements(config)
    assert any("asyncpg" in r for r in reqs)
    assert any("alembic" in r for r in reqs)


def test_requirements_sqlite() -> None:
    reqs = get_requirements(ProjectConfig(project_name="x", db="sqlite", orm="sqlalchemy"))
    assert any("aiosqlite" in r for r in reqs)
    assert any("alembic" in r for r in reqs)


def test_requirements_tests() -> None:
    reqs = get_requirements(ProjectConfig(project_name="x", tests=True))
    assert any("pytest" in r for r in reqs)
    assert any("httpx" in r for r in reqs)


def test_requirements_lint() -> None:
    reqs = get_requirements(ProjectConfig(project_name="x", lint=True))
    assert any("ruff" in r for r in reqs)
    assert any("black" in r for r in reqs)


def test_template_vars_complete() -> None:
    config = ProjectConfig(project_name="x", db="sqlite", docker=True, tests=True, lint=True)
    v = config.to_template_vars()
    for key in ("project_name", "db", "orm", "docker", "tests", "lint", "use_db", "ci", "makefile"):
        assert key in v
