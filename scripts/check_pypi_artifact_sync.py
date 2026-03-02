"""Check whether local release artifacts match already-published PyPI artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

import tomllib


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare local dist artifacts with PyPI artifacts for current project version."
    )
    parser.add_argument(
        "--dist-dir",
        default="dist",
        help="Directory containing local build artifacts.",
    )
    return parser.parse_args()


def _project_identity(pyproject_path: Path) -> tuple[str, str]:
    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)
    project = data["project"]
    return str(project["name"]), str(project["version"])


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _local_artifacts(dist_dir: Path, package: str, version: str) -> list[Path]:
    wheel_pattern = f"{package.replace('-', '_')}-{version}-*.whl"
    sdist_name = f"{package}-{version}.tar.gz"
    wheels = sorted(dist_dir.glob(wheel_pattern))
    sdist = dist_dir / sdist_name

    artifacts: list[Path] = []
    artifacts.extend(wheels)
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
        digests = item.get("digests", {})
        sha256 = digests.get("sha256")
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
    package, version = _project_identity(Path("pyproject.toml"))
    artifacts = _local_artifacts(dist_dir, package, version)

    exists, remote_files = _pypi_release_files(package, version)
    if not exists:
        _set_github_outputs(exists=False, identical=False)
        print(f"PyPI does not have {package}=={version}.")
        return 0

    mismatches: list[str] = []
    for artifact in artifacts:
        local_sha = _sha256_file(artifact)
        remote_sha = remote_files.get(artifact.name)
        if not remote_sha:
            mismatches.append(f"{artifact.name}: missing on PyPI")
            continue
        if local_sha != remote_sha:
            mismatches.append(f"{artifact.name}: local={local_sha} pypi={remote_sha}")

    if mismatches:
        _set_github_outputs(exists=True, identical=False)
        print(f"PyPI already has {package}=={version}, but artifacts differ.")
        for mismatch in mismatches:
            print(f"  - {mismatch}")
        print("Bump [project].version before publishing changes.")
        return 1

    _set_github_outputs(exists=True, identical=True)
    print(f"PyPI already has {package}=={version} with identical artifacts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
