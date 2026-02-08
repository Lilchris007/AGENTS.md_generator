from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..model import ProjectInfo


@dataclass(frozen=True)
class StackAdapter:
    name: str

    def default_info(
        self, target: Path, project_name: str
    ) -> ProjectInfo:  # pragma: no cover
        raise NotImplementedError


def project_name_from_dir(target: Path) -> str:
    return target.resolve().name
