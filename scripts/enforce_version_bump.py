from __future__ import annotations

import argparse
import subprocess
import sys


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fail if package source changed without a version bump in pyproject.toml."
    )
    parser.add_argument("--base", required=True, help="Base git revision (PR base SHA).")
    parser.add_argument("--head", required=True, help="Head git revision (PR head SHA).")
    return parser.parse_args()


def _run(*args: str) -> str:
    return subprocess.check_output(args, text=True).strip()


def _changed_files(base: str, head: str) -> list[str]:
    out = _run("git", "diff", "--name-only", base, head)
    return [line for line in out.splitlines() if line]


def _load_toml(text: str) -> dict:  # type: ignore[type-arg]
    if sys.version_info >= (3, 11):
        import tomllib

        return tomllib.loads(text)
    try:
        import tomllib  # type: ignore[no-redef]

        return tomllib.loads(text)
    except ImportError:
        pass
    try:
        import tomli  # type: ignore[import]

        return tomli.loads(text)
    except ImportError:
        pass
    import re

    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if match:
        return {"project": {"version": match.group(1)}}
    raise RuntimeError("Cannot parse pyproject.toml: install tomli for Python < 3.11.")


def _version_at_rev(rev: str) -> str:
    text = _run("git", "show", f"{rev}:pyproject.toml")
    return str(_load_toml(text)["project"]["version"])


def _is_package_change(path: str) -> bool:
    return path.startswith("fastforgex/")


def main() -> int:
    args = _parse_args()
    changed = _changed_files(args.base, args.head)
    package_changed = any(_is_package_change(p) for p in changed)

    if not package_changed:
        print("No package source changes detected. Version bump not required.")
        return 0

    old_version = _version_at_rev(args.base)
    new_version = _version_at_rev(args.head)

    if old_version == new_version:
        print("Package source changed but version was not bumped.", file=sys.stderr)
        print(f"Version unchanged: {new_version}", file=sys.stderr)
        print("Bump [project].version in pyproject.toml before merging.", file=sys.stderr)
        return 1

    print(f"Version bumped: {old_version} -> {new_version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
