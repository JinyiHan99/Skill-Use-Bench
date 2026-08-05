#!/usr/bin/env python3

from __future__ import annotations
import argparse
import sys
from pathlib import Path


ENV_BLOCK = """\

# Working environment

You are an autonomous coding agent running inside a sandbox container.
The current working directory contains the initial files you need
under `./assets/{task_id}/`.

The available shell tools are: bash, read, edit, grep.
You may freely use Read / Edit / Write / Bash / Grep as needed.

# Your task

Solve the task above by acting in the sandbox. When you are done,
write your final summary to the model's last text response (no special
file required).
"""


def _parse_yaml(text: str) -> dict:
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text) or {}
    except ImportError:
        in_desc = False
        lines = []
        indent = None
        for raw in text.splitlines():
            if raw.startswith("description:"):
                rest = raw[len("description:"):].strip()
                if rest in ("|", ">", "|-", ">-", "|+", ">+"):
                    in_desc = True
                    continue
                if rest:
                    return {"description": rest.strip("'\" ")}
            elif in_desc:
                if raw and not raw[0].isspace():
                    break
                if indent is None and raw.strip():
                    indent = len(raw) - len(raw.lstrip())
                if raw.strip() == "" or (indent is not None and len(raw) - len(raw.lstrip()) >= indent):
                    lines.append(raw[indent:] if indent and len(raw) >= indent else raw)
        return {"description": "\n".join(lines).rstrip()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True, help="path to task yaml")
    ap.add_argument("--task-id", required=True, help="task id (used in env block)")
    ap.add_argument("--out", required=True, help="output prompt.txt path")
    args = ap.parse_args()

    src = Path(args.task)
    if not src.is_file():
        print(f"[build_prompt] ERROR: task yaml not found: {src}", file=sys.stderr)
        return 2

    data = _parse_yaml(src.read_text(encoding="utf-8"))
    desc = (data.get("description") or "").rstrip()
    if not desc:
        print(f"[build_prompt] ERROR: empty description in {src}", file=sys.stderr)
        return 2

    body = desc + "\n" + ENV_BLOCK.format(task_id=args.task_id)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(body, encoding="utf-8")
    print(f"[build_prompt] {src} → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
