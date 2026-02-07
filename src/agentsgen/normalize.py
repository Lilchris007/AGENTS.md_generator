from __future__ import annotations


def normalize_markdown(text: str) -> str:
    # 1) Normalize newlines.
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 2) Strip trailing spaces on each line.
    lines = [ln.rstrip(" \t") for ln in text.split("\n")]

    # 3) Collapse excessive blank lines (keep at most 2 consecutive).
    out: list[str] = []
    blank_run = 0
    for ln in lines:
        if ln == "":
            blank_run += 1
            if blank_run <= 2:
                out.append(ln)
            continue
        blank_run = 0
        out.append(ln)

    normalized = "\n".join(out).rstrip("\n") + "\n"
    return normalized
