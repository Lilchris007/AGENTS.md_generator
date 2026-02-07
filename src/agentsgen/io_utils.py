from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        Path(tmp).replace(path)
    finally:
        try:
            Path(tmp).unlink(missing_ok=True)
        except Exception:
            pass


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(read_text(path))


def write_json_atomic(path: Path, obj: dict[str, Any]) -> None:
    content = json.dumps(obj, indent=2, ensure_ascii=False) + "\n"
    write_text_atomic(path, content)
