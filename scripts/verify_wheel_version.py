"""Verify wheel metadata version matches CLI --version output."""

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
        description="Install a built wheel in a temp venv and verify CLI version output."
    )
    parser.add_argument(
        "--dist-dir",
        default="dist",
        help="Directory that contains built wheel files.",
    )
    return parser.parse_args()


def _latest_wheel(dist_dir: Path) -> Path:
    wheels = sorted(dist_dir.glob("*.whl"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not wheels:
        raise FileNotFoundError(f"No wheel files found in {dist_dir}")
    return wheels[0]


def _wheel_version(wheel_path: Path) -> str:
    with zipfile.ZipFile(wheel_path) as wheel:
        metadata_files = [name for name in wheel.namelist() if name.endswith(".dist-info/METADATA")]
        if not metadata_files:
            raise RuntimeError(f"No METADATA file found in wheel: {wheel_path}")
        metadata = wheel.read(metadata_files[0]).decode("utf-8")
    for line in metadata.splitlines():
        if line.startswith("Version: "):
            return line.split("Version: ", 1)[1].strip()
    raise RuntimeError(f"Version field not found in wheel metadata: {wheel_path}")


def _venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _venv_fastforgex(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "fastforgex.exe"
    return venv_dir / "bin" / "fastforgex"


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, capture_output=True, text=True)


def main() -> int:
    args = _parse_args()
    dist_dir = Path(args.dist_dir).resolve()
    wheel_path = _latest_wheel(dist_dir)
    expected = f"fastforgex, version {_wheel_version(wheel_path)}"

    with tempfile.TemporaryDirectory(prefix="fastforgex-wheel-check-") as tmp:
        venv_dir = Path(tmp) / ".venv"
        _run([sys.executable, "-m", "venv", str(venv_dir)])
        python_bin = _venv_python(venv_dir)
        cli_bin = _venv_fastforgex(venv_dir)
        _run([str(python_bin), "-m", "pip", "install", "--upgrade", "pip"])
        _run([str(python_bin), "-m", "pip", "install", str(wheel_path)])
        version_proc = _run([str(cli_bin), "--version"])
        actual = version_proc.stdout.strip()

    if actual != expected:
        print("Wheel CLI version mismatch detected:", file=sys.stderr)
        print(f"  wheel:    {wheel_path}", file=sys.stderr)
        print(f"  expected: {expected}", file=sys.stderr)
        print(f"  actual:   {actual}", file=sys.stderr)
        return 1

    print(f"Verified: {actual} ({wheel_path.name})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
