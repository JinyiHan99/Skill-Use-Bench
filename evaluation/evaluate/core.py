"""Generic batch evaluation: iterate <batch_dir>/jobs/<model>/, dispatch the
matching evaluator by task_id and produce eval_summary.csv / eval_report.md / eval_details.jsonl.
"""
from __future__ import annotations

import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .base import JobResult
from .tasks import get_evaluator


# ---------------------------- Public entry -------------------------------


def evaluate_batch(batch_dir: Path,
                   task_id: Optional[str] = None,
                   repo_root: Optional[Path] = None,
                   use_llm_judge: bool = False,
                   llm_judge=None) -> List[JobResult]:
    """Run the full evaluation on a batch directory, emit three artefact files and return the JobResult list.

    Parameters
    ----
    batch_dir : runs/<TASK>/batch_<ts>_<TASK>_<mode>/
    task_id   : inferred from the batch dir name if omitted (batch_<ts>_<TASK>_<mode>)
    repo_root : project root (containing tasks/, assets/, evaluate/); if omitted, walked up from batch_dir
    """
    batch_dir = Path(batch_dir).resolve()
    if not batch_dir.is_dir():
        raise FileNotFoundError(f"batch_dir does not exist: {batch_dir}")

    if task_id is None:
        task_id = _infer_task_id(batch_dir)
    if repo_root is None:
        repo_root = _infer_repo_root(batch_dir)

    EvaluatorCls = get_evaluator(task_id)
    evaluator = EvaluatorCls(repo_root=repo_root,
                             use_llm_judge=use_llm_judge,
                             llm_judge=llm_judge)

    jobs_dir = batch_dir / "jobs"
    if not jobs_dir.is_dir():
        raise FileNotFoundError(f"jobs/ subdirectory does not exist: {jobs_dir}")

    results: List[JobResult] = []
    for model_dir in sorted(p for p in jobs_dir.iterdir() if p.is_dir()):
        model = model_dir.name
        try:
            res = evaluator.evaluate(model_dir, model=model)
        except Exception as e:
            # Record the failure for one model without aborting the whole batch
            res = JobResult(task_id=task_id, model=model, job_dir=model_dir)
            res.extras["error"] = f"{type(e).__name__}: {e}"
        res.compute_scores()
        results.append(res)

    _write_summary_csv(batch_dir, results)
    _write_details_jsonl(batch_dir, results)
    _write_report_md(batch_dir, task_id, results)

    return results


# ---------------------------- Inference helpers --------------------------


_BATCH_DIR_RE = re.compile(
    r"^batch_(?P<ts>\d{8}-\d{6})_(?P<task>.+)_(?P<mode>full|noskill)$"
)


def _infer_task_id(batch_dir: Path) -> str:
    m = _BATCH_DIR_RE.match(batch_dir.name)
    if m:
        return m.group("task")
    # Fallback: parent directory name
    if batch_dir.parent.name.startswith("T"):
        return batch_dir.parent.name
    raise ValueError(
        f"Cannot infer task_id from batch dir name: {batch_dir.name}; pass --task-id explicitly"
    )


def _infer_repo_root(batch_dir: Path) -> Path:
    """Expected layout: <repo_root>/runs/<TASK>/batch_xxx/. Walk up until a dir containing tasks/ is found."""
    for p in [batch_dir, *batch_dir.parents]:
        if (p / "tasks").is_dir() and (p / "evaluate").is_dir():
            return p
    # Fallback: three levels above batch_dir
    return batch_dir.parent.parent.parent


# ---------------------------- Output writers -----------------------------


def _write_summary_csv(batch_dir: Path, results: List[JobResult]) -> None:
    if not results:
        return
    rows = [r.to_flat_dict() for r in results]

    # Collect all columns (order: task_id, model -> each rubric item in appearance order -> aggregate scores)
    cols: list[str] = ["task_id", "model"]
    seen = set(cols)
    for r in results:
        for c in r.outcome + r.must_do + r.must_not + r.process:
            if c.id not in seen:
                cols.append(c.id)
                seen.add(c.id)
    for k in ("outcome", "adherence", "process", "task_score", "verdict"):
        if k not in seen:
            cols.append(k)

    out = batch_dir / "eval_summary.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for row in rows:
            w.writerow({c: row.get(c, "") for c in cols})


def _write_details_jsonl(batch_dir: Path, results: List[JobResult]) -> None:
    out = batch_dir / "eval_details.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r.to_full_dict(), ensure_ascii=False) + "\n")


def _write_report_md(batch_dir: Path, task_id: str, results: List[JobResult]) -> None:
    out = batch_dir / "eval_report.md"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

  # Sort by task_score descending
    ranked = sorted(results, key=lambda r: -r.task_score)

    lines: list[str] = []
    lines.append(f"# Evaluation report - {task_id} - `{batch_dir.name}`")
    lines.append("")
    lines.append(f"_Generated: {now}_")
    lines.append("")

    # ---- Leaderboard ----
    lines.append("## Model ranking")
    lines.append("")
    lines.append("| Rank | Model | TaskScore | Outcome | Adherence | Process | TaskCompletion | Verdict |")
    lines.append("|---|---|---:|---:|---:|---:|---:|:---:|")
    for i, r in enumerate(ranked, 1):
        tc = r.extras.get("task_completion_accuracy", 0.0)
        lines.append(
            f"| {i} | `{r.model}` | **{r.task_score:.3f}** "
            f"| {r.outcome_score:.3f} | {r.adherence_score:.3f} | {r.process_score:.3f} "
            f"| {tc:.3f} "
            f"| `{r.verdict}` |"
        )
    lines.append("")

    # ---- Per-model details ----
    lines.append("## Per-model rubric hits")
    lines.append("")
    for r in ranked:
        lines.append(f"### `{r.model}` - TaskScore={r.task_score:.3f} ({r.verdict})")
        lines.append("")
        if "error" in r.extras:
            lines.append(f"> WARNING: evaluation error: {r.extras['error']}")
            lines.append("")
        lines.append(f"**Outcome** ({r.outcome_score:.3f})")
        lines.append("")
        lines.extend(_render_checks(r.outcome))
        lines.append("")
        lines.append(f"**Adherence** ({r.adherence_score:.3f}) · "
                     f"must-do hit {sum(1 for c in r.must_do if c.passed is True)}/"
                     f"{len(r.must_do)}; must-not triggered "
                     f"{sum(1 for c in r.must_not if c.passed is True)}/{len(r.must_not)}")
        lines.append("")
        lines.extend(_render_checks(r.must_do, kind="MD"))
        lines.extend(_render_checks(r.must_not, kind="MN"))
        lines.append("")
        lines.append(f"**Process** ({r.process_score:.3f})")
        lines.append("")
        lines.extend(_render_checks(r.process))
        lines.append("")
        lines.append("---")
        lines.append("")

    out.write_text("\n".join(lines), encoding="utf-8")


def _render_checks(checks, kind: str = "") -> list[str]:
    out: list[str] = []
    for c in checks:
        if c.passed is True:
            mark = "[X] triggered" if kind == "MN" else "[OK]"
        elif c.passed is False:
            mark = "[OK] not triggered" if kind == "MN" else "[X]"
        else:
            mark = "-"
        det = c.detail.strip().replace("\n", " ")
        if len(det) > 120:
            det = det[:117] + "..."
        out.append(f"- `{c.id}` {mark} {det}")
    return out
