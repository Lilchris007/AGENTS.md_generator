from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProjectInfo:
    project_name: str
    stack: str  # node|python|static

    package_manager: str = ""  # npm|pnpm|yarn
    python_tooling: str = ""  # venv|poetry

    # Exact one-liner commands. Keep strings stable to preserve idempotency.
    commands: dict[str, str] = field(default_factory=dict)

    # Repo conventions.
    source_dirs: list[str] = field(default_factory=list)
    config_locations: list[str] = field(default_factory=list)
    branching_model: str = ""  # main, main+dev, none

    warnings: list[str] = field(default_factory=list)

    def normalized(self) -> "ProjectInfo":
        self.source_dirs = sorted({x.strip() for x in self.source_dirs if x and x.strip()})
        self.config_locations = sorted({x.strip() for x in self.config_locations if x and x.strip()})
        self.warnings = sorted({x.strip() for x in self.warnings if x and x.strip()})

        # Stable command ordering isn't required in JSON, but keep keys consistent.
        allowed = ["install", "dev", "test", "lint", "format", "build", "single_test"]
        new_cmds: dict[str, str] = {}
        for k in allowed:
            v = (self.commands.get(k, "") or "").strip()
            if v:
                new_cmds[k] = v
        # Keep any extra keys in a stable order at the end.
        for k in sorted(set(self.commands.keys()) - set(allowed)):
            v = (self.commands.get(k, "") or "").strip()
            if v:
                new_cmds[k] = v
        self.commands = new_cmds

        self.package_manager = (self.package_manager or "").strip()
        self.python_tooling = (self.python_tooling or "").strip()
        self.branching_model = (self.branching_model or "").strip()
        self.project_name = (self.project_name or "").strip()
        self.stack = (self.stack or "").strip()

        return self

    def to_json(self) -> dict[str, Any]:
        return {
            "project_name": self.project_name,
            "stack": self.stack,
            "package_manager": self.package_manager,
            "python_tooling": self.python_tooling,
            "commands": self.commands,
            "source_dirs": self.source_dirs,
            "config_locations": self.config_locations,
            "branching_model": self.branching_model,
            "warnings": self.warnings,
        }

    @staticmethod
    def from_json(d: dict[str, Any]) -> "ProjectInfo":
        return ProjectInfo(
            project_name=str(d.get("project_name", "")),
            stack=str(d.get("stack", "")),
            package_manager=str(d.get("package_manager", "")),
            python_tooling=str(d.get("python_tooling", "")),
            commands=dict(d.get("commands", {}) or {}),
            source_dirs=list(d.get("source_dirs", []) or []),
            config_locations=list(d.get("config_locations", []) or []),
            branching_model=str(d.get("branching_model", "")),
            warnings=list(d.get("warnings", []) or []),
        ).normalized()


@dataclass
class RenderPlan:
    sections: dict[str, str]
