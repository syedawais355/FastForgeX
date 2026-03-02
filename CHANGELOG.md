# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.2] - 2026-03-03

### Fixed
- CLI version reporting now resolves from installed package metadata with a source fallback, preventing stale hardcoded version output.
- Added automated wheel verification in CI/publish workflows to ensure `fastforgex --version` matches wheel metadata before release.
- Publish workflow now runs from GitHub Release publishing and blocks publishing if the version already exists on PyPI.
- Publish workflow now validates release tag/version alignment and release commit alignment with `main` to prevent outdated artifact releases.

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

[0.1.2]: https://github.com/syedawais355/FastForgeX/releases/tag/v0.1.2
[0.1.1]: https://github.com/syedawais355/FastForgeX/releases/tag/v0.1.1
[0.1.0]: https://github.com/syedawais355/FastForgeX/releases/tag/v0.1.0
