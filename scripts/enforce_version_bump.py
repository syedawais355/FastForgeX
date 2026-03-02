"""Fail CI if package code changed without bumping project version."""

from __future__ import annotations

import argparse
import subprocess
import sys

import tomllib


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ensure pyproject version is bumped when package source changes."
    )
    parser.add_argument("--base", required=True, help="Base git revision (usually PR base SHA).")
    parser.add_argument("--head", required=True, help="Head git revision (usually PR head SHA).")
    return parser.parse_args()


def _run(*args: str) -> str:
    return subprocess.check_output(args, text=True).strip()


def _changed_files(base: str, head: str) -> list[str]:
    out = _run("git", "diff", "--name-only", base, head)
    return [line for line in out.splitlines() if line]


def _version_from_text(pyproject_text: str) -> str:
    data = tomllib.loads(pyproject_text)
    return str(data["project"]["version"])


def _version_at_rev(rev: str) -> str:
    text = _run("git", "show", f"{rev}:pyproject.toml")
    return _version_from_text(text)


def _is_package_change(path: str) -> bool:
    return path.startswith("fastforgex/")


def main() -> int:
    args = _parse_args()
    changed = _changed_files(args.base, args.head)
    package_changed = any(_is_package_change(path) for path in changed)

    if not package_changed:
        print("No package source changes detected. Version bump not required.")
        return 0

    old_version = _version_at_rev(args.base)
    new_version = _version_at_rev(args.head)
    if old_version == new_version:
        print("Package source changed but pyproject version was not bumped.", file=sys.stderr)
        print(f"Version unchanged: {new_version}", file=sys.stderr)
        print("Bump [project].version in pyproject.toml.", file=sys.stderr)
        return 1

    print(f"Package source changed and version bumped: {old_version} -> {new_version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
