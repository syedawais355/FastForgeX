# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-03-05

### Added
- Comprehensive runtime integration test suite (`tests/test_generated_runtime.py`) covering all 16 meaningful configuration combinations — compile validation, file presence, content invariants, and live pytest execution for no-DB and SQLite projects.

### Changed
- `_write_linting` in the generator was split into `_write_pyproject` (runs when `tests or lint`) and `_write_pre_commit` (runs only when `lint`).
- Makefile `help` target redesigned with ANSI color codes, grouped sections (SETUP, DEVELOPMENT, TESTING, CODE QUALITY, DATABASE, DOCKER), and actual shell commands shown beneath each target.
- Live pytest tests in the runtime test suite skip on Python < 3.11, as generated projects target Python 3.12.

### Fixed
- Generated `conftest.py` now correctly uses `@pytest_asyncio.fixture` instead of `@pytest.fixture` for async fixtures, fixing compatibility with pytest-asyncio ≥ 0.23 strict mode.
- `pyproject.toml` is now generated whenever `--tests` or `--lint` is selected (previously only generated with `--lint`), ensuring `asyncio_mode = "auto"` is always set when tests are included.
- Makefile `.PHONY` declaration now correctly includes `test-cov`, `migration`, and `rollback`, and conditionally includes `down` only when `--db postgresql --docker` is selected.
- CLI now raises a clear error when `--orm` is specified without `--db` instead of falling into interactive mode.
- Generated `app/core/logger.py` uses `datetime.UTC` (Python 3.12 target) and `app/core/config.py` uses `list[str]` with `from __future__ import annotations` — both consistent with the generated project's `target-version = "py312"` ruff config.

## [0.1.9] - 2026-03-03

### Added
- Automated lint and formatting job in CI workflow: runs ruff and black on every push/PR, auto-commits formatting fixes.
- CI test job now depends on the lint job to enforce code style before running tests.

### Changed
- Refined CLI option formatting and spacing in `main.py` for a more consistent and professional output.
- Improved internal scripts (`enforce_version_bump.py`, `verify_wheel_matches_source.py`, `check_pypi_artifact_sync.py`) with better structure and error handling.

### Fixed
- Added type assertion for `project_name` in CLI to satisfy mypy strict mode.

## [0.1.8] - 2026-03-03

### Fixed
- Applied Black formatting to CLI entry point.
- Hardened CI/CD pipeline to ensure consistent PyPI publishing.

## [0.1.7] - 2026-03-03

### Fixed
- Applied automated code formatting with Black to resolve linting failures.

## [0.1.6] - 2026-03-03

### Changed
- Streamlined CLI docstrings for a cleaner and more professional look.

## [0.1.5] - 2026-03-03

### Added
- Professionalized CLI help messages with emojis and detailed feature lists.
- Enhanced 'new' command documentation with usage examples and clear option descriptions.

## [0.1.4] - 2026-03-03

### Fixed
- Resolved PyPI artifact mismatch by bumping version to 0.1.4.
- Hardened GitHub Actions to prevent race conditions during the release process.

## [0.1.3] - 2026-03-03

### Fixed
- Publish workflow now compares locally built artifacts against PyPI artifacts for the same version.
- Release runs skip upload only when artifacts are byte-identical; otherwise they fail and require a version bump.
- This guarantees that published packages always map to the exact source and metadata of that release version.

## [0.1.2] - 2026-03-03

### Fixed
- CLI version reporting now resolves from installed package metadata with a source fallback, preventing stale hardcoded version output.
- Added automated wheel verification in CI/publish workflows to ensure `fastforgex --version` matches wheel metadata before release.
- Publish workflow now runs from GitHub Release publishing and blocks publishing if the version already exists on PyPI.
- Publish workflow now validates release tag/version alignment and release commit alignment with `main` to prevent outdated artifact releases.
- CI now blocks PRs that change package source without a corresponding `pyproject.toml` version bump.
- CI/publish now verify wheel package files exactly match repository source files.
- Publish workflow now treats already-published versions as idempotent only when artifacts are identical; otherwise it fails and requires a version bump.

### Added
- Email notifications for every change pushed to `main`.
- Email notifications for PyPI publish success/failure outcomes.

## [0.1.1] - 2026-03-02

### Fixed
- Type checking with mypy strict mode
- Exception chaining for proper error handling
- Code formatting with black and ruff compliance

### Added
- MyPy type checker to dev dependencies
- Enhanced CI workflow with type checking and package validation
- Build and twine checks for PyPI compliance

## [0.1.0] - 2026-03-02

### Added
- Initial release of FastForgeX
- Interactive mode for project generation with guided prompts
- Flag mode for scripting and CI/CD integration
- Preset mode with minimal, api, and full configurations
- Database support: SQLite, PostgreSQL
- ORM support: SQLAlchemy
- Docker support with Dockerfile and docker-compose templates
- Testing framework setup with pytest
- Linting configuration with ruff and black
- GitHub Actions CI/CD pipeline
- Makefile for common development tasks
- Dry-run mode to preview generated files
- Full type hints across all modules
- Comprehensive documentation and examples

[0.2.0]: https://github.com/syedawais355/FastForgeX/releases/tag/v0.2.0
[0.1.9]: https://github.com/syedawais355/FastForgeX/releases/tag/v0.1.9
[0.1.8]: https://github.com/syedawais355/FastForgeX/releases/tag/v0.1.8
[0.1.7]: https://github.com/syedawais355/FastForgeX/releases/tag/v0.1.7
[0.1.6]: https://github.com/syedawais355/FastForgeX/releases/tag/v0.1.6
[0.1.5]: https://github.com/syedawais355/FastForgeX/releases/tag/v0.1.5
[0.1.4]: https://github.com/syedawais355/FastForgeX/releases/tag/v0.1.4
[0.1.3]: https://github.com/syedawais355/FastForgeX/releases/tag/v0.1.3
[0.1.2]: https://github.com/syedawais355/FastForgeX/releases/tag/v0.1.2
[0.1.1]: https://github.com/syedawais355/FastForgeX/releases/tag/v0.1.1
[0.1.0]: https://github.com/syedawais355/FastForgeX/releases/tag/v0.1.0
