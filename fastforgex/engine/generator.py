"""Project generation orchestrator — writes all files for a given config."""

from __future__ import annotations

from pathlib import Path

from fastforgex.engine.config import ProjectConfig
from fastforgex.engine.renderer import render
from fastforgex.engine.resolver import get_requirements


def generate(config: ProjectConfig, output_dir: Path) -> Path:
    """Generate a complete project at output_dir/project_name. Returns the project root."""
    root = output_dir / config.project_name
    root.mkdir(parents=True, exist_ok=False)

    v = config.to_template_vars()

    _write_base(root, v)

    if config.use_db:
        _write_db(root, v)

    if config.docker:
        _write_docker(root, v)

    if config.tests:
        _write_tests(root, v)

    if config.lint:
        _write_linting(root, v)

    if config.ci:
        _write_ci(root, v)

    if config.makefile:
        _write_makefile(root, v)

    _write_requirements(root, config)
    _write_env(root, config)
    _write_gitignore(root)
    _write_readme(root, v)

    return root


def _write_base(root: Path, v: dict[str, object]) -> None:
    app = root / "app"
    for d in ("api", "core", "services"):
        (app / d).mkdir(parents=True)

    _put(app / "__init__.py", "")
    _put(app / "api" / "__init__.py", "")
    _put(app / "services" / "__init__.py", "")
    _put(app / "main.py", render("base/main.py.j2", v))
    _put(app / "api" / "routes.py", render("base/routes.py.j2", v))
    _put(app / "core" / "config.py", render("base/config.py.j2", v))
    _put(app / "core" / "logger.py", render("base/logger.py.j2", v))
    _put(app / "core" / "exceptions.py", render("base/exceptions.py.j2", v))


def _write_db(root: Path, v: dict[str, object]) -> None:
    db_dir = root / "app" / "db"
    (db_dir / "models").mkdir(parents=True)

    _put(db_dir / "__init__.py", "")
    _put(db_dir / "models" / "__init__.py", "")
    _put(db_dir / "base.py", render("db/base.py.j2", v))
    _put(db_dir / "session.py", render("db/session.py.j2", v))

    alembic_dir = root / "alembic" / "versions"
    alembic_dir.mkdir(parents=True)
    _put(root / "alembic.ini", render("db/alembic.ini.j2", v))
    _put(root / "alembic" / "env.py", render("db/alembic_env.py.j2", v))
    _put(root / "alembic" / "script.py.mako", render("db/script.py.mako.j2", v))
    _put(root / "alembic" / "versions" / ".gitkeep", "")


def _write_docker(root: Path, v: dict[str, object]) -> None:
    _put(root / "Dockerfile", render("docker/Dockerfile.j2", v))
    _put(root / ".dockerignore", render("docker/dockerignore.j2", v))
    sh = root / "entrypoint.sh"
    _put(sh, render("docker/entrypoint.sh.j2", v))
    sh.chmod(0o755)
    if v.get("db") == "postgresql":
        _put(root / "docker-compose.yml", render("docker/docker-compose.yml.j2", v))


def _write_tests(root: Path, v: dict[str, object]) -> None:
    tests = root / "tests"
    tests.mkdir()
    _put(tests / "__init__.py", "")
    _put(tests / "conftest.py", render("tests/conftest.py.j2", v))
    _put(tests / "test_health.py", render("tests/test_health.py.j2", v))


def _write_linting(root: Path, v: dict[str, object]) -> None:
    _put(root / "pyproject.toml", render("linting/pyproject.toml.j2", v))
    _put(root / ".pre-commit-config.yaml", render("linting/pre-commit-config.yaml.j2", v))


def _write_ci(root: Path, v: dict[str, object]) -> None:
    gh = root / ".github" / "workflows"
    gh.mkdir(parents=True)
    _put(gh / "ci.yml", render("ci/ci.yml.j2", v))


def _write_makefile(root: Path, v: dict[str, object]) -> None:
    _put(root / "Makefile", render("makefile/Makefile.j2", v))


def _write_requirements(root: Path, config: ProjectConfig) -> None:
    _put(root / "requirements.txt", "\n".join(get_requirements(config)) + "\n")


def _write_env(root: Path, config: ProjectConfig) -> None:
    lines = [
        "# Application",
        "APP_ENV=development",
        "LOG_FORMAT=text",
        "",
    ]
    if config.db == "postgresql":
        lines += [
            "# Database",
            "DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname",
            "",
        ]
    elif config.db == "sqlite":
        lines += [
            "# Database",
            "DATABASE_URL=sqlite+aiosqlite:///./app.db",
            "",
        ]
    _put(root / ".env.example", "\n".join(lines))


def _write_gitignore(root: Path) -> None:
    _put(root / ".gitignore", _GITIGNORE)


def _write_readme(root: Path, v: dict[str, object]) -> None:
    _put(root / "README.md", render("base/README.md.j2", v))


def _put(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


_GITIGNORE = """\
__pycache__/
*.py[cod]
*.so
.env
.venv/
venv/
dist/
build/
*.egg-info/
.pytest_cache/
.ruff_cache/
.mypy_cache/
.DS_Store
*.db
*.sqlite3
"""
