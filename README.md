# FastForgeX

[![PyPI version](https://img.shields.io/pypi/v/fastforgex.svg?logo=python&logoColor=white)](https://pypi.org/project/fastforgex/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**FastAPI project scaffolding CLI.**
Generate a complete, production-ready FastAPI backend in seconds. Pick your database, ORM, Docker, tests, linting, CI, and Makefile. Every generated file is fully typed, immediately runnable, and requires zero modification after generation.

```
pip install fastforgex
fastforgex new
```

---

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Quickstart](#quickstart)
- [Usage](#usage)
  - [Interactive Mode](#interactive-mode)
  - [Flag Mode](#flag-mode)
  - [Preset Mode](#preset-mode)
  - [Dry Run](#dry-run)
- [All Options](#all-options)
- [Presets](#presets)
- [Generation Flow](#generation-flow)
- [Generated Project](#generated-project)
  - [File Structure](#file-structure)
  - [What Each File Contains](#what-each-file-contains)
  - [Dependency Map](#dependency-map)
- [Platform Guide](#platform-guide)
  - [macOS](#macos)
  - [Linux](#linux)
  - [Windows](#windows)
- [After Generation](#after-generation)
- [License](#license)

---

## Requirements

| Requirement | Version |
|---|---|
| Python | 3.12 or higher |
| pip | any recent version |
| Docker (optional) | 24+ |

---

## Installation

```bash
pip install fastforgex
```

Verify the install:

```bash
fastforgex --version
```

To upgrade to a newer version later:

```bash
pip install --upgrade fastforgex
```

---

## Quickstart

The fastest way to get a working FastAPI project:

```bash
fastforgex new myapi --db postgresql --docker --tests --lint --ci --makefile
cd myapi
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs`.

---

## Usage

FastForgeX has three modes: interactive, flag-based, and preset.

### Interactive Mode

```bash
fastforgex new
```

Walks through each option with styled prompts. Displays a configuration summary before writing any files.

```
? Project name:                    myapi
? Database:                        postgresql
? ORM:                             sqlalchemy
? Include Docker?                  Yes
? Include tests?                   Yes
? Include linting (ruff + black)?  Yes
? Include GitHub Actions CI?       Yes
? Include Makefile?                Yes

Configuration:
  Project  : myapi
  Database : postgresql
  ORM      : sqlalchemy
  Docker   : True
  Tests    : True
  Lint     : True
  CI       : True
  Makefile : True

? Generate project? Yes
```

You can also pass just the project name and let the rest be interactive:

```bash
fastforgex new myapi
```

---

### Flag Mode

Pass all options directly. No prompts are shown.

```bash
# PostgreSQL + Docker + tests + lint
fastforgex new myapi --db postgresql --docker --tests --lint

# SQLite + tests only
fastforgex new myapi --db sqlite --tests

# Everything enabled
fastforgex new myapi --db postgresql --docker --tests --lint --ci --makefile

# Generate into a specific directory
fastforgex new myapi --db sqlite --tests --output /path/to/projects
```

---

### Preset Mode

Use a preset to skip selecting individual options:

```bash
fastforgex new myapi --preset minimal
fastforgex new myapi --preset api
fastforgex new myapi --preset full
```

See [Presets](#presets) for what each preset includes.

---

### Dry Run

Preview every file that would be created without writing anything to disk:

```bash
fastforgex new myapi --db postgresql --docker --tests --lint --dry-run
```

Output:

```
Dry run for project 'myapi':

  .env.example
  .gitignore
  .github/workflows/ci.yml
  .pre-commit-config.yaml
  Dockerfile
  .dockerignore
  docker-compose.yml
  entrypoint.sh
  app/__init__.py
  app/api/__init__.py
  app/api/routes.py
  app/core/config.py
  app/core/exceptions.py
  app/core/logger.py
  app/db/__init__.py
  app/db/base.py
  app/db/models/__init__.py
  app/db/session.py
  app/main.py
  app/services/__init__.py
  alembic.ini
  alembic/env.py
  alembic/script.py.mako
  alembic/versions/.gitkeep
  pyproject.toml
  requirements.txt
  tests/__init__.py
  tests/conftest.py
  tests/test_health.py
  README.md

30 files would be created.
```

---

## All Options

```
fastforgex new [PROJECT_NAME] [OPTIONS]
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `PROJECT_NAME` | argument | prompted | Name of the project folder. Hyphens are converted to underscores. Must start with a letter. |
| `--db` | `none` / `sqlite` / `postgresql` | `none` | Database backend. SQLAlchemy is automatically added when any DB is selected. |
| `--orm` | `none` / `sqlalchemy` | auto | ORM layer. Defaults to `sqlalchemy` when `--db` is set. Explicitly passing `none` with a database raises an error. |
| `--docker` | flag | off | Adds `Dockerfile`, `.dockerignore`, `entrypoint.sh`. Adds `docker-compose.yml` for PostgreSQL. |
| `--tests` | flag | off | Adds `tests/` with `conftest.py` and `test_health.py`. |
| `--lint` | flag | off | Adds `pyproject.toml` with ruff, black, and mypy config. Adds `.pre-commit-config.yaml`. |
| `--ci` | flag | off | Adds `.github/workflows/ci.yml`. Includes a PostgreSQL service container when DB is PostgreSQL. |
| `--makefile` | flag | off | Adds `Makefile` with targets for run, test, lint, migrate, build, up, down. |
| `--preset` | `minimal` / `api` / `full` | none | Use a predefined stack. Overrides individual flags. |
| `--output` / `-o` | path | `.` | Directory to generate the project in. |
| `--dry-run` | flag | off | Print all files that would be created. Write nothing. |

---

## Presets

| Option | `minimal` | `api` | `full` |
|--------|-----------|-------|--------|
| Database | none | postgresql | postgresql |
| ORM | none | sqlalchemy | sqlalchemy |
| Docker | no | yes | yes |
| Tests | yes | yes | yes |
| Lint | yes | yes | yes |
| CI | no | yes | yes |
| Makefile | no | yes | yes |

```bash
fastforgex new myapi --preset minimal    # lightweight, no DB, no Docker
fastforgex new myapi --preset api        # full production stack
fastforgex new myapi --preset full       # same as api
```

---

## Generation Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     fastforgex new                           │
└────────────────────────┬────────────────────────────────────┘
                         │
             ┌───────────▼───────────┐
             │   Parse input mode    │
             └───────────┬───────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
┌───────▼──────┐ ┌───────▼──────┐ ┌──────▼───────┐
│  Flag mode   │ │ Preset mode  │ │ Interactive  │
│  (all flags  │ │  (--preset)  │ │    mode      │
│  provided)   │ │              │ │  (prompts)   │
└───────┬──────┘ └───────┬──────┘ └──────┬───────┘
        └────────────────┼────────────────┘
                         │
             ┌───────────▼───────────┐
             │   Validate project    │
             │   name (hyphens →     │
             │   underscores, must   │
             │   start with letter)  │
             └───────────┬───────────┘
                         │
             ┌───────────▼───────────┐
             │  Dependency resolver  │
             │  DB selected + no ORM │
             │  → auto-add SQLAlchemy│
             │  ORM + no DB → error  │
             └───────────┬───────────┘
                         │
             ┌───────────▼───────────┐
             │     --dry-run?        │
             │  Yes → print files,   │
             │  exit without writing │
             └───────────┬───────────┘
                         │ No
             ┌───────────▼───────────┐
             │   Render Jinja2       │
             │   templates with      │
             │   ProjectConfig vars  │
             └───────────┬───────────┘
                         │
             ┌───────────▼───────────┐
             │   Write all files     │
             │   to output dir       │
             └───────────┬───────────┘
                         │
             ┌───────────▼───────────┐
             │  Print next steps     │
             └───────────────────────┘
```

---

## Generated Project

### File Structure

The structure below shows every possible file. Only the files relevant to your selected options are created.

```
myapi/
│
├── app/                          always generated
│   ├── __init__.py
│   ├── main.py                   FastAPI app, lifespan, CORS, exception handlers
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py             /health endpoint with typed response
│   ├── core/
│   │   ├── config.py             pydantic-settings, reads .env
│   │   ├── exceptions.py         AppError, NotFoundError, UnauthorizedError
│   │   └── logger.py             structured logging (JSON or text)
│   ├── db/                       only with --db
│   │   ├── __init__.py
│   │   ├── base.py               SQLAlchemy DeclarativeBase
│   │   ├── session.py            async engine, get_db dependency
│   │   └── models/
│   │       └── __init__.py
│   └── services/
│       └── __init__.py
│
├── alembic/                      only with --db
│   ├── env.py                    async Alembic env wired to settings
│   ├── script.py.mako            migration template
│   └── versions/
│       └── .gitkeep
│
├── tests/                        only with --tests
│   ├── __init__.py
│   ├── conftest.py               AsyncClient fixture (httpx + ASGI)
│   └── test_health.py            health endpoint test
│
├── .github/
│   └── workflows/
│       └── ci.yml                only with --ci
│
├── Dockerfile                    only with --docker
├── .dockerignore                 only with --docker
├── entrypoint.sh                 only with --docker
├── docker-compose.yml            only with --docker + --db postgresql
│
├── Makefile                      only with --makefile
├── pyproject.toml                only with --lint (ruff, black, mypy, pytest)
├── .pre-commit-config.yaml       only with --lint
├── alembic.ini                   only with --db
│
├── requirements.txt              always generated
├── .env.example                  always generated
├── .gitignore                    always generated
└── README.md                     always generated
```

---

### What Each File Contains

#### `app/main.py`

FastAPI application instance with:
- Lifespan context manager (startup + shutdown handlers)
- `init_db()` called on startup when DB is selected
- `close_db()` called on shutdown to dispose the connection pool
- CORS middleware with `cors_origins` from config
- Global handler for `AppError` — returns structured JSON with the correct HTTP status code
- Global handler for all unhandled exceptions — logs the error, returns `500`
- Swagger docs disabled automatically when `APP_ENV=production`

#### `app/core/config.py`

`pydantic-settings` `BaseSettings` class that reads from `.env`. Only includes `DATABASE_URL` when a database is selected. Fails loudly at startup if a required variable is missing.

| Variable | Default | Description |
|---|---|---|
| `APP_ENV` | `development` | `development`, `production`, or `test` |
| `LOG_FORMAT` | `text` | `text` for colored dev output, `json` for structured production logs |
| `CORS_ORIGINS` | `["*"]` | List of allowed CORS origins |
| `DATABASE_URL` | required | Only present when `--db` is used |

#### `app/core/exceptions.py`

Base exception hierarchy wired to the global handler in `main.py`. Raise these anywhere in your service layer — they are caught automatically.

```
AppError (status_code=400)
├── NotFoundError (status_code=404)
└── UnauthorizedError (status_code=401)
```

#### `app/core/logger.py`

Structured logger built on Python's standard `logging`. Returns a per-module logger via `get_logger(__name__)`. Format is controlled by `LOG_FORMAT`:

- `text` — formatted timestamp, level, module name, message (development)
- `json` — structured JSON payload with level, logger, message, and optional exc_info (production)

#### `app/db/session.py` (with `--db`)

Lazy async SQLAlchemy engine with:
- `init_db()` — creates all tables on startup (development convenience)
- `close_db()` — disposes the connection pool on shutdown
- `get_db()` — FastAPI dependency yielding an `AsyncSession` per request
- PostgreSQL: `pool_size=10`, `max_overflow=20`

#### `alembic/env.py` (with `--db`)

Fully async Alembic environment. Reads `DATABASE_URL` from `settings`. Ready to use immediately:

```bash
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

#### `Dockerfile` (with `--docker`)

Multi-stage build:
1. `builder` stage — installs dependencies into `/install`
2. Runtime stage — copies installed packages, runs as non-root `app` user
3. Docker `HEALTHCHECK` polling `/health` every 30 seconds

#### `entrypoint.sh` (with `--docker`)

Runs `alembic upgrade head` before starting uvicorn when a database is selected. This ensures migrations are always applied before the server accepts traffic.

#### `docker-compose.yml` (with `--docker` + `--db postgresql`)

Two services:
- `db` — `postgres:16-alpine` with a `pg_isready` health check
- `app` — built from `Dockerfile`, starts only after `db` is healthy

#### `.github/workflows/ci.yml` (with `--ci`)

Runs on every push and pull request to `main`:
1. Set up Python 3.12
2. Install dependencies
3. Run `ruff check .` and `black --check .` (if lint is enabled)
4. Run `pytest` (if tests are enabled)
5. Starts a PostgreSQL 16 service container when DB is PostgreSQL

#### Repository release automation

This repository includes additional root workflows:
- `.github/workflows/publish.yml`: publishes to PyPI when a GitHub Release is published.
- `.github/workflows/notify-main.yml`: sends an email on every push to `main`.

`publish.yml` also validates that:
1. Release tag matches `pyproject.toml` version (`vX.Y.Z`).
2. Release commit equals current `main` HEAD.
3. `pyproject.toml` version is not already present on PyPI.
4. Built wheel metadata version matches `fastforgex --version`.
5. Built wheel package files exactly match repository `fastforgex/` source files.
6. If a version is already published, the workflow skips upload and exits successfully (idempotent release runs).

`ci.yml` also enforces that any PR changing files under `fastforgex/` must bump `project.version` in `pyproject.toml`.

Recommended release flow:
1. Merge all changes to `main`.
2. Bump `version` in `pyproject.toml` and update `CHANGELOG.md`.
3. Create and push tag `vX.Y.Z` from `main`.
4. Publish a GitHub Release for that tag.

Required GitHub repository secrets for notifications:
- `SMTP_SERVER`
- `SMTP_PORT` (optional, defaults to `587`)
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `NOTIFY_EMAIL_TO`

Required GitHub repository secret for publishing:
- `PYPI_API_TOKEN`

#### `Makefile` (with `--makefile`)

| Target | Command | Notes |
|--------|---------|-------|
| `make install` | `pip install -r requirements.txt` | always |
| `make run` | `uvicorn app.main:app --reload` | always |
| `make test` | `pytest` | with `--tests` |
| `make test-cov` | `pytest --cov=app` | with `--tests` |
| `make lint` | `ruff check . && black --check .` | with `--lint` |
| `make format` | `ruff check . --fix && black .` | with `--lint` |
| `make migrate` | `alembic upgrade head` | with `--db` |
| `make migration name=...` | `alembic revision --autogenerate` | with `--db` |
| `make rollback` | `alembic downgrade -1` | with `--db` |
| `make build` | `docker build -t <name> .` | with `--docker` |
| `make up` | `docker compose up -d` | with `--docker` + postgresql |
| `make down` | `docker compose down` | with `--docker` + postgresql |
| `make help` | prints all targets | always |

---

### Dependency Map

This table shows what gets added to `requirements.txt` based on your selections.

```
Base (always)
  fastapi>=0.111.0
  pydantic-settings>=2.3.0
  uvicorn[standard]>=0.30.0

--db postgresql
  sqlalchemy[asyncio]>=2.0.30
  asyncpg>=0.29.0
  alembic>=1.13.0

--db sqlite
  sqlalchemy[asyncio]>=2.0.30
  aiosqlite>=0.20.0
  alembic>=1.13.0

--tests
  pytest>=8.2.0
  pytest-asyncio>=0.23.0
  httpx>=0.27.0

--lint
  ruff>=0.5.0
  black>=24.4.0
```

---

## Platform Guide

### macOS

Install Python 3.12 via Homebrew if you do not already have it:

```bash
brew install python@3.12
```

Install FastForgeX:

```bash
pip3 install fastforgex
```

Create a project and run it:

```bash
fastforgex new myapi --db postgresql --docker --tests --lint
cd myapi
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

With Makefile:

```bash
make install
make run
```

---

### Linux

Install Python 3.12:

```bash
# Ubuntu / Debian
sudo apt update
sudo apt install python3.12 python3.12-venv python3-pip

# Fedora / RHEL
sudo dnf install python3.12
```

Install FastForgeX:

```bash
pip3 install fastforgex
```

Create a project and run it:

```bash
fastforgex new myapi --db postgresql --docker --tests --lint
cd myapi
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

---

### Windows

Install Python 3.12 from [python.org](https://www.python.org/downloads/). During installation, check "Add Python to PATH".

Open PowerShell and install FastForgeX:

```powershell
pip install fastforgex
```

Create a project and run it:

```powershell
fastforgex new myapi --db postgresql --docker --tests --lint
cd myapi
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

With Makefile on Windows, install [GNU Make for Windows](https://gnuwin32.sourceforge.net/packages/make.htm) or use the commands directly from the table above.

Note: `entrypoint.sh` requires WSL or Git Bash on Windows. For local development without Docker, run the commands inside it manually.

---

## After Generation

### Without a database

```bash
cd myapi
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

### With SQLite

```bash
cd myapi
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env             # DATABASE_URL is already set for SQLite
alembic upgrade head
uvicorn app.main:app --reload
```

### With PostgreSQL (local)

Start PostgreSQL, create a database, then:

```bash
cd myapi
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env: set DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/yourdb
alembic upgrade head
uvicorn app.main:app --reload
```

### With PostgreSQL + Docker Compose

```bash
cd myapi
cp .env.example .env
docker compose up -d
```

The `app` service starts only after the `db` service passes its health check. Migrations run automatically via `entrypoint.sh`.

### Enable pre-commit hooks (with `--lint`)

```bash
pip install pre-commit
pre-commit install
```

Every `git commit` will now run ruff and black automatically.

### Run tests (with `--tests`)

```bash
pytest
```

### Add a migration (with `--db`)

Define a model in `app/db/models/`, import it in `app/db/base.py`, then:

```bash
alembic revision --autogenerate -m "add users table"
alembic upgrade head
```

Or with the Makefile:

```bash
make migration name="add users table"
make migrate
```

---

## License

MIT License

Copyright (c) 2026 Syed Muhammad Awais Gillani

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
