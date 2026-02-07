from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Detection:
    stack: str
    confidence: str
    reason: str


def detect_stack(target: Path) -> Detection:
    if (target / "package.json").is_file():
        return Detection(stack="node", confidence="high", reason="Found package.json")
    if (target / "pyproject.toml").is_file():
        return Detection(stack="python", confidence="high", reason="Found pyproject.toml")
    if (target / "requirements.txt").is_file():
        return Detection(stack="python", confidence="medium", reason="Found requirements.txt")

    if (target / "index.html").is_file():
        return Detection(stack="static", confidence="medium", reason="Found index.html")

    return Detection(stack="static", confidence="low", reason="No stack indicator files found")
