"""Central configuration dataclass for a FastForgeX generation run."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

Database = Literal["none", "sqlite", "postgresql"]
ORM = Literal["none", "sqlalchemy"]

_IDENTIFIER = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*$")


def validate_project_name(name: str) -> str:
    """Raise ValueError if name is not a valid Python identifier / folder name."""
    cleaned = name.strip().replace("-", "_").replace(" ", "_")
    if not _IDENTIFIER.match(cleaned):
        raise ValueError(
            f"'{name}' is not a valid project name. "
            "Use letters, digits, and underscores only. Must start with a letter."
        )
    return cleaned


@dataclass(frozen=True)
class ProjectConfig:
    """Immutable description of the project to be generated."""

    project_name: str
    db: Database = "none"
    orm: ORM = "none"
    docker: bool = False
    tests: bool = False
    lint: bool = False
    ci: bool = False
    makefile: bool = False
    use_db: bool = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "use_db", self.db != "none")

    def to_template_vars(self) -> dict[str, object]:
        return {
            "project_name": self.project_name,
            "db": self.db,
            "orm": self.orm,
            "docker": self.docker,
            "tests": self.tests,
            "lint": self.lint,
            "ci": self.ci,
            "makefile": self.makefile,
            "use_db": self.use_db,
        }
