from __future__ import annotations

import re
from pathlib import Path


_VAR_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")


def render_template(template_text: str, ctx: dict[str, str]) -> str:
    def repl(m: re.Match[str]) -> str:
        key = m.group(1)
        if key not in ctx:
            raise KeyError(f"Missing template variable: {key}")
        return ctx[key]

    return _VAR_RE.sub(repl, template_text)


def load_template(path: Path) -> str:
    return path.read_text(encoding="utf-8")
