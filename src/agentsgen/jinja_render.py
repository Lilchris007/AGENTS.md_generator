from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, StrictUndefined


def _env() -> Environment:
    # Keep templates deterministic (no autoescape; strict undefined to catch mistakes).
    return Environment(undefined=StrictUndefined, autoescape=False)


def render_jinja_template(template_text: str, ctx: dict[str, Any]) -> str:
    tpl = _env().from_string(template_text)
    return tpl.render(**ctx)


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")

