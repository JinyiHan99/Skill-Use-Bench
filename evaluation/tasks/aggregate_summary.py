#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--batch-dir", required=True)
    p.add_argument("--task-id",   required=True)
    p.add_argument("--mode",      required=True)
    return p.parse_args()


def _safe_lines(path: Path) -> int:
    if not path.is_file():
        return 0
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def _safe_size(path: Path) -> int:
    try:
        return path.stat().st_size if path.is_file() else 0
    except Exception:
        return 0


def _read_meta(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _rel(base: Path, target: Path) -> str:
    try:
        return str(target.relative_to(base))
    except ValueError:
        return str(target)


def collect(batch_dir: Path, task_id: str, mode: str) -> list[dict]:
    jobs_dir = batch_dir / "jobs"
    if jobs_dir.is_dir():
        search_dir = jobs_dir
    else:
        search_dir = batch_dir
    rows: list[dict] = []

    for model_dir in sorted(p for p in search_dir.iterdir() if p.is_dir()):
        if model_dir.name.startswith(("_", ".")):
            continue
        # A directory only counts as a model job when trace.jsonl or meta.json exists.
        if not (model_dir / "trace.jsonl").exists() and not (model_dir / "meta.json").exists():
            continue
        model = model_dir.name
        meta_path   = model_dir / "meta.json"
        trace_path  = model_dir / "trace.jsonl"
        answer_path = model_dir / "answer.txt"
        log_path    = model_dir / "run.log"
        csv_path    = model_dir / "outputs" / task_id / "table_page2.csv"

        meta = _read_meta(meta_path)

        rows.append({
            "task_id":       task_id,
            "model":         model,
            "mode":   mode,
            "ok":            int(bool(meta.get("ok"))),
            "exit_code":     meta.get("exit_code", ""),
            "duration_sec":  meta.get("duration_sec", ""),
            "result_subtype":  meta.get("result_subtype", ""),
            "result_is_error": (
                "" if meta.get("result_is_error") is None
                else int(bool(meta.get("result_is_error")))
            ),
            "num_turns":meta.get("num_turns", ""),
            "max_turns":     meta.get("max_turns", ""),
            "csv_exists":    int(csv_path.is_file()),
            "csv_path":   _rel(batch_dir, csv_path)    if csv_path.is_file()    else "",
            "trace_lines":   _safe_lines(trace_path),
            "answer_len":    _safe_size(answer_path),
            "trace_path":    _rel(batch_dir, trace_path)  if trace_path.is_file()  else "",
            "answer_path":   _rel(batch_dir, answer_path) if answer_path.is_file() else "",
            "log_path":      _rel(batch_dir, log_path)    if log_path.is_file()    else "",
            "meta_path":     _rel(batch_dir, meta_path)   if meta_path.is_file()   else "",
        })
    return rows


def write_outputs(batch_dir: Path, rows: list[dict]) -> None:
    csv_path   = batch_dir / "summary.csv"
    jsonl_path = batch_dir / "summary.jsonl"

    cols = [
        "task_id", "model", "mode",
        "ok", "exit_code", "duration_sec",
        "result_subtype", "result_is_error", "num_turns", "max_turns",
        "csv_exists", "csv_path",
        "trace_lines", "answer_len",
        "trace_path", "answer_path", "log_path", "meta_path",
    ]

    with csv_path.open("w", newline="", encoding="utf-8") as cf, \
         jsonl_path.open("w", encoding="utf-8") as jf:
        writer = csv.DictWriter(cf, fieldnames=cols)
        writer.writeheader()
        for r in rows:
            writer.writerow({c: r.get(c, "") for c in cols})
            jf.write(json.dumps(r, ensure_ascii=False) + "\n")


def main() -> int:
    args = parse_args()
    batch_dir = Path(args.batch_dir).resolve()
    if not batch_dir.is_dir():
        print(f"[aggregate] batch_dir does not exist: {batch_dir}", file=sys.stderr)
        return 2

    rows = collect(batch_dir, args.task_id, args.mode)
    if not rows:
        print("[aggregate] WARNING: no jobs/<model>/ subdirectory found", file=sys.stderr)

    write_outputs(batch_dir, rows)

    ok_count = sum(r["ok"] for r in rows)
    csv_count = sum(r["csv_exists"] for r in rows)
    print(f"[aggregate] {len(rows)} model(s); agent ok = {ok_count}; CSV produced = {csv_count}")
    print(f"[aggregate] summary.csv  -> {batch_dir / 'summary.csv'}")
    print(f"[aggregate] summary.jsonl -> {batch_dir / 'summary.jsonl'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
