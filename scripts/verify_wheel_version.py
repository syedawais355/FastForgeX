from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install a built wheel in a temp venv and verify the CLI version output."
    )
    parser.add_argument("--dist-dir", default="dist", help="Directory containing built wheels.")
    return parser.parse_args()


def _latest_wheel(dist_dir: Path) -> Path:
    wheels = sorted(dist_dir.glob("*.whl"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not wheels:
        raise FileNotFoundError(f"No wheel files found in {dist_dir}")
    return wheels[0]


def _wheel_version(wheel_path: Path) -> str:
    with zipfile.ZipFile(wheel_path) as wheel:
        metadata_files = [name for name in wheel.namelist() if name.endswith(".dist-info/METADATA")]
        if not metadata_files:
            raise RuntimeError(f"No METADATA found in wheel: {wheel_path}")
        metadata = wheel.read(metadata_files[0]).decode("utf-8")
    for line in metadata.splitlines():
        if line.startswith("Version: "):
            return line.split("Version: ", 1)[1].strip()
    raise RuntimeError(f"Version field not found in wheel METADATA: {wheel_path}")


def _venv_bin(venv_dir: Path, name: str) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / f"{name}.exe"
    return venv_dir / "bin" / name


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, capture_output=True, text=True)


def main() -> int:
    args = _parse_args()
    dist_dir = Path(args.dist_dir).resolve()
    wheel_path = _latest_wheel(dist_dir)
    expected = f"fastforgex, version {_wheel_version(wheel_path)}"

    with tempfile.TemporaryDirectory(prefix="fastforgex-verify-") as tmp:
        venv_dir = Path(tmp) / ".venv"
        _run([sys.executable, "-m", "venv", str(venv_dir)])
        python_bin = _venv_bin(venv_dir, "python")
        cli_bin = _venv_bin(venv_dir, "fastforgex")
        _run([str(python_bin), "-m", "pip", "install", "--upgrade", "pip"])
        _run([str(python_bin), "-m", "pip", "install", str(wheel_path)])
        result = _run([str(cli_bin), "--version"])
        actual = result.stdout.strip()

    if actual != expected:
        print("CLI version mismatch:", file=sys.stderr)
        print(f"  expected: {expected}", file=sys.stderr)
        print(f"  actual:   {actual}", file=sys.stderr)
        return 1

    print(f"CLI version verified: {actual}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())