# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.1.7]: https://github.com/syedawais355/FastForgeX/releases/tag/v0.1.7
[0.1.6]: https://github.com/syedawais355/FastForgeX/releases/tag/v0.1.6
[0.1.5]: https://github.com/syedawais355/FastForgeX/releases/tag/v0.1.5
[0.1.4]: https://github.com/syedawais355/FastForgeX/releases/tag/v0.1.4
[0.1.3]: https://github.com/syedawais355/FastForgeX/releases/tag/v0.1.3
[0.1.2]: https://github.com/syedawais355/FastForgeX/releases/tag/v0.1.2
[0.1.1]: https://github.com/syedawais355/FastForgeX/releases/tag/v0.1.1
[0.1.0]: https://github.com/syedawais355/FastForgeX/releases/tag/v0.1.0
