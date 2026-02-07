from __future__ import annotations

from pathlib import Path

from .base import StackAdapter
from ..model import ProjectInfo


class StaticAdapter(StackAdapter):
    name = "static"

    def default_info(self, target: Path, project_name: str) -> ProjectInfo:
        commands = {
            "install": "(none)",
            "dev": "python -m http.server 8000  # or your preferred dev server",
            "test": "(none)",
            "build": "(none)",
        }
        return ProjectInfo(
            project_name=project_name,
            stack="static",
            commands=commands,
            source_dirs=["."],
            config_locations=[],
            branching_model="main",
            warnings=[],
        ).normalized()
