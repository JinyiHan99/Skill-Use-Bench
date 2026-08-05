"""Common base class and data structures for every task evaluator."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


# ---------------------------- Data structures ----------------------------


@dataclass
class CheckResult:
    """Result for a single rubric item."""
    id: str                       # e.g. "O1" / "MD3" / "MN2" / "P1"
    passed: Optional[bool]        # True=hit / False=miss / None=N/A (data missing)
    detail: str = ""              # short reason (<= 80 chars)

    def __post_init__(self) -> None:
        # Guard against numpy.bool_ etc. that break downstream `is True` checks / JSON serialization
        if self.passed is not None:
            self.passed = bool(self.passed)

    def to_dict(self) -> dict:
        return {"id": self.id, "passed": self.passed, "detail": self.detail}


@dataclass
class JobResult:
    """Complete evaluation result for a single model job."""
    task_id: str
    model: str
    job_dir: Path

    outcome:   List[CheckResult] = field(default_factory=list)   # O*
    must_do:   List[CheckResult] = field(default_factory=list)   # MD*
    must_not:  List[CheckResult] = field(default_factory=list)   # MN* (passed=True means the penalty was **triggered**)
    process:   List[CheckResult] = field(default_factory=list)   # P*

    # Aggregate scores
    outcome_score:   float = 0.0
    adherence_score: float = 0.0
    process_score:   float = 0.0
    task_score:      float = 0.0
    verdict:         str   = "fail"

    # Extra metadata (optional)
    extras: Dict[str, object] = field(default_factory=dict)

    # ---- Aggregation --------------------------------------------------
    def compute_scores(self,
                       weights: tuple[float, float, float] = (0.30, 0.50, 0.20),
                       pass_threshold: float = 0.70,
                       adherence_threshold: float = 0.6) -> None:
        """Compute the overall score and verdict from outcome/must_do/must_not/process."""
        # Outcome: mean of bools (None entries skipped)
        self.outcome_score   = _mean_passed(self.outcome)

        # Adherence: max(0, ΣMD - ΣMN) / |MD|
        md_hit = sum(1 for c in self.must_do  if c.passed is True)
        md_total = len([c for c in self.must_do  if c.passed is not None]) or len(self.must_do) or 1
        mn_hit = sum(1 for c in self.must_not if c.passed is True)
        self.adherence_score = max(0.0, (md_hit - mn_hit) / md_total)

        # Process: mean of bools (None entries skipped; all-None counts as 0)
        self.process_score   = _mean_passed(self.process)

        wO, wA, wP = weights
        self.task_score = (wO * self.outcome_score
                           + wA * self.adherence_score
                           + wP * self.process_score)

        if self.task_score >= pass_threshold and self.adherence_score >= adherence_threshold:
            self.verdict = "pass"
        elif self.task_score >= pass_threshold:
            self.verdict = "outcome-pass"
        else:
            self.verdict = "fail"

        # Task Completion Accuracy (pass rate over outcome items)
        tc_items = [c for c in self.outcome if c.passed is not None]
        if tc_items:
            tc_passed = sum(1 for c in tc_items if c.passed is True)
            self.extras["task_completion_accuracy"] = round(tc_passed / len(tc_items), 4)
            self.extras["task_completion_passed"] = tc_passed
            self.extras["task_completion_total"] = len(tc_items)
        else:
            self.extras["task_completion_accuracy"] = 0.0
            self.extras["task_completion_passed"] = 0
            self.extras["task_completion_total"] = 0

    # ---- Serialization ------------------------------------------------
    def to_flat_dict(self) -> dict:
        """Flatten to a CSV-friendly row: one column per rubric item (0/1/-)."""
        out: dict[str, object] = {
            "task_id": self.task_id,
            "model":   self.model,
        }
        for c in self.outcome + self.must_do + self.must_not + self.process:
            out[c.id] = _bool_cell(c.passed)
        out.update({
            "outcome":   round(self.outcome_score,   4),
            "adherence": round(self.adherence_score, 4),
            "process":   round(self.process_score,   4),
            "task_score": round(self.task_score,     4),
            "task_completion": round(self.extras.get("task_completion_accuracy", 0.0), 4),
            "verdict":   self.verdict,
        })
        return out

    def to_full_dict(self) -> dict:
        return {
            "task_id":   self.task_id,
            "model":     self.model,
            "job_dir":   str(self.job_dir),
            "outcome":   [c.to_dict() for c in self.outcome],
            "must_do":   [c.to_dict() for c in self.must_do],
            "must_not":  [c.to_dict() for c in self.must_not],
            "process":   [c.to_dict() for c in self.process],
            "scores": {
                "outcome":   round(self.outcome_score,   4),
                "adherence": round(self.adherence_score, 4),
                "process":   round(self.process_score,   4),
                "task_score": round(self.task_score,     4),
            },
            "verdict": self.verdict,
            "extras":  self.extras,
        }


def _mean_passed(checks: List[CheckResult]) -> float:
    vals = [1.0 if c.passed else 0.0 for c in checks if c.passed is not None]
    if not vals:
        return 0.0
    return sum(vals) / len(vals)


def _bool_cell(passed: Optional[bool]) -> str:
    if passed is None:
        return "-"
    return "1" if passed else "0"


# ---------------------------- Abstract base ------------------------------


class BaseEvaluator:
    """Base class for every task evaluator.

    Subclasses must provide:
      - class attribute task_id (e.g. "T01")
      - implementation of evaluate(job_dir) -> JobResult
    """

    task_id: str = ""

    def __init__(self,
                 repo_root: Path,
                 use_llm_judge: bool = False,
                 llm_judge=None) -> None:
        self.repo_root = repo_root
        self.use_llm_judge = use_llm_judge
        self.llm_judge = llm_judge

    def evaluate(self, job_dir: Path, model: str) -> JobResult:  # pragma: no cover
        raise NotImplementedError
