"""
Runtime integration tests: generate every meaningful config and verify the output
compiles, contains the right content, and (for no-DB projects) passes pytest.
"""

from __future__ import annotations

import os
import py_compile
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from fastforgex.engine.config import ProjectConfig
from fastforgex.engine.generator import generate
from fastforgex.engine.resolver import resolve

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _gen(tmp_path: Path, **kwargs: Any) -> Path:
    config = resolve(ProjectConfig(project_name="proj", **kwargs))
    return generate(config, tmp_path)


def _assert_compiles(root: Path) -> None:
    """Every generated .py file must be syntactically valid."""
    for path in root.rglob("*.py"):
        if path.is_file():
            try:
                py_compile.compile(str(path), doraise=True)
            except py_compile.PyCompileError as exc:
                pytest.fail(f"Syntax error in {path.relative_to(root)}: {exc}")


# ---------------------------------------------------------------------------
# Parametrised compile + content tests across all meaningful config combos
# ---------------------------------------------------------------------------

CONFIGS: list[dict[str, Any]] = [
    {},
    {"tests": True},
    {"lint": True},
    {"tests": True, "lint": True},
    {"makefile": True},
    {"ci": True},
    {"tests": True, "lint": True, "docker": True, "ci": True, "makefile": True},
    {"db": "sqlite"},
    {"db": "sqlite", "tests": True},
    {"db": "sqlite", "tests": True, "lint": True},
    {"db": "sqlite", "docker": True},
    {"db": "sqlite", "tests": True, "lint": True, "docker": True, "ci": True, "makefile": True},
    {"db": "postgresql"},
    {"db": "postgresql", "tests": True, "lint": True},
    {"db": "postgresql", "docker": True},
    {"db": "postgresql", "tests": True, "lint": True, "docker": True, "ci": True, "makefile": True},
]

CONFIG_IDS = [
    "bare",
    "tests",
    "lint",
    "tests_lint",
    "makefile",
    "ci",
    "full_nodb",
    "sqlite",
    "sqlite_tests",
    "sqlite_tests_lint",
    "sqlite_docker",
    "sqlite_full",
    "pg",
    "pg_tests_lint",
    "pg_docker",
    "pg_full",
]


@pytest.fixture(params=CONFIGS, ids=CONFIG_IDS)
def generated_project(tmp_path: Path, request: pytest.FixtureRequest) -> Path:
    idx = CONFIGS.index(request.param)
    unique = tmp_path / CONFIG_IDS[idx]
    unique.mkdir()
    return _gen(unique, **request.param)


# ---------------------------------------------------------------------------
# Compile tests — all configs
# ---------------------------------------------------------------------------


def test_all_python_files_compile(generated_project: Path) -> None:
    _assert_compiles(generated_project)


# ---------------------------------------------------------------------------
# Base-file presence — all configs
# ---------------------------------------------------------------------------


def test_base_files_always_present(generated_project: Path) -> None:
    for rel in (
        "app/main.py",
        "app/api/routes.py",
        "app/core/config.py",
        "app/core/exceptions.py",
        "app/core/logger.py",
        "requirements.txt",
        ".env.example",
        ".gitignore",
        "README.md",
    ):
        assert (generated_project / rel).exists(), f"missing {rel}"


# ---------------------------------------------------------------------------
# pyproject.toml presence: only when tests OR lint
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "kwargs,expect",
    [
        ({}, False),
        ({"tests": True}, True),
        ({"lint": True}, True),
        ({"tests": True, "lint": True}, True),
        ({"makefile": True}, False),
        ({"docker": True}, False),
        ({"ci": True}, False),
    ],
)
def test_pyproject_presence(tmp_path: Path, kwargs: dict[str, Any], expect: bool) -> None:
    root = _gen(tmp_path, **kwargs)
    assert (root / "pyproject.toml").exists() is expect


# ---------------------------------------------------------------------------
# pyproject.toml content
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "kwargs,expected,absent",
    [
        (
            {"tests": True},
            ["[tool.pytest.ini_options]", "asyncio_mode"],
            ["[tool.ruff]", "[tool.black]"],
        ),
        (
            {"lint": True},
            ["[tool.ruff]", "[tool.black]", "[tool.mypy]"],
            ["[tool.pytest.ini_options]"],
        ),
        (
            {"tests": True, "lint": True},
            ["[tool.ruff]", "[tool.pytest.ini_options]", "asyncio_mode"],
            [],
        ),
    ],
)
def test_pyproject_content(
    tmp_path: Path,
    kwargs: dict[str, Any],
    expected: list[str],
    absent: list[str],
) -> None:
    root = _gen(tmp_path, **kwargs)
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    for token in expected:
        assert token in text, f"'{token}' missing from pyproject.toml for {kwargs}"
    for token in absent:
        assert token not in text, f"'{token}' should not be in pyproject.toml for {kwargs}"


