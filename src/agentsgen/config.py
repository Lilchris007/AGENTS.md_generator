from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .model import ProjectInfo


@dataclass(frozen=True)
class ToolMarkers:
    start: str = "<!-- AGENTSGEN:START section={section} -->"
    end: str = "<!-- AGENTSGEN:END section={section} -->"


@dataclass
class ToolConfig:
    # v1 schema (recommended). We also support reading legacy ProjectInfo-only configs.
    version: int = 1

    mode: str = "safe"
    on_missing_markers: str = "write_generated"
    generated_suffix: str = ".generated"

    markers: ToolMarkers = field(default_factory=ToolMarkers)

    # Which sections are expected in AGENTS.md (and which stack section to include).
    sections: list[str] = field(
        default_factory=lambda: [
            "guardrails",
            "workflow",
            "style",
            "verification",
            "stack",
            "repo_context",
        ]
    )

    presets: dict[str, Any] = field(default_factory=dict)
    defaults: dict[str, Any] = field(default_factory=dict)

    project: ProjectInfo = field(default_factory=lambda: ProjectInfo(project_name="", stack="static").normalized())

    def to_json(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "mode": self.mode,
            "on_missing_markers": self.on_missing_markers,
            "generated_suffix": self.generated_suffix,
            "markers": {"start": self.markers.start, "end": self.markers.end},
            "sections": list(self.sections),
            "presets": self.presets,
            "defaults": self.defaults,
            "project": self.project.to_json(),
        }

    @staticmethod
    def from_json(d: dict[str, Any]) -> "ToolConfig":
        # Legacy format: ProjectInfo-only dict (no version field).
        if "version" not in d and "project_name" in d and "stack" in d:
            info = ProjectInfo.from_json(d)
            cfg = ToolConfig(project=info)
            return cfg

        cfg = ToolConfig()
        cfg.version = int(d.get("version", 1))
        cfg.mode = str(d.get("mode", "safe"))
        cfg.on_missing_markers = str(d.get("on_missing_markers", "write_generated"))
        cfg.generated_suffix = str(d.get("generated_suffix", ".generated"))

        m = d.get("markers", {}) or {}
        cfg.markers = ToolMarkers(
            start=str(m.get("start", cfg.markers.start)),
            end=str(m.get("end", cfg.markers.end)),
        )

        cfg.sections = list(d.get("sections", cfg.sections) or cfg.sections)
        cfg.presets = dict(d.get("presets", {}) or {})
        cfg.defaults = dict(d.get("defaults", {}) or {})

        proj = d.get("project", {}) or {}
        cfg.project = ProjectInfo.from_json(proj) if proj else ProjectInfo(project_name="", stack="static").normalized()
        return cfg

