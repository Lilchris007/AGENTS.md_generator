from __future__ import annotations

CONFIG_FILENAME = ".agentsgen.json"

AGENTS_FILENAME = "AGENTS.md"
RUNBOOK_FILENAME = "RUNBOOK.md"

AGENTS_GENERATED_FILENAME = "AGENTS.generated.md"
RUNBOOK_GENERATED_FILENAME = "RUNBOOK.generated.md"

PROMPTS_DIRNAME = "prompt"

SECTION_NAMES = [
    "overview",
    "rules",
    "commands",
    "structure",
    "output_protocol",
    # Shared cross-stack sections.
    "guardrails",
    "workflow",
    "verification",
    "style",
    # Stack-specific sections (only one is required depending on stack).
    "python",
    "node",
    "static",
]

MARKER_PREFIX = "AGENTSGEN"


def start_marker(section: str) -> str:
    # Default marker format (configurable in .agentsgen.json v1):
    # <!-- AGENTSGEN:START section=commands -->
    return f"<!-- {MARKER_PREFIX}:START section={section} -->"


def end_marker(section: str) -> str:
    return f"<!-- {MARKER_PREFIX}:END section={section} -->"