# ---------------------------------------------------------------------------
# pre-commit: only with lint
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "kwargs,expect",
    [
        ({"lint": True}, True),
        ({"tests": True}, False),
        ({}, False),
    ],
)
def test_pre_commit_only_with_lint(tmp_path: Path, kwargs: dict[str, Any], expect: bool) -> None:
    root = _gen(tmp_path, **kwargs)
    assert (root / ".pre-commit-config.yaml").exists() is expect


# ---------------------------------------------------------------------------
# conftest.py uses pytest_asyncio (not plain pytest.fixture)
# ---------------------------------------------------------------------------


def test_conftest_uses_pytest_asyncio_fixture(tmp_path: Path) -> None:
    root = _gen(tmp_path, tests=True)
    src = (root / "tests" / "conftest.py").read_text(encoding="utf-8")
    assert "import pytest_asyncio" in src
    assert "@pytest_asyncio.fixture" in src
    assert "@pytest.fixture" not in src


# ---------------------------------------------------------------------------
# DB-related invariants
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "db,fragment",
    [("sqlite", "aiosqlite"), ("postgresql", "asyncpg")],
)
def test_env_example_db_url(tmp_path: Path, db: str, fragment: str) -> None:
    root = _gen(tmp_path, db=db)
    env = (root / ".env.example").read_text(encoding="utf-8")
    assert "DATABASE_URL" in env
    assert fragment in env


def test_docker_compose_only_for_postgresql_docker(tmp_path: Path) -> None:
    pg = _gen(tmp_path / "pg", db="postgresql", docker=True)
    sq = _gen(tmp_path / "sq", db="sqlite", docker=True)
    nd = _gen(tmp_path / "nd", docker=True)
    assert (pg / "docker-compose.yml").exists()
    assert not (sq / "docker-compose.yml").exists()
    assert not (nd / "docker-compose.yml").exists()


def test_no_db_folder_without_db(tmp_path: Path) -> None:
    root = _gen(tmp_path)
    assert not (root / "app" / "db").exists()
    assert not (root / "alembic.ini").exists()


def test_main_imports_close_db_only_with_db(tmp_path: Path) -> None:
    with_db = _gen(tmp_path / "with", db="sqlite")
    no_db = _gen(tmp_path / "without")
    assert "from app.db.session import close_db" in (with_db / "app/main.py").read_text()
    assert "close_db" not in (no_db / "app/main.py").read_text()


def test_config_has_database_url_only_with_db(tmp_path: Path) -> None:
    with_db = _gen(tmp_path / "with", db="sqlite")
    no_db = _gen(tmp_path / "without")
    assert "database_url" in (with_db / "app/core/config.py").read_text()
    assert "database_url" not in (no_db / "app/core/config.py").read_text()


# ---------------------------------------------------------------------------
# Docker invariants
# ---------------------------------------------------------------------------


def test_dockerfile_is_multistage(tmp_path: Path) -> None:
    root = _gen(tmp_path, docker=True)
    src = (root / "Dockerfile").read_text(encoding="utf-8")
    assert "AS builder" in src
    assert "HEALTHCHECK" in src
    assert "USER app" in src


def test_entrypoint_runs_alembic_only_with_db(tmp_path: Path) -> None:
    with_db = _gen(tmp_path / "with", db="sqlite", docker=True)
    no_db = _gen(tmp_path / "without", docker=True)
    assert "alembic upgrade head" in (with_db / "entrypoint.sh").read_text()
    assert "alembic" not in (no_db / "entrypoint.sh").read_text()


# ---------------------------------------------------------------------------
# CI invariants
# ---------------------------------------------------------------------------


def test_ci_has_postgres_service_only_for_postgresql(tmp_path: Path) -> None:
    pg = _gen(tmp_path / "pg", db="postgresql", ci=True)
    sq = _gen(tmp_path / "sq", db="sqlite", ci=True)
    assert "postgres:" in (pg / ".github/workflows/ci.yml").read_text()
    assert "postgres:" not in (sq / ".github/workflows/ci.yml").read_text()


def test_ci_lint_step_only_with_lint(tmp_path: Path) -> None:
    with_lint = _gen(tmp_path / "wl", ci=True, lint=True)
    no_lint = _gen(tmp_path / "nl", ci=True)
    assert "ruff check" in (with_lint / ".github/workflows/ci.yml").read_text()
    assert "ruff check" not in (no_lint / ".github/workflows/ci.yml").read_text()


