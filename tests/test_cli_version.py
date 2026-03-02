"""Tests for FastForgeX CLI version reporting."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError

import pytest
from click.testing import CliRunner

import fastforgex.cli.main as cli_main


def test_resolve_cli_version_prefers_distribution_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli_main, "package_version", lambda _name: "9.9.9")
    assert cli_main._resolve_cli_version() == "9.9.9"


def test_resolve_cli_version_falls_back_when_metadata_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _raise_not_found(_name: str) -> str:
        raise PackageNotFoundError

    monkeypatch.setattr(cli_main, "package_version", _raise_not_found)
    monkeypatch.setattr(cli_main, "__version__", "0+unknown")
    assert cli_main._resolve_cli_version() == "0+unknown"


def test_cli_version_output_matches_resolved_version() -> None:
    result = CliRunner().invoke(cli_main.cli, ["--version"])
    assert result.exit_code == 0
    assert result.output.strip() == f"fastforgex, version {cli_main._resolve_cli_version()}"
