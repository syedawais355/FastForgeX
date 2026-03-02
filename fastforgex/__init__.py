"""FastForgeX - FastAPI project scaffolding CLI."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("fastforgex")
except PackageNotFoundError:
    __version__ = "0+unknown"
