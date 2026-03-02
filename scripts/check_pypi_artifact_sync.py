from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare local dist artifacts with published PyPI artifacts."
    )
    parser.add_argument("--dist-dir", default="dist", help="Directory containing build artifacts.")
    return parser.parse_args()


def _load_toml(path: Path) -> dict:  # type: ignore[type-arg]
    if sys.version_info >= (3, 11):
        import tomllib
        with path.open("rb") as f:
            return tomllib.load(f)
    try:
        import tomllib  # type: ignore[no-redef]
        with path.open("rb") as f:
            return tomllib.load(f)
    except ImportError:
        pass
    try:
        import tomli  # type: ignore[import]
        with path.open("rb") as f:
            return tomli.load(f)
    except ImportError:
        pass
    import re
    text = path.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    name_match = re.search(r'^name\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if match and name_match:
        return {"project": {"name": name_match.group(1), "version": match.group(1)}}
    raise RuntimeError("Cannot parse pyproject.toml: install tomli for Python < 3.11.")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _local_artifacts(dist_dir: Path, package: str, version: str) -> list[Path]:
    wheel_pattern = f"{package.replace('-', '_')}-{version}-*.whl"
    sdist_name = f"{package}-{version}.tar.gz"
    artifacts: list[Path] = sorted(dist_dir.glob(wheel_pattern))
    sdist = dist_dir / sdist_name
    if sdist.exists():
        artifacts.append(sdist)
    if not artifacts:
        raise FileNotFoundError(f"No artifacts found for {package}=={version} in {dist_dir}.")
    return artifacts


def _pypi_release_files(package: str, version: str) -> tuple[bool, dict[str, str]]:
    url = f"https://pypi.org/pypi/{package}/{version}/json"
    try:
        with urllib.request.urlopen(url) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return False, {}
        raise
    files: dict[str, str] = {}
    for item in payload.get("urls", []):
        filename = item.get("filename")
        sha256 = (item.get("digests") or {}).get("sha256")
        if filename and sha256:
            files[str(filename)] = str(sha256)
    return True, files


def _set_github_outputs(exists: bool, identical: bool) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return
    with Path(output_path).open("a", encoding="utf-8") as f:
        f.write(f"exists={'true' if exists else 'false'}\n")
        f.write(f"identical={'true' if identical else 'false'}\n")


def main() -> int:
    args = _parse_args()
    dist_dir = Path(args.dist_dir).resolve()
    data = _load_toml(Path("pyproject.toml"))
    package = str(data["project"]["name"])
    version = str(data["project"]["version"])
    artifacts = _local_artifacts(dist_dir, package, version)

    exists, remote_files = _pypi_release_files(package, version)
    if not exists:
        _set_github_outputs(exists=False, identical=False)
        print(f"PyPI does not have {package}=={version}. Ready to publish.")
        return 0

    mismatches: list[str] = []
    for artifact in artifacts:
        local_sha = _sha256_file(artifact)
        remote_sha = remote_files.get(artifact.name)
        if not remote_sha:
            mismatches.append(f"{artifact.name}: missing on PyPI")
        elif local_sha != remote_sha:
            mismatches.append(f"{artifact.name}: local={local_sha[:12]} pypi={remote_sha[:12]}")

    if mismatches:
        _set_github_outputs(exists=True, identical=False)
        print(f"PyPI has {package}=={version} but artifacts differ. Bump the version.", file=sys.stderr)
        for mismatch in mismatches:
            print(f"  {mismatch}", file=sys.stderr)
        return 1

    _set_github_outputs(exists=True, identical=True)
    print(f"PyPI already has identical artifacts for {package}=={version}. Skipping publish.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())