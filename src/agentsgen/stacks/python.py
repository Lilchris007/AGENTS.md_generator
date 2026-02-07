from __future__ import annotations

from pathlib import Path

from .base import StackAdapter
from ..model import ProjectInfo


def _detect_python_tooling(target: Path) -> str:
    pyproject = target / "pyproject.toml"
    if pyproject.is_file():
        try:
            import tomllib  # py311+

            d = tomllib.loads(pyproject.read_text(encoding="utf-8"))
            tool = d.get("tool", {}) or {}
            if "poetry" in tool:
                return "poetry"
        except Exception:
            pass
    return "venv"


class PythonAdapter(StackAdapter):
    name = "python"

    def default_info(self, target: Path, project_name: str) -> ProjectInfo:
        tooling = _detect_python_tooling(target)

        if tooling == "poetry":
            commands = {
                "install": "poetry install",
                "dev": "poetry run python -m your_module  # TODO",
                "test": "poetry run pytest",
                "lint": "poetry run ruff check .",
                "format": "poetry run ruff format .",
                "single_test": "poetry run pytest path/to/test_file.py::TestClass::test_name",
            }
            config_locations = ["pyproject.toml"]
        else:
            commands = {
                "install": "python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt",
                "dev": "python -m your_module  # TODO",
                "test": "pytest",
                "lint": "ruff check .",
                "format": "ruff format .",
                "single_test": "pytest path/to/test_file.py::TestClass::test_name",
            }
            config_locations = ["pyproject.toml", "requirements.txt"]

        return ProjectInfo(
            project_name=project_name,
            stack="python",
            python_tooling=tooling,
            commands=commands,
            source_dirs=["src"],
            config_locations=config_locations,
            branching_model="main",
            warnings=[],
        ).normalized()
