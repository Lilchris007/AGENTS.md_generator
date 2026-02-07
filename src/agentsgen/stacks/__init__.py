from __future__ import annotations

from .base import StackAdapter
from .node import NodeAdapter
from .python import PythonAdapter
from .static import StaticAdapter


def adapter_for(stack: str) -> StackAdapter:
    stack = (stack or "").strip().lower()
    if stack == "node":
        return NodeAdapter(name="node")
    if stack == "python":
        return PythonAdapter(name="python")
    if stack == "static":
        return StaticAdapter(name="static")

    raise ValueError(f"Unsupported stack: {stack}")
