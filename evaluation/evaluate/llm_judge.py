"""LLM judge abstraction.

A default offline heuristic judge is provided: it makes approximate decisions
based on keyword matching, has no external dependencies and works out of the
box. When a real LLM client is available, it can be swapped in for a
higher-quality judge.

Usage:

    from evaluate.llm_judge import HeuristicJudge
    judge = HeuristicJudge()
    answer = (job_dir / "answer.txt").read_text(...)
    yes, reason = judge.ask("MD4", answer)

Plugging in a real LLM (example):

    class MyJudge:
        def ask(self, qid: str, agent_response: str) -> tuple[bool, str]:
  ...  # call your own OpenAI / Claude client
        return yes_no, reason
"""
from __future__ import annotations

from typing import Tuple


class HeuristicJudge:
    """Keyword-based offline judge; only handles the registered qids."""

    def ask(self, qid: str, agent_response: str, **ctx) -> Tuple[bool, str]:
        text = (agent_response or "")
        low  = text.lower()

        if qid == "MD4":
            # Does the response explain that "table extraction should prefer pdfplumber"?
            mentions_pp = "pdfplumber" in low
            mentions_reason = any(k in low for k in [
                "table extraction",
                "for table", "table-aware", "table extract", "designed for", "suitable",
                "extract table", "recommend", "preferred", "better",
            ])
            ok = mentions_pp and mentions_reason
            if not mentions_pp:
                return False, "pdfplumber not mentioned"
            if not mentions_reason:
                return False, "no rationale given (missing keywords such as suitable/recommend/preferred)"
            return True, "pdfplumber mentioned with a rationale"

        if qid == "MN3":
            # Give-up style answer (penalty triggered on match)
            quit_kw = [
                "cannot read", "unable to read", "unable to complete",
                "i am unable", "i'm unable", "give up",
                "cannot process", "unable to process",
            ]
            hit = next((k for k in quit_kw if k in low), None)
            if hit:
                return True, f"matched give-up phrase: {hit!r}"
            return False, "no clear give-up phrase detected"

        if qid == "P2":
            # Does the response identify at least one formatting trap and its handling?
            traps = {
                "no vertical separator": ["no vertical", "no vertical line",
                         "vertical separator"],
                "$ in its own column":   ["dollar sign", "$ in separate",
                        "$ column"],
                "multi-line cell":       ["multi-line cell", "multiline",
                              "spans two lines", "wrapped row"],
                "em-dash":               ["em-dash", "em dash"],
                "thousands separator":   ["thousands separator", "comma separator"],
            }
            hits = [name for name, kws in traps.items() if any(k.lower() in low for k in kws)]
            if hits:
                return True, "detected traps: " + " / ".join(hits[:3])
            return False, "no formatting trap mentioned"

        # Unknown qid: equivalent to None (return False with an "unknown" reason)
        return False, f"unknown qid: {qid}"


def make_default_judge():
    """Evaluators use HeuristicJudge by default; callers may swap in another judge."""
    return HeuristicJudge()
