from __future__ import annotations

import json
from pathlib import Path

from .base import StackAdapter
from ..model import ProjectInfo


def _detect_package_manager(target: Path) -> str:
    if (target / "pnpm-lock.yaml").is_file():
        return "pnpm"
    if (target / "yarn.lock").is_file():
        return "yarn"
    if (target / "package-lock.json").is_file():
        return "npm"

    pkg = target / "package.json"
    if pkg.is_file():
        try:
            d = json.loads(pkg.read_text(encoding="utf-8"))
            pm = str(d.get("packageManager", ""))
            if pm.startswith("pnpm@"):  # pragma: no cover
                return "pnpm"
            if pm.startswith("yarn@"):  # pragma: no cover
                return "yarn"
            if pm.startswith("npm@"):  # pragma: no cover
                return "npm"
        except Exception:
            pass

    return "npm"


class NodeAdapter(StackAdapter):
    name = "node"

    def default_info(self, target: Path, project_name: str) -> ProjectInfo:
        pm = _detect_package_manager(target)

        if pm == "npm":
            commands = {
                "install": "npm install",
                "dev": "npm run dev",
                "test": "npm test",
                "lint": "npm run lint",
                "build": "npm run build",
            }
        elif pm == "yarn":
            commands = {
                "install": "yarn",
                "dev": "yarn dev",
                "test": "yarn test",
                "lint": "yarn lint",
                "build": "yarn build",
            }
        else:
            commands = {
                "install": "pnpm install",
                "dev": "pnpm dev",
                "test": "pnpm test",
                "lint": "pnpm lint",
                "build": "pnpm build",
            }

        commands["single_test"] = "(depends on test runner; e.g. `pnpm test -- -t name` or `pnpm vitest path/to.test.ts`)"

        return ProjectInfo(
            project_name=project_name,
            stack="node",
            package_manager=pm,
            commands=commands,
            source_dirs=["src"],
            config_locations=["package.json"],
            branching_model="main",
            warnings=[],
        ).normalized()
