"""Integration tests for the project file generator."""

from __future__ import annotations

from pathlib import Path

import pytest

from fastforgex.engine.config import ProjectConfig
from fastforgex.engine.generator import generate
from fastforgex.engine.resolver import resolve


def _gen(tmp_path: Path, **kwargs: object) -> Path:
    config = resolve(ProjectConfig(project_name="testproject", **kwargs))  # type: ignore[arg-type]
    return generate(config, tmp_path)


def test_base_files_always_created(tmp_path: Path) -> None:
    root = _gen(tmp_path)
    for rel in (
        "app/main.py",
        "app/api/routes.py",
        "app/core/config.py",
        "app/core/logger.py",
        "app/core/exceptions.py",
        "requirements.txt",
        ".env.example",
        ".gitignore",
        "README.md",
    ):
        assert (root / rel).exists(), f"missing: {rel}"


def test_no_db_folder_without_db(tmp_path: Path) -> None:
    root = _gen(tmp_path)
    assert not (root / "app" / "db").exists()
    assert not (root / "alembic.ini").exists()


def test_db_files_created_sqlite(tmp_path: Path) -> None:
    root = _gen(tmp_path, db="sqlite")
    assert (root / "app" / "db" / "session.py").exists()
    assert (root / "app" / "db" / "base.py").exists()
    assert (root / "alembic.ini").exists()
    assert (root / "alembic" / "env.py").exists()
    assert (root / "alembic" / "script.py.mako").exists()


def test_db_files_created_postgresql(tmp_path: Path) -> None:
    root = _gen(tmp_path, db="postgresql")
    assert (root / "alembic.ini").exists()


def test_docker_files_created(tmp_path: Path) -> None:
    root = _gen(tmp_path, docker=True)
    assert (root / "Dockerfile").exists()
    assert (root / ".dockerignore").exists()
    assert (root / "entrypoint.sh").exists()


def test_compose_only_for_postgresql(tmp_path: Path) -> None:
    root_pg = _gen(tmp_path / "pg", db="postgresql", docker=True)
    assert (root_pg / "docker-compose.yml").exists()

    root_sq = _gen(tmp_path / "sq", db="sqlite", docker=True)
    assert not (root_sq / "docker-compose.yml").exists()


def test_no_docker_by_default(tmp_path: Path) -> None:
    root = _gen(tmp_path)
    assert not (root / "Dockerfile").exists()


def test_tests_scaffold_created(tmp_path: Path) -> None:
    root = _gen(tmp_path, tests=True)
    assert (root / "tests" / "conftest.py").exists()
    assert (root / "tests" / "test_health.py").exists()


def test_lint_config_created(tmp_path: Path) -> None:
    root = _gen(tmp_path, lint=True)
    assert (root / "pyproject.toml").exists()
    assert (root / ".pre-commit-config.yaml").exists()


def test_ci_workflow_created(tmp_path: Path) -> None:
    root = _gen(tmp_path, ci=True)
    assert (root / ".github" / "workflows" / "ci.yml").exists()


def test_makefile_created(tmp_path: Path) -> None:
    root = _gen(tmp_path, makefile=True)
    assert (root / "Makefile").exists()


def test_duplicate_raises(tmp_path: Path) -> None:
    _gen(tmp_path)
    with pytest.raises(FileExistsError):
        _gen(tmp_path)


def test_env_example_has_database_url_postgresql(tmp_path: Path) -> None:
    root = _gen(tmp_path, db="postgresql")
    env = (root / ".env.example").read_text()
    assert "DATABASE_URL" in env
    assert "asyncpg" in env


def test_env_example_has_database_url_sqlite(tmp_path: Path) -> None:
    root = _gen(tmp_path, db="sqlite")
    env = (root / ".env.example").read_text()
    assert "DATABASE_URL" in env
    assert "aiosqlite" in env


def test_requirements_asyncpg_for_postgresql(tmp_path: Path) -> None:
    root = _gen(tmp_path, db="postgresql")
    reqs = (root / "requirements.txt").read_text()
    assert "asyncpg" in reqs
    assert "alembic" in reqs


def test_entrypoint_executable(tmp_path: Path) -> None:
    root = _gen(tmp_path, docker=True)
    sh = root / "entrypoint.sh"
    assert sh.stat().st_mode & 0o111