def test_ci_db_env_var_set_for_sqlite(tmp_path: Path) -> None:
    root = _gen(tmp_path, db="sqlite", ci=True, tests=True)
    ci_text = (root / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "sqlite+aiosqlite" in ci_text


def test_ci_db_env_var_set_for_postgresql(tmp_path: Path) -> None:
    root = _gen(tmp_path, db="postgresql", ci=True, tests=True)
    ci_text = (root / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "postgresql+asyncpg" in ci_text


# ---------------------------------------------------------------------------
# Makefile invariants
# ---------------------------------------------------------------------------


def test_makefile_phony_includes_test_cov(tmp_path: Path) -> None:
    root = _gen(tmp_path, tests=True, makefile=True)
    first_line = (root / "Makefile").read_text(encoding="utf-8").splitlines()[0]
    assert "test-cov" in first_line


def test_makefile_phony_includes_migration_rollback(tmp_path: Path) -> None:
    root = _gen(tmp_path, db="sqlite", makefile=True)
    first_line = (root / "Makefile").read_text(encoding="utf-8").splitlines()[0]
    assert "migration" in first_line
    assert "rollback" in first_line


def test_makefile_down_only_for_postgresql_docker(tmp_path: Path) -> None:
    pg = _gen(tmp_path / "pg", db="postgresql", docker=True, makefile=True)
    nd = _gen(tmp_path / "nd", docker=True, makefile=True)
    assert "down:" in (pg / "Makefile").read_text()
    assert "down:" not in (nd / "Makefile").read_text()


def test_makefile_down_not_in_phony_without_postgresql(tmp_path: Path) -> None:
    root = _gen(tmp_path, docker=True, makefile=True)
    first_line = (root / "Makefile").read_text(encoding="utf-8").splitlines()[0]
    assert "down" not in first_line


# ---------------------------------------------------------------------------
# Requirements invariants
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "kwargs,tokens",
    [
        ({}, ["fastapi", "pydantic-settings", "uvicorn"]),
        ({"db": "sqlite"}, ["aiosqlite", "alembic", "sqlalchemy"]),
        ({"db": "postgresql"}, ["asyncpg", "alembic"]),
        ({"tests": True}, ["pytest", "httpx", "pytest-asyncio"]),
        ({"lint": True}, ["ruff", "black"]),
    ],
)
def test_requirements_content(tmp_path: Path, kwargs: dict[str, Any], tokens: list[str]) -> None:
    root = _gen(tmp_path, **kwargs)
    reqs = (root / "requirements.txt").read_text(encoding="utf-8")
    for token in tokens:
        assert token in reqs, f"'{token}' missing from requirements.txt for {kwargs}"


# ---------------------------------------------------------------------------
# Settings: project name embedded correctly
# ---------------------------------------------------------------------------


def test_project_name_in_settings(tmp_path: Path) -> None:
    root = _gen(tmp_path)
    config_src = (root / "app/core/config.py").read_text(encoding="utf-8")
    assert 'app_name: str = "proj"' in config_src


# ---------------------------------------------------------------------------
# Live pytest run — no-DB projects (all required deps exist in this env)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "kwargs",
    [
        {"tests": True},
        {"tests": True, "lint": True},
        {"tests": True, "docker": True},
        {"tests": True, "makefile": True},
        {"tests": True, "ci": True},
        {"tests": True, "lint": True, "docker": True, "ci": True, "makefile": True},
    ],
    ids=[
        "tests_only",
        "tests_lint",
        "tests_docker",
        "tests_makefile",
        "tests_ci",
        "tests_full_nodb",
    ],
)
@pytest.mark.skipif(
    sys.version_info < (3, 11),
    reason="Generated projects target Python 3.12 (uses datetime.UTC, list[str])",
)
def test_live_pytest_no_db(tmp_path: Path, kwargs: dict[str, Any]) -> None:
    """Generate a no-DB project and actually run its own test suite."""
    root = _gen(tmp_path, **kwargs)
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"],
        cwd=str(root),
        check=True,
        timeout=120,
    )
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
        cwd=str(root),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"pytest failed for {kwargs}\n"
        f"--- STDOUT ---\n{result.stdout}\n"
        f"--- STDERR ---\n{result.stderr}"
    )


# ---------------------------------------------------------------------------
# Live pytest run — SQLite (skip if sqlalchemy not installed)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "kwargs",
    [
        {"db": "sqlite", "tests": True},
        {"db": "sqlite", "tests": True, "lint": True},
    ],
    ids=["sqlite_tests", "sqlite_tests_lint"],
)
@pytest.mark.skipif(
    sys.version_info < (3, 11),
    reason="Generated projects target Python 3.12 (uses datetime.UTC, list[str])",
)
def test_live_pytest_sqlite(tmp_path: Path, kwargs: dict[str, Any]) -> None:
    """Generate a SQLite project and run its health test (no DB setup needed for /health)."""
    try:
        import aiosqlite  # noqa: F401
        import sqlalchemy  # noqa: F401
    except ImportError:
        pytest.skip("sqlalchemy/aiosqlite not installed in this environment")

    root = _gen(tmp_path, **kwargs)
    env = {
        **os.environ,
        "DATABASE_URL": "sqlite+aiosqlite:///./test.db",
        "APP_ENV": "test",
    }
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"],
        cwd=str(root),
        check=True,
        timeout=120,
        env=env,
    )
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
        cwd=str(root),
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
    )
    assert result.returncode == 0, (
        f"pytest failed for sqlite {kwargs}\n"
        f"--- STDOUT ---\n{result.stdout}\n"
        f"--- STDERR ---\n{result.stderr}"
    )
