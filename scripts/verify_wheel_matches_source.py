from __future__ import annotations

import argparse
import hashlib
import zipfile
from pathlib import Path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify the built wheel contains files identical to the repository source."
    )
    parser.add_argument(
        "--dist-dir",
        default="dist",
        help="Directory containing built wheels.",
    )
    return parser.parse_args()


def _latest_wheel(dist_dir: Path) -> Path:
    wheels = sorted(dist_dir.glob("*.whl"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not wheels:
        raise FileNotFoundError(f"No wheel files found in {dist_dir}")
    return wheels[0]


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _repo_file_map(root: Path) -> dict[str, Path]:
    files: dict[str, Path] = {}
    for path in (root / "fastforgex").rglob("*"):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        if path.name.endswith("~") or path.name.startswith("."):
            continue
        rel = path.relative_to(root).as_posix()
        files[rel] = path
    return files


def main() -> int:
    args = _parse_args()
    root = Path.cwd()
    wheel_path = _latest_wheel(Path(args.dist_dir).resolve())
    repo_files = _repo_file_map(root)

    with zipfile.ZipFile(wheel_path) as wheel:
        wheel_files = {
            name
            for name in wheel.namelist()
            if name.startswith("fastforgex/") and not name.endswith("/")
        }

        missing_in_wheel = sorted(set(repo_files) - wheel_files)
        extra_in_wheel = sorted(wheel_files - set(repo_files))

        if missing_in_wheel:
            print("Files missing from wheel:")
            for item in missing_in_wheel:
                print(f"  {item}")
        if extra_in_wheel:
            print("Unexpected files in wheel:")
            for item in extra_in_wheel:
                print(f"  {item}")
        if missing_in_wheel or extra_in_wheel:
            return 1

        mismatches: list[str] = []
        for rel, repo_path in sorted(repo_files.items()):
            repo_bytes = repo_path.read_bytes()
            wheel_bytes = wheel.read(rel)
            if repo_bytes != wheel_bytes:
                mismatches.append(
                    f"{rel}: repo={_sha256(repo_bytes)[:12]} wheel={_sha256(wheel_bytes)[:12]}"
                )

    if mismatches:
        print("Content mismatches between source and wheel:")
        for mismatch in mismatches:
            print(f"  {mismatch}")
        return 1

    print(f"Wheel source parity verified: {wheel_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())