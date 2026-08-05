#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
score_trace.py v2 —— 用 rubric.yaml 给一条 trace.jsonl 打分。

核心特性
========
1. 自动识别两种 trace 格式：
   - chat 模拟格式（v1 的 mvp/_scripts/run_trace.py 输出）
   - Claude Code stream-json 格式（batch_run_eval/tasks/run_task.sh 输出，主路径）
2. 三类 verifier：
   - regex      : 直接在 trace 上做正则匹配（适合字面量明确的规则）
   - state-diff : 检查容器 cwd 拷出的文件最终状态（需 --job-dir）
   - llm-judge  : 调外部 LLM 对 trace 段做语义判断（默认 gpt-5）
3. 不再依赖 gold_trace 做对比；rubric 是唯一的 skill-following 判定口径。

rubric 字段（v2）
=================
- id: r1
  type: required-tool / forbidden-tool / order / required-arg / boundary /
        lesson / termination / trigger-condition
  locus: tool-call / tool-arg / file-state / final-output
  verifier: regex | state-diff | llm-judge
  severity: hard | soft
  exclusive: true | false          # (legacy alias: anti_prior)
  weight: 1.0
  spec: |
    人话描述（也作为 LLM-judge 的判定依据）
  signal:
    # —— regex verifier 字段 —— #
    pattern: "<regex on serialized step>"
    must_not_match: "<regex>"
    first_step_pattern: "<regex>"
    must_appear_before: ["<regex_a>", "<regex_b>"]
    in_final_answer: "<regex>"
    forbidden_in_final_answer: "<regex>"

    # —— state-diff verifier 字段（locus=file-state）—— #
    file: "outputs/SF02/filters.py"        # 相对 job-dir
    file_must_contain: "<regex>"
    file_must_not_contain: "<regex>"

    # —— llm-judge verifier 字段 —— #
    judge_question: |
      Yes/No question to ask the judge model. Should answer ONLY YES or NO.
    judge_context_window:                  # 喂给 judge 的上下文范围
      - serialized_steps                   # 默认：所有 step 的 tool/args/intent
      - final_answer                       # 模型最终回复
      - tool_results_first_n: 3            # 前 N 个 tool_result 的内容
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sys
import textwrap
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


# ──────────────────────────────────────────────────────────────────────
# 0. YAML loading
# ──────────────────────────────────────────────────────────────────────
def _parse_yaml(text: str) -> dict:
    try:
        import yaml  # type: ignore
        data = yaml.safe_load(text)
        return data or {}
    except ImportError:
        return _mini_yaml(text)


def _mini_yaml(text: str) -> dict:
    """Tiny fallback parser for the simple rubric/task YAML used by this MVP."""
    lines = text.splitlines()
    root: dict = {}
    stack: list[tuple[int, object]] = [(-1, root)]
    i = 0
    while i < len(lines):
        raw = lines[i]
        stripped = raw.rstrip()
        if not stripped.strip() or stripped.lstrip().startswith("#"):
            i += 1
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        while stack and indent <= stack[-1][0]:
            if len(stack) == 1:
                break
            stack.pop()
        _, parent = stack[-1]
        line = stripped.strip()
        if line.startswith("- "):
            item = line[2:].strip()
            if not isinstance(parent, list):
                raise ValueError(f"unexpected list item at line {i+1}: {raw!r}")
            if ":" in item:
                k, _, v = item.partition(":")
                d: dict = {k.strip(): _parse_scalar(v.strip()) if v.strip() else None}
                parent.append(d)
                stack.append((indent, d))
            else:
                parent.append(_parse_scalar(item))
            i += 1
            continue
        if ":" not in line:
            raise ValueError(f"unrecognized line {i+1}: {raw!r}")
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        if val == "" or val is None:
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines):
                nxt = lines[j]
                nxt_indent = len(nxt) - len(nxt.lstrip(" "))
                container: object = [] if nxt_indent > indent and nxt.strip().startswith("- ") else {}
            else:
                container = {}
            if not isinstance(parent, dict):
                raise ValueError(f"key in non-dict parent at line {i+1}")
            parent[key] = container
            stack.append((indent, container))
            i += 1
            continue
        if val in ("|", ">", "|-", ">-"):
            block_lines: list[str] = []
            j = i + 1
            base_indent = None
            while j < len(lines):
                ln = lines[j]
                if not ln.strip():
                    block_lines.append("")
                    j += 1
                    continue
                ln_indent = len(ln) - len(ln.lstrip(" "))
                if ln_indent <= indent:
                    break
                if base_indent is None:
                    base_indent = ln_indent
                block_lines.append(ln[base_indent:] if base_indent else ln)
                j += 1
            block_text = "\n".join(block_lines).rstrip("\n")
            if val.startswith(">"):
                block_text = " ".join(s for s in block_text.split("\n") if s)
            if isinstance(parent, dict):
                parent[key] = block_text
            i = j
            continue
        if isinstance(parent, dict):
            parent[key] = _parse_scalar(val)
        i += 1
    return root


def _parse_scalar(s: str):
    if s == "" or s is None:
        return None
    if s.lower() == "true":
        return True
    if s.lower() == "false":
        return False
    if s.lower() in ("null", "~"):
        return None
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    return s


# ──────────────────────────────────────────────────────────────────────
# 1. Trace loading & normalization
# ──────────────────────────────────────────────────────────────────────
def load_trace(p: Path) -> dict:
    """
    Returns a normalized trace dict:
      {
        "format": "chat-sim" | "claude-stream" | "codex-stream",
        "meta": {...},
        "steps": [{"tool": str, "args": str|dict, "intent": str, "result": str|None}],
        "final_answer": str,
        "system_init": dict | None,        # claude-stream / codex-stream
        "raw_lines": [...]                 # for llm-judge full context
      }
    """
    lines = []
    for raw in p.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s:
            continue
        try:
            lines.append(json.loads(s))
        except Exception:
            continue
    if not lines:
        return {"format": "empty", "meta": {}, "steps": [], "final_answer": "",
                "system_init": None, "raw_lines": []}
    # 判断格式
    first = lines[0]
    if first.get("type") == "system" and first.get("subtype") == "init":
        return _normalize_claude_stream(lines)
    if first.get("type") == "thread.started":
        return _normalize_codex_stream(lines, trace_path=p)
    return _normalize_chat_sim(lines)


def _normalize_chat_sim(lines: list[dict]) -> dict:
    meta = {}
    raw = ""
    steps = []
    for o in lines:
        if o.get("_meta"):
            meta = o
        elif o.get("_raw_response"):
            raw = o.get("text", "")
        elif "tool" in o:
            steps.append({
                "tool": o.get("tool", ""),
                "args": o.get("args", ""),
                "intent": o.get("intent", ""),
                "result": None,
            })
    final_answer = ""
    for s in steps:
        if s["tool"] == "final_answer":
            a = s["args"]
            final_answer = a if isinstance(a, str) else json.dumps(a, ensure_ascii=False)
            break
    if not final_answer:
        final_answer = raw
    return {"format": "chat-sim", "meta": meta, "steps": steps,
            "final_answer": final_answer, "system_init": None, "raw_lines": lines}


def _normalize_codex_stream(lines: list[dict], *, trace_path: Path | None = None) -> dict:
    """
    Normalize Codex CLI trace (thread.started / item.started / item.completed / turn.*)
    into the same step-list shape used by claude-stream.

    Codex trace format:
      - Lines with type="item.completed" and item.type="command_execution" → steps (tool="Bash")
      - Lines with type="item.completed" and item.type="agent_message" → final_answer text
      - Lines with type="item.completed" and item.type="reasoning" → skipped (internal CoT)
      - Lines with type="turn.completed" → marks end of a turn

    Skill injection in Codex:
      Codex CLI uses .codex/skills/<name>/SKILL.md — the same progressive-disclosure
      mechanism as Claude Code's .claude/skills/. Codex shows only the skill name +
      description in the system prompt; the model must actively read the SKILL.md file
      to obtain the full skill content. This makes the trigger semantics equivalent
      to Claude Code: did the model actively access the skill content?
    """
    ordered_steps: list[dict] = []
    final_answer_parts: list[str] = []
    num_turns = 0

    for o in lines:
        t = o.get("type", "")
        item = o.get("item", {})
        item_type = item.get("type", "")

        if t == "item.completed":
            if item_type == "command_execution":
                command = item.get("command", "")
                output = item.get("aggregated_output", "")
                exit_code = item.get("exit_code")
                status = item.get("status", "")

                # Map to Bash tool step (consistent with claude-stream's tool naming)
                step = {
                    "tool": "Bash",
                    "args": {"command": command},
                    "intent": "",
                    "result": output,
                    "_codex_exit_code": exit_code,
                    "_codex_status": status,
                }
                ordered_steps.append(step)

            elif item_type == "agent_message":
                text = item.get("text", "")
                if text:
                    final_answer_parts.append(text)

            # reasoning, error, todo_list — skip (not actionable steps)

        elif t == "turn.completed":
            num_turns += 1

    final_answer = "\n\n".join(final_answer_parts)

    # ── Detect skill registration via .codex/skills/*/SKILL.md ──
    # Codex CLI's native skill mechanism: skills placed in .codex/skills/<name>/SKILL.md
    # are listed (name + description only) in the system prompt. The model must actively
    # read SKILL.md to get the full content — same progressive-disclosure as Claude Code.
    skills_registered: list[str] = []
    tools_available: list[str] = ["Bash"]  # Codex CLI always has shell access
    skill_files: dict[str, str] = {}  # skill_name -> SKILL.md path

    if trace_path is not None:
        job_dir = trace_path.parent
        # Search skill directories in both layouts:
        #   - .codex/skills/       (old / claude-code-compatible layout)
        #   - .codex_home/skills/  (codex-native harness: $CODEX_HOME=.codex_home)
        candidate_skill_dirs = [
            job_dir / ".codex" / "skills",
            job_dir / ".codex_home" / "skills",
        ]
        skills_dir = next((d for d in candidate_skill_dirs if d.is_dir()), None)
        if skills_dir is not None:
            for skill_subdir in skills_dir.iterdir():
                if skill_subdir.is_dir() and skill_subdir.name != ".system":
                    skill_md = skill_subdir / "SKILL.md"
                    if skill_md.exists():
                        # Extract skill name from YAML frontmatter
                        skill_name = skill_subdir.name  # fallback: directory name
                        try:
                            content = skill_md.read_text(encoding="utf-8", errors="replace")
                            if content.startswith("---"):
                                end = content.find("---", 3)
                                if end > 0:
                                    for line in content[3:end].splitlines():
                                        line = line.strip()
                                        if line.startswith("name:"):
                                            parsed = line[5:].strip().strip('"').strip("'")
                                            if parsed:
                                                skill_name = parsed
                                            break
                        except Exception:
                            pass
                        skills_registered.append(skill_name)
                        skill_files[skill_name] = str(skill_md)

        # Backward compatibility: also check .codex/instructions.md (old injection method)
        instructions_md = job_dir / ".codex" / "instructions.md"
        if instructions_md.exists() and not skills_registered:
            try:
                content = instructions_md.read_text(encoding="utf-8", errors="replace")
                if content.startswith("---"):
                    end = content.find("---", 3)
                    if end > 0:
                        for line in content[3:end].splitlines():
                            line = line.strip()
                            if line.startswith("name:"):
                                parsed = line[5:].strip().strip('"').strip("'")
                                if parsed:
                                    skills_registered.append(parsed)
                                    skill_files[parsed] = str(instructions_md)
                                break
            except Exception:
                pass

    # Build a synthetic system_init compatible with claude-stream format
    system_init = {
        "type": "system",
        "subtype": "init",
        "tools": tools_available,
        "skills": skills_registered,
        "_codex_skill_files": skill_files,
        "_synthetic": True,  # Flag: this was constructed, not from trace
    }

    meta = {
        "skills_registered": skills_registered,
        "tools_available": tools_available,
        "num_turns": num_turns,
        "_codex_skill_files": skill_files,
    }

    return {
        "format": "codex-stream",
        "meta": meta,
        "steps": ordered_steps,
        "final_answer": final_answer,
        "system_init": system_init,
        "raw_lines": lines,
    }


def _normalize_claude_stream(lines: list[dict]) -> dict:
    """
    Normalize Claude Code stream-json into the same step list shape.
    Each tool_use becomes one step; matching tool_result fills `result`.
    """
    system_init = lines[0]
    in_progress: dict[int, dict] = {}     # block_index -> {id, name, parts}
    steps_by_id: dict[str, dict] = {}     # tool_use_id -> step
    ordered_steps: list[dict] = []
    final_answer = ""
    final_meta = {}

    for o in lines:
        t = o.get("type")
        if t == "stream_event":
            ev = o.get("event", {})
            et = ev.get("type")
            idx = ev.get("index")
            if et == "content_block_start":
                cb = ev.get("content_block", {})
                if cb.get("type") == "tool_use":
                    in_progress[idx] = {
                        "id": cb.get("id"),
                        "name": cb.get("name", ""),
                        "parts": [],
                    }
            elif et == "content_block_delta" and idx in in_progress:
                d = ev.get("delta", {})
                if d.get("type") == "input_json_delta":
                    in_progress[idx]["parts"].append(d.get("partial_json", ""))
            elif et == "content_block_stop" and idx in in_progress:
                blk = in_progress.pop(idx)
                full = "".join(blk["parts"])
                try:
                    parsed = json.loads(full) if full else {}
                except Exception:
                    parsed = {"_raw": full}
                step = {
                    "tool": blk["name"],
                    "args": parsed,
                    "intent": "",
                    "result": None,
                    "_id": blk["id"],
                }
                steps_by_id[blk["id"]] = step
                ordered_steps.append(step)
        elif t == "user":
            # tool_result —— 注入到匹配的 step
            msg = o.get("message", {})
            content = msg.get("content", [])
            if isinstance(content, list):
                for c in content:
                    if isinstance(c, dict) and c.get("type") == "tool_result":
                        tid = c.get("tool_use_id")
                        rc = c.get("content", "")
                        if isinstance(rc, list):
                            rc = "\n".join(
                                (x.get("text", "") if isinstance(x, dict) else str(x))
                                for x in rc
                            )
                        if tid in steps_by_id:
                            steps_by_id[tid]["result"] = rc
        elif t == "result":
            final_answer = o.get("result", "") or ""
            final_meta = {
                "subtype": o.get("subtype"),
                "is_error": o.get("is_error"),
                "num_turns": o.get("num_turns"),
                "total_cost_usd": o.get("total_cost_usd"),
            }

    meta = {
        "model": system_init.get("model"),
        "session_id": system_init.get("session_id"),
        "skills_registered": system_init.get("skills", []),
        "tools_available": system_init.get("tools", []),
        "result_meta": final_meta,
    }
    return {"format": "claude-stream", "meta": meta, "steps": ordered_steps,
            "final_answer": final_answer, "system_init": system_init,
            "raw_lines": lines}


# ──────────────────────────────────────────────────────────────────────
# 2. Step serialization (a unified text view for regex / llm-judge)
# ──────────────────────────────────────────────────────────────────────
def serialize_step(step: dict, include_result: bool = False) -> str:
    args = step.get("args", "")
    if not isinstance(args, str):
        args = json.dumps(args, ensure_ascii=False)
    intent = step.get("intent", "") or ""
    base = f"{step.get('tool', '')}:{args}:{intent}"
    if include_result and step.get("result"):
        r = step["result"]
        if not isinstance(r, str):
            r = json.dumps(r, ensure_ascii=False)
        base += f"|RESULT:{r[:300]}"
    return base


# ──────────────────────────────────────────────────────────────────────
# 3. Verifiers
# ──────────────────────────────────────────────────────────────────────
def _verify_regex(item: dict, trace: dict) -> tuple[bool, str]:
    sig = item.get("signal") or {}
    # 兼容层 1：rubric 中 pattern/must_not_match 等放在 item 顶层（无 signal 嵌套）的写法
    if not sig:
        _compat_keys = ("pattern", "must_not_match", "first_step_pattern",
                        "must_appear_before", "in_final_answer", "forbidden_in_final_answer")
        compat = {k: item[k] for k in _compat_keys if k in item}
        if compat:
            # 对于 forbidden-tool / forbidden-arg 类型，顶层 pattern 语义是"不应出现"
            item_type = (item.get("type") or "").lower()
            if item_type in ("forbidden-tool", "forbidden-arg") and "pattern" in compat and "must_not_match" not in compat:
                compat["must_not_match"] = compat.pop("pattern")
            sig = compat
    # 兼容层 2：regex 模式写在 spec 文本中（如 "regex: (pattern)" 或 "regex pattern: ..."）
    if not sig:
        spec_text = item.get("spec") or ""
        item_type = (item.get("type") or "").lower()
        # 匹配多种写法：
        #   "regex: <pattern>"
        #   "regex pattern: <pattern>"
        #   "regex (不应出现): <pattern>"
        #   "negative regex (不应出现): <pattern>"
        # 策略：找到所有 regex 行，第一个非 negative 行作为 pattern，negative 行作为 must_not_match
        _regex_lines = re.findall(
            r'(?:^|\n)\s*((?:negative\s+)?regex(?:\s+pattern|\s*[\(（][^)）]*[\)）])?)\s*[:：]\s*(.+?)(?:\n|$)',
            spec_text, re.I)
        if _regex_lines:
            patterns = []
            forbidden_patterns = []
            for prefix, pat_str in _regex_lines:
                pat_str = pat_str.strip()
                prefix_lower = prefix.lower()
                is_neg_line = ("negative" in prefix_lower or "不应出现" in prefix
                               or "forbidden" in prefix_lower)
                if is_neg_line:
                    forbidden_patterns.append(pat_str)
                else:
                    patterns.append(pat_str)
            # 根据 item type 决定最终语义
            if item_type in ("forbidden-tool", "forbidden-arg", "boundary"):
                # forbidden 类型：优先取 negative regex，否则把 positive 也当 must_not_match
                mnm = forbidden_patterns[0] if forbidden_patterns else (patterns[0] if patterns else None)
                if mnm:
                    sig = {"must_not_match": mnm}
            else:
                # positive 类型：取 positive regex 作为 pattern
                built = {}
                if patterns:
                    built["pattern"] = patterns[0]
                if forbidden_patterns:
                    built["must_not_match"] = forbidden_patterns[0]
                if built:
                    sig = built
    tool_signal_keys = {
        "command_pattern",
        "command_all_patterns",
        "command_must_not_match",
        "ignore_comments",
        "forbid_range_on_files",
        "require_after_each",
        "last_command_ok",
    }
    if any(k in sig for k in tool_signal_keys):
        passed, reason = _verify_tool_call({"signal": sig}, trace)
        if not passed:
            return False, reason
        sig = {k: v for k, v in sig.items() if k not in tool_signal_keys}

    serialized = [serialize_step(s) for s in trace["steps"]]
    final_ans = trace["final_answer"]

    # ── 正则匹配（带超时保护，防止灾难性回溯） ──
    import signal as _signal

    class _RegexTimeout(Exception):
        pass

    def _regex_alarm(signum, frame):
        raise _RegexTimeout("regex timed out")

    _REGEX_TIMEOUT = 10  # 单次正则匹配最多 10 秒

    def _safe_search(pat, text):
        """带超时的 re.search，防止 catastrophic backtracking。"""
        old = _signal.signal(_signal.SIGALRM, _regex_alarm)
        _signal.alarm(_REGEX_TIMEOUT)
        try:
            return pat.search(text)
        except _RegexTimeout:
            return None
        finally:
            _signal.alarm(0)
            _signal.signal(_signal.SIGALRM, old)

    if "pattern" in sig:
        pat = re.compile(sig["pattern"], re.I | re.S)
        if not any(_safe_search(pat, s) for s in serialized):
            return False, f"no step matches pattern {sig['pattern']!r}"
    if "must_not_match" in sig:
        pat = re.compile(sig["must_not_match"], re.I | re.S)
        hits = [s for s in serialized if _safe_search(pat, s)]
        if hits:
            return False, f"forbidden pattern matched {len(hits)}x; first: {hits[0][:140]!r}"
    if "first_step_pattern" in sig:
        if not serialized:
            return False, "no steps at all"
        pat = re.compile(sig["first_step_pattern"], re.I | re.S)
        if not pat.search(serialized[0]):
            return False, f"first step {serialized[0][:140]!r} did not match {sig['first_step_pattern']!r}"
    if "must_appear_before" in sig:
        a, b = sig["must_appear_before"]
        pa, pb = re.compile(a, re.I | re.S), re.compile(b, re.I | re.S)
        idx_a = next((i for i, s in enumerate(serialized) if pa.search(s)), None)
        idx_b = next((i for i, s in enumerate(serialized) if pb.search(s)), None)
        if idx_a is None or idx_b is None:
            return False, f"order: a_found={idx_a is not None} b_found={idx_b is not None}"
        if idx_a >= idx_b:
            return False, f"order violation: a@{idx_a} not before b@{idx_b}"
    if "in_final_answer" in sig:
        pat = re.compile(sig["in_final_answer"], re.I | re.S)
        if not pat.search(final_ans):
            return False, f"final_answer missing {sig['in_final_answer']!r}"
    if "forbidden_in_final_answer" in sig:
        pat = re.compile(sig["forbidden_in_final_answer"], re.I | re.S)
        if pat.search(final_ans):
            return False, f"final_answer contains forbidden {sig['forbidden_in_final_answer']!r}"
    return True, ""


def _verify_state_diff(item: dict, trace: dict, job_dir: Path | None) -> tuple[bool, str]:
    sig = item.get("signal") or {}
    if not job_dir:
        return False, "state-diff verifier requires --job-dir"
    rel = sig.get("file")
    if not rel:
        return False, "state-diff signal.file missing"
    p = (job_dir / rel)
    if not p.exists():
        return False, f"file does not exist: {rel}"
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return False, f"file unreadable: {e}"
    if "file_must_contain" in sig:
        import signal as _sig2
        class _RxTO2(Exception): pass
        def _h2(sn, f): raise _RxTO2()
        # 支持 file_must_contain 为列表（多个 pattern 全部匹配）或单字符串
        patterns_contain = sig["file_must_contain"]
        if isinstance(patterns_contain, str):
            patterns_contain = [patterns_contain]
        for pat_str in patterns_contain:
            old2 = _sig2.signal(_sig2.SIGALRM, _h2)
            _sig2.alarm(10)
            try:
                matched = re.search(pat_str, text, re.I | re.S)
            except _RxTO2:
                matched = None
            finally:
                _sig2.alarm(0)
                _sig2.signal(_sig2.SIGALRM, old2)
            if not matched:
                return False, f"file missing pattern {pat_str!r}"
    if "file_must_not_contain" in sig:
        import signal as _sig3
        class _RxTO3(Exception): pass
        def _h3(sn, f): raise _RxTO3()
        # 支持 file_must_not_contain 为列表或单字符串
        patterns_forbid = sig["file_must_not_contain"]
        if isinstance(patterns_forbid, str):
            patterns_forbid = [patterns_forbid]
        for pat_str2 in patterns_forbid:
            old3 = _sig3.signal(_sig3.SIGALRM, _h3)
            _sig3.alarm(10)
            try:
                matched2 = re.search(pat_str2, text, re.I | re.S)
            except _RxTO3:
                matched2 = None
            finally:
                _sig3.alarm(0)
                _sig3.signal(_sig3.SIGALRM, old3)
            if matched2:
                return False, f"file contains forbidden {pat_str2!r}"
    return True, ""


def _verify_state_check(item: dict, trace: dict, job_dir: Path | None,
                         rubric_meta: dict) -> tuple[bool, str]:
    """State-check verifier for v3 rubrics (SF04+).

    Uses rubric_meta (artifact_main, task_id, artifact_anchor) and item's
    verifier_detail.state_check to do AST/regex checks on final workspace files.
    Also dispatches OOXML/PPTX artifact checks expressed as state-check signals.
    """
    sig = item.get("signal") or {}
    if isinstance(sig, dict) and ("output_candidates" in sig or sig.get("must_be_valid_ooxml")):
        return _verify_pptx(item, trace, job_dir)

    import ast as _ast
    import glob as _glob

    if not job_dir:
        return False, "state-check verifier requires --job-dir"

    task_id = rubric_meta.get("task_id", "")
    artifact_main = rubric_meta.get("artifact_main", "")
    artifact_anchor = rubric_meta.get("artifact_anchor", "")

    # Locate the target file in job_dir. Try multiple search paths:
    #   1) job_dir / artifact_main
    #   2) job_dir / assets / <task_id> / artifact_main
    #   3) glob pattern from verifier_detail
    target_file = None
    if artifact_main:
        candidates = [
            job_dir / artifact_main,
            job_dir / "assets" / task_id / artifact_main,
        ]
        for c in candidates:
            if c.exists():
                target_file = c
                break

    # If not found via artifact_main, try glob from verifier_detail
    if not target_file:
        vd = item.get("verifier_detail", {})
        state_check_desc = vd.get("state_check", "") if isinstance(vd, dict) else ""
        # Extract glob pattern like "glob **/separable.py"
        import re as _re
        glob_match = _re.search(r'glob\s+(\S+)', state_check_desc)
        if glob_match:
            pattern = glob_match.group(1)
            matches = list(job_dir.rglob(pattern.replace("**/", "")))
            if matches:
                target_file = matches[0]

    # For items that check a different file (e.g., README), try to find it
    item_id = item.get("id", "")
    spec = item.get("spec", "")

    # If this is a gate check, the main requirement is that the target file
    # exists and has meaningful content
    provenance = item.get("provenance", "")
    outcome_field = item.get("outcome_field", "")

    if provenance == "gate" or "evaluable" in item_id.lower():
        # Gate check: file must exist and have relevant content
        if not target_file or not target_file.exists():
            return False, f"target file not found (artifact_main={artifact_main!r})"
        try:
            content = target_file.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return False, f"cannot read target file: {e}"
        if not content.strip():
            return False, "target file is empty"

        # For Python files, try AST parse + check for docstring/class/function
        if target_file.suffix == ".py":
            try:
                tree = _ast.parse(content)
            except SyntaxError as e:
                return False, f"Python syntax error: {e}"

            # If artifact_anchor is specified, check it exists
            if artifact_anchor:
                import re as _re
                if not _re.search(artifact_anchor, content):
                    return False, f"anchor pattern not found: {artifact_anchor!r}"

            # Check for docstring presence (gate requirement)
            # Look for class/function with docstring OR _add_docstr calls with content
            has_docstring = False
            for node in _ast.walk(tree):
                if isinstance(node, (_ast.ClassDef, _ast.FunctionDef, _ast.AsyncFunctionDef)):
                    if (_ast.get_docstring(node)):
                        has_docstring = True
                        break
            # Also check for _add_docstr pattern (C-binding style)
            if not has_docstring:
                import re as _re2
                if _re2.search(r'_add_docstr\s*\(', content):
                    # File uses _add_docstr; check there's substantial string content
                    if _re2.search(r'(?:r"""|\"\"\"|r\'\'\'|\'\'\')', content):
                        has_docstring = True
            if not has_docstring:
                return False, "no docstring found in any class/function"
        # For non-Python (e.g., README.md)
        elif "readme" in item_id.lower() or "readme" in spec.lower():
            if len(content) < 50:
                return False, "README content too short"
        return True, ""

    # For non-gate items: skill-following checks
    # These need the target file content for regex/AST analysis
    if not target_file or not target_file.exists():
        return False, f"target file not found for state-check"
    try:
        content = target_file.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return False, f"cannot read: {e}"

    # Extract verifier_detail for pattern-based checks
    vd = item.get("verifier_detail", {})
    state_check_desc = vd.get("state_check", "") if isinstance(vd, dict) else ""
    import re as _re

    # Heuristic checks based on item id/spec patterns
    item_id_lower = item_id.lower()

    # --- Raw string check ---
    if "raw_string" in item_id_lower or "raw_string" in spec.lower():
        # Check for r""" or r''' prefix
        if not _re.search(r'(?:^|\n)\s*r(?:"""|' + "''')", content):
            return False, 'no raw string literal (r\"\"\"...\"\"\") found'

    # --- Section order check ---
    if "section_order" in item_id_lower or "order" in item_id_lower:
        # Check PyTorch section ordering: description before Args before Returns before Examples
        markers = []
        for marker_name, pattern in [
            ("math/ref", r'(?:\.\.\s*math::|:(?:class|func|meth):)'),
            ("Args", r'^\s*Args:\s*$'),
            ("Returns", r'^\s*Returns:\s*$'),
            ("Examples", r'^\s*Examples::\s*$'),
        ]:
            m = _re.search(pattern, content, _re.M)
            if m:
                markers.append((marker_name, m.start()))
        if len(markers) >= 2:
            positions = [pos for _, pos in markers]
            if positions != sorted(positions):
                return False, f"section order violated: {[n for n,_ in markers]}"

    # --- Args/Returns completeness ---
    if "args" in item_id_lower and "returns" in item_id_lower:
        if not _re.search(r'^\s*Args:\s*$', content, _re.M):
            return False, "Args section missing"
        if not _re.search(r'^\s*Returns:\s*$', content, _re.M):
            return False, "Returns section missing"

    # --- Math/rst format ---
    if "math" in item_id_lower or "rst" in item_id_lower:
        if not _re.search(r':math:`[^`]+`', content) and not _re.search(r'\.\.\s*math::', content):
            return False, "no :math: or .. math:: found"

    # --- Examples format ---
    if "examples" in item_id_lower or "doctest" in item_id_lower:
        if not _re.search(r'^\s*Examples::\s*$', content, _re.M):
            return False, "Examples:: header not found"
        if ">>>" not in content:
            return False, "no >>> doctest lines found"

    # --- Cross references ---
    if "cross_reference" in item_id_lower or "sphinx" in item_id_lower:
        # N/A if no related symbols mentioned
        related_symbols = ["Conv2d", "BatchNorm2d", "Module", "Tensor"]
        has_related = any(sym in content for sym in related_symbols)
        if not has_related:
            return True, "N/A: no related symbols referenced"
        if not _re.search(r':(?:class|func|meth|attr):`', content):
            return False, "related symbols referenced without Sphinx roles"

    # --- Must-not (forbidden patterns) ---
    if item.get("outcome_field") == "must_not" or "violation" in item_id_lower:
        # For MN items, "passed=True" means NO violations found.
        # Check for forbidden patterns
        violations = []
        forbidden_patterns = [
            (r'(?:^|\n)\s*(?:Arguments|Parameters|Params):', "non-PyTorch header"),
            (r'\[([^\]]+)\]\([^\)]+\)', "Markdown link"),
        ]
        for pat, desc in forbidden_patterns:
            if _re.search(pat, content):
                violations.append(desc)
        if violations:
            return False, f"violations found: {', '.join(violations)}"
        return True, ""

    # --- Task completion / artifact integrity ---
    if outcome_field == "outcome" or "artifact_integrity" in item_id_lower or "task_completion" in item_id_lower:
        # Basic check: file exists and is non-trivial
        if target_file.suffix == ".py":
            try:
                tree = _ast.parse(content)
                return True, ""
            except SyntaxError as e:
                return False, f"syntax broken: {e}"
        if len(content) > 50:
            return True, ""
        return False, "file too short for task completion"

    # --- Trigger check (P1) ---
    if "trigger" in item_id_lower and provenance == "skill":
        # Check if skill signals are present in the content
        signals = 0
        if _re.search(r'(?:^|\n)\s*r(?:"""|' + "''')", content):
            signals += 1
        if _re.search(r'^\s+\w+\s*\([^)]*\)\s*:', content, _re.M):
            signals += 1
        if _re.search(r':math:`', content):
            signals += 1
        if _re.search(r'\.\.\s*math::', content):
            signals += 1
        if _re.search(r':(?:class|func):`', content):
            signals += 1
        if _re.search(r'^\s*Examples::\s*$', content, _re.M):
            signals += 1

        # If this is a "no_trigger" boundary check, logic is inverted:
        # PASS when signals == 0 (no skill leakage into non-skill artifact)
        if "no_trigger" in item_id_lower or item.get("type") == "boundary":
            if signals == 0:
                return True, "no skill signals found in artifact (correct)"
            return False, f"found {signals} skill signal(s) in non-skill artifact (leakage)"

        # Normal positive trigger check
        if signals >= 2:
            return True, f"skill triggered ({signals} signals found)"
        return False, f"only {signals} skill signal(s) found, need ≥2"

    # Default: if we got here without failing, pass
    return True, ""


# ──────────────────────────────────────────────────────────────────────
# 3b. Structured action extraction (tool-call / command-context verifiers)
#
# 设计动机（见 skill_13_pptx/rubrics/RUBRIC_REVIEW_REPORT.md）：
#   原 regex verifier 把每个 step 序列化成 `tool:args:intent` 后做全文匹配，
#   会被模型的自述、计划文本、写入文件的注释污染（如一句"我要编辑 pptx embed
#   xml"即命中 g1，`# do not import pptx` 注释误触发 must_not_match）。
#   这里把 trace 还原成"真实工具调用"的结构化视图，让规则只锁定：
#     - Bash 命令字符串（真正执行的命令）
#     - Write/Edit/MultiEdit 写入的文件路径与正文
#     - Read 工具调用的目标文件与是否带 offset/limit 范围参数
#   从而把"命令上下文 / tool-call 结构化"校验落地，杜绝自然语言污染。
# ──────────────────────────────────────────────────────────────────────
_EDIT_TOOLS = {"write", "edit", "multiedit", "str_replace_editor", "create_file",
               "apply_patch", "fsedit"}
_READ_TOOLS = {"read", "read_file", "cat", "view"}


def _strip_inline_comments(text: str) -> str:
    """去掉 shell/python 风格的行内注释，避免 must_not_match 误伤注释。

    仅移除以 `#` 起头（或前面是空白）的注释片段；保留 `#` 出现在引号内的
    情况不做精细解析（对本 benchmark 的命令/代码足够）。
    """
    out_lines = []
    for ln in text.splitlines():
        # 跳过整行注释
        stripped = ln.lstrip()
        if stripped.startswith("#"):
            continue
        # 去掉行尾 ` # ...` 注释（# 前需是空白，降低误删字符串里 # 的概率）
        m = _re_inline_comment.search(ln)
        if m:
            ln = ln[:m.start()]
        out_lines.append(ln)
    return "\n".join(out_lines)


import re as _re_mod
_re_inline_comment = _re_mod.compile(r'(?:^|\s)#.*$')


def _extract_actions(trace: dict) -> dict:
    """把规范化 trace 还原成结构化工具调用视图。

    Returns:
      {
        "commands": [str, ...],                 # Bash/shell 命令原文
        "edits":    [{"path": str, "payload": str}, ...],
        "reads":    [{"path": str, "has_range": bool}, ...],
        "events":   [{"kind": "cmd"|"edit", "text": str, "ok": bool}, ...],
                    # 有序事件流，供"每次编辑后须验证"之类的序列校验使用
      }
    """
    commands: list[str] = []
    edits: list[dict] = []
    reads: list[dict] = []
    events: list[dict] = []

    for s in trace.get("steps", []):
        tool = (s.get("tool") or "").lower()
        args = s.get("args")
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except Exception:
                args = {"_raw": args}
        if not isinstance(args, dict):
            args = {}
        result = s.get("result")
        if result is not None and not isinstance(result, str):
            try:
                result = json.dumps(result, ensure_ascii=False)
            except Exception:
                result = str(result)
        ok = _result_ok(result)

        if tool == "bash" or tool == "shell" or tool == "run_command" or tool == "execute_command":
            cmd = args.get("command") or args.get("cmd") or args.get("_raw") or ""
            if isinstance(cmd, list):
                cmd = " ".join(str(x) for x in cmd)
            cmd = str(cmd)
            if cmd.strip():
                commands.append(cmd)
                events.append({"kind": "cmd", "text": "CMD " + cmd, "ok": ok})
                # Bash 中对 .xml/.rels 文件的写操作也产生 EDIT 事件，
                # 使 require_after_each trigger 能追踪 python/sed/cat/tee 方式的 XML 修改。
                # 判定逻辑：命令中涉及 .xml/.rels 且有写入证据。
                _has_xml_ref = _re_mod.search(r'\.(xml|rels)\b', cmd)
                if _has_xml_ref:
                    _write_evidence = _re_mod.search(
                        r'(?i)('
                        r'sed\s+-i'                    # sed -i (in-place edit)
                        r'|>\s*\S*\.(xml|rels)'        # redirect to .xml
                        r'|open\([^\)]*["\'][wa]'      # python open(... 'w'/'a')
                        r'|\.write\('                  # .write(
                        r'|ElementTree.*\.write\('     # ET.write()
                        r'|etree.*\.write\('           # lxml etree.write()
                        r'|tostring\('                 # etree.tostring (then write)
                        r'|replace\([^\)]*\)'          # str replace (in xml context)
                        r'|re\.sub\('                  # regex sub (modifying xml)
                        r'|shutil\.copy'               # copying modified xml
                        r')', cmd)
                    if _write_evidence:
                        full_m = _re_mod.search(r'[\w/\\\.\-]+\.(xml|rels)\b', cmd)
                        target_path = full_m.group(0) if full_m else "?.xml"
                        events.append({"kind": "edit",
                                       "text": f"EDIT {target_path} :: (bash-write)",
                                       "ok": ok})
        elif tool in _EDIT_TOOLS:
            path = (args.get("file_path") or args.get("path")
                    or args.get("filename") or args.get("target_file") or "")
            payload_parts = []
            for k in ("content", "new_string", "new_str", "file_text", "text"):
                v = args.get(k)
                if isinstance(v, str):
                    payload_parts.append(v)
            # MultiEdit: edits=[{new_string:...}, ...]
            edl = args.get("edits")
            if isinstance(edl, list):
                for e in edl:
                    if isinstance(e, dict):
                        for k in ("new_string", "new_str", "content"):
                            if isinstance(e.get(k), str):
                                payload_parts.append(e[k])
            payload = "\n".join(payload_parts)
            edits.append({"path": str(path), "payload": payload})
            events.append({"kind": "edit",
                           "text": f"EDIT {path} :: {payload}", "ok": ok})
        elif tool in _READ_TOOLS:
            path = (args.get("file_path") or args.get("path")
                    or args.get("filename") or args.get("_raw") or "")
            has_range = ("offset" in args and args.get("offset") not in (None, "", 0)) or \
                        ("limit" in args and args.get("limit") not in (None, "")) or \
                        ("start_line" in args) or ("end_line" in args) or \
                        ("line_range" in args) or ("range" in args)
            reads.append({"path": str(path), "has_range": bool(has_range)})

    return {"commands": commands, "edits": edits, "reads": reads, "events": events}


def _result_ok(result: str | None) -> bool:
    """启发式判断一次工具调用是否成功（无报错 / 退出码 0）。"""
    if not result:
        return True  # 无结果不视为失败
    bad = _re_mod.search(
        r'(traceback|exit code\s*[1-9]|exit status\s*[1-9]|non-zero|'
        r'command failed|error:|fatal:|no such file|cannot )', result, _re_mod.I)
    return not bad


def _verify_tool_call(item: dict, trace: dict) -> tuple[bool, str]:
    """命令上下文 / tool-call 结构化校验。

    支持的 signal 字段（均可组合）：
      command_pattern:        正向——至少一条 Bash 命令匹配该正则
      command_all_patterns:   正向——列表中每个正则都至少有一条命令匹配（AND）
      command_must_not_match: 负向——命令与写入正文中都不得匹配该正则
      ignore_comments: true   负向匹配前剥离行内注释（默认 true）
      forbid_range_on_files:  负向——Read 这些 basename 文件时不得带 offset/limit；
                              同时拦截 bash 中对这些文件的 `head/tail/sed -n` 范围读取
      require_after_each:     序列——{trigger, follow, min_follow, follow_requires_ok}
                              每个 trigger 事件后、下一个 trigger 之前必须出现 follow 事件
    """
    sig = item.get("signal") or {}
    actions = _extract_actions(trace)
    commands = actions["commands"]
    edits = actions["edits"]
    reads = actions["reads"]
    events = actions["events"]

    # ── 正向：单一命令模式 ──
    if "command_pattern" in sig:
        pat = _re_mod.compile(sig["command_pattern"], _re_mod.I)
        if not any(pat.search(c) for c in commands):
            return False, f"no bash command matches {sig['command_pattern']!r}"

    # ── 正向：多命令模式（AND，证明完整工作流）──
    if "command_all_patterns" in sig:
        pats = sig["command_all_patterns"]
        if isinstance(pats, str):
            pats = [pats]
        missing = []
        for p in pats:
            cp = _re_mod.compile(p, _re_mod.I)
            if not any(cp.search(c) for c in commands):
                missing.append(p)
        if missing:
            return False, f"workflow incomplete; no command matches: {missing}"

    # ── 负向：命令/写入正文中不得出现禁止库/调用 ──
    if "command_must_not_match" in sig:
        ignore_comments = sig.get("ignore_comments", True)
        haystacks = list(commands) + [e["payload"] for e in edits]
        if ignore_comments:
            haystacks = [_strip_inline_comments(h) for h in haystacks]
        pat = _re_mod.compile(sig["command_must_not_match"], _re_mod.I)
        for h in haystacks:
            m = pat.search(h)
            if m:
                return False, f"forbidden lib/call in command/code: {m.group(0)!r}"

    # ── 负向：读取 skill 文档不得带范围参数 ──
    if "forbid_range_on_files" in sig:
        names = sig["forbid_range_on_files"]
        if isinstance(names, str):
            names = [names]
        names_l = [n.lower() for n in names]
        for r in reads:
            base = os.path.basename(r["path"]).lower()
            if base in names_l and r["has_range"]:
                return False, f"range (offset/limit) used while reading {base}"
        # bash 范围读取拦截：head/tail -n / sed -n 'a,bp' / awk NR 针对这些文件
        range_cmd = _re_mod.compile(
            r'(?i)\b(head|tail|sed\s+-n|awk)\b.*\b('
            + "|".join(_re_mod.escape(n) for n in names_l) + r')\b')
        for c in commands:
            if range_cmd.search(c) and _re_mod.search(r'-n\b|NR|,\s*\d|\d\s*,', c):
                return False, f"bash range-read of skill doc: {c[:120]!r}"

    # ── 序列：每次编辑后须验证 ──
    if "require_after_each" in sig:
        seq = sig["require_after_each"]
        trig = _re_mod.compile(seq["trigger"], _re_mod.I)
        foll = _re_mod.compile(seq["follow"], _re_mod.I)
        min_follow = int(seq.get("min_follow", 0))
        follow_requires_ok = bool(seq.get("follow_requires_ok", False))
        pending_edit = False
        follow_count = 0
        trig_count = 0
        for ev in events:
            txt = ev["text"]
            is_follow = foll.search(txt) and (ev["ok"] if follow_requires_ok else True)
            is_trig = trig.search(txt)
            # follow 优先消费 pending（一个 step 不会同时是 edit 又是 validate）
            if is_follow:
                follow_count += 1
                pending_edit = False
            elif is_trig:
                if pending_edit:
                    return False, "an edit was not validated before the next edit"
                pending_edit = True
                trig_count += 1
        if pending_edit:
            return False, "last edit was not followed by a validate"
        if trig_count == 0:
            return False, f"no edit event matched trigger {seq['trigger']!r}"
        if follow_count < min_follow:
            return False, f"validate ran {follow_count}x < required {min_follow}x"

    # ── 正向：最后一次匹配命令必须成功 ──
    if "last_command_ok" in sig:
        pat = _re_mod.compile(sig["last_command_ok"], _re_mod.I)
        last_match = None
        for ev in events:
            if ev["kind"] == "cmd" and pat.search(ev["text"]):
                last_match = ev
        if last_match is None:
            return False, f"no command matches last_command_ok pattern {sig['last_command_ok']!r}"
        if not last_match["ok"]:
            return False, f"last matching command failed: {last_match['text'][:120]!r}"

    return True, ""


# ──────────────────────────────────────────────────────────────────────
# 3c. OOXML / PPTX deterministic state checks (task-completion & artifact)
#
# pptx 本质是 zip；嵌入的 xlsx 也是 zip。全部用标准库解包，不依赖
# python-pptx / openpyxl，做确定性断言（输出存在、合法 OOXML 结构、
# 嵌入工作簿单元格值、公式 <f> 保留、新 slide 注册、auto-number bullet 等）。
# ──────────────────────────────────────────────────────────────────────
def _find_output_file(job_dir: Path, candidates: list[str]) -> Path | None:
    for name in candidates:
        p = job_dir / name
        if p.exists():
            return p
        hits = list(job_dir.rglob(name))
        if hits:
            return hits[0]
    return None


def _read_zip_member(zf, member_glob: str):
    import fnmatch
    for n in zf.namelist():
        if fnmatch.fnmatch(n, member_glob) or n == member_glob:
            return n, zf.read(n)
    return None, None


def _xl_cell_inner(sheet_xml: str, ref: str):
    """返回单元格 <c r="ref"> 的内部 XML，找不到返回 None。"""
    m = _re_mod.search(r'<c\b[^>]*\br="%s"[^>]*>(.*?)</c>' % _re_mod.escape(ref),
                       sheet_xml, _re_mod.S)
    if m:
        return m.group(1)
    if _re_mod.search(r'<c\b[^>]*\br="%s"[^>]*/>' % _re_mod.escape(ref), sheet_xml):
        return ""
    return None


def _verify_pptx(item: dict, trace: dict, job_dir: Path | None) -> tuple[bool, str]:
    """对最终产物 pptx 做确定性 OOXML 断言。

    signal 字段：
      output_candidates:   [文件名, ...]  在 job_dir 内（含子目录）查找产物
      must_be_valid_ooxml: true            合法 zip
      required_parts:      ['[Content_Types].xml', 'ppt/presentation.xml', ...]
      embedded_xlsx:       {path_glob, sheet, cell_equals:{ref:val}, formula_cells_preserved:[ref,...]}
      slides:              {min_count, slide_part, contains:[...], registered_parts:[...],
                            buautonum_min, no_leading_bullets: true}
    """
    import zipfile, io
    sig = item.get("signal") or {}
    if not job_dir:
        return False, "pptx-check verifier requires --job-dir"

    candidates = sig.get("output_candidates") or ["results.pptx", "output.pptx"]
    if isinstance(candidates, str):
        candidates = [candidates]
    out = _find_output_file(job_dir, candidates)
    if not out:
        return False, f"output file not found (looked for {candidates})"

    try:
        zf = zipfile.ZipFile(out)
    except Exception as e:
        return False, f"output is not a valid zip/OOXML: {e}"
    names = zf.namelist()
    bad = zf.testzip()
    if bad is not None:
        return False, f"corrupt zip member: {bad}"

    # 必备 OOXML 部件
    for part in (sig.get("required_parts") or []):
        if part not in names:
            return False, f"missing OOXML part: {part}"

    # ── 嵌入工作簿断言（t1）──
    exl = sig.get("embedded_xlsx")
    if exl:
        ename, ebytes = _read_zip_member(zf, exl.get("path_glob", "ppt/embeddings/*.xlsx"))
        if not ename:
            return False, f"embedded xlsx not found ({exl.get('path_glob')})"
        try:
            xzf = zipfile.ZipFile(io.BytesIO(ebytes))
        except Exception as e:
            return False, f"embedded xlsx not a valid zip: {e}"
        sheet = exl.get("sheet", "xl/worksheets/sheet1.xml")
        if sheet not in xzf.namelist():
            return False, f"embedded sheet not found: {sheet}"
        sheet_xml = xzf.read(sheet).decode("utf-8", "replace")
        # 单元格值断言
        for ref, expected in (exl.get("cell_equals") or {}).items():
            inner = _xl_cell_inner(sheet_xml, ref)
            if inner is None:
                return False, f"cell {ref} not present in sheet"
            vm = _re_mod.search(r'<v>(.*?)</v>', inner, _re_mod.S)
            if not vm:
                return False, f"cell {ref} has no <v> value"
            got = vm.group(1).strip()
            exp = str(expected).strip()
            try:
                if abs(float(got) - float(exp)) > 1e-9:
                    return False, f"cell {ref} = {got!r}, expected {exp!r}"
            except ValueError:
                if got != exp:
                    return False, f"cell {ref} = {got!r}, expected {exp!r}"
        # 公式保留断言
        for ref in (exl.get("formula_cells_preserved") or []):
            inner = _xl_cell_inner(sheet_xml, ref)
            if inner is None or "<f" not in inner:
                return False, f"formula cell {ref} lost its <f> element"

    # ── slide 断言（t2）──
    sl = sig.get("slides")
    if sl:
        slide_parts = [n for n in names if _re_mod.match(r'ppt/slides/slide\d+\.xml$', n)]
        if "min_count" in sl and len(slide_parts) < int(sl["min_count"]):
            return False, f"only {len(slide_parts)} slides < {sl['min_count']}"
        for part in (sl.get("registered_parts") or []):
            # 在 [Content_Types].xml / presentation.xml.rels / presentation.xml 中检索注册痕迹
            ct = zf.read("[Content_Types].xml").decode("utf-8", "replace") if "[Content_Types].xml" in names else ""
            rels = zf.read("ppt/_rels/presentation.xml.rels").decode("utf-8", "replace") if "ppt/_rels/presentation.xml.rels" in names else ""
            base = os.path.basename(part)
            if part not in ct and base not in rels:
                return False, f"new slide not registered: {part}"
        target_part = sl.get("slide_part")
        slide_xml = ""
        if target_part and target_part in names:
            slide_xml = zf.read(target_part).decode("utf-8", "replace")
        elif slide_parts:
            # 默认取编号最大的 slide（新增的收尾页）
            target_part = sorted(slide_parts, key=lambda n: int(_re_mod.search(r'(\d+)\.xml$', n).group(1)))[-1]
            slide_xml = zf.read(target_part).decode("utf-8", "replace")
        for needle in (sl.get("contains") or []):
            if needle not in slide_xml:
                return False, f"{target_part} does not contain {needle!r}"
        if "buautonum_min" in sl:
            n_bu = len(_re_mod.findall(r'<a:buAutoNum\b', slide_xml))
            if n_bu < int(sl["buautonum_min"]):
                return False, f"buAutoNum count {n_bu} < {sl['buautonum_min']} (auto-numbering missing)"
        if sl.get("buautonum_type"):
            want = _re_mod.escape(str(sl["buautonum_type"]))
            if not _re_mod.search(r'<a:buAutoNum\b[^>]*\btype=["\']%s["\']' % want, slide_xml):
                return False, f"buAutoNum type {sl['buautonum_type']!r} not found"
        if sl.get("no_leading_bullets"):
            # 检查可见文本 run 不以手动编号/符号开头
            texts = _re_mod.findall(r'<a:t>(.*?)</a:t>', slide_xml, _re_mod.S)
            lead = _re_mod.compile(r'^\s*(?:\d+\s*[\.\)]|[\(（]\s*\d+\s*[\)）]|[•·\-\*]|[①②③④⑤⑥⑦⑧⑨⑩]|[一二三四五六七八九十]+\s*、)')
            for t in texts:
                if lead.match(t):
                    return False, f"manual bullet/number found in run text: {t[:40]!r}"
            # 若声明用 auto-number 却完全没有 buAutoNum，也判失败（vacuous）
            if sl.get("require_buautonum_when_listing") and not _re_mod.search(r'<a:buAutoNum\b', slide_xml):
                return False, "list expected to use buAutoNum but none found"

    # ── caption 格式断言（t2）──
    cf = sig.get("caption_format")
    if cf:
        for part in (cf.get("slide_parts") or []):
            if part not in names:
                return False, f"caption slide part missing: {part}"
            xml = zf.read(part).decode("utf-8", "replace")
            if cf.get("typeface") and not _re_mod.search(r'\btypeface=["\']%s["\']' % _re_mod.escape(str(cf["typeface"])), xml):
                return False, f"{part} missing typeface={cf['typeface']!r}"
            if cf.get("sz") and not _re_mod.search(r'\bsz=["\']%s["\']' % _re_mod.escape(str(cf["sz"])), xml):
                return False, f"{part} missing sz={cf['sz']!r}"
            if cf.get("color_srgb") and not _re_mod.search(r'\bval=["\']%s["\']' % _re_mod.escape(str(cf["color_srgb"])), xml, _re_mod.I):
                return False, f"{part} missing color {cf['color_srgb']!r}"
            if cf.get("alignment") and not _re_mod.search(r'\balgn=["\']%s["\']' % _re_mod.escape(str(cf["alignment"])), xml):
                return False, f"{part} missing alignment {cf['alignment']!r}"
            if str(cf.get("bold", "")).lower() in {"0", "false", "none"} and _re_mod.search(r'<a:b\b', xml):
                return False, f"{part} contains bold marker despite bold={cf['bold']!r}"

    return True, ""


def _verify_llm_judge(item: dict, trace: dict, judge_model: str,
                      judge_call_fn) -> tuple[bool, str]:
    sig = item.get("signal") or {}
    question = sig.get("judge_question") or sig.get("query")
    # Fallback: v3 rubrics may put question in verifier_detail.llm_judge_question
    if not question:
        vd = item.get("verifier_detail") or {}
        question = vd.get("llm_judge_question")
    if not question:
        return False, "llm-judge signal.judge_question/query missing"
    cw = sig.get("judge_context_window") or ["serialized_steps", "final_answer"]
    expected = (sig.get("judge_expected") or "YES").strip().upper()
    if expected not in ("YES", "NO"):
        return False, f"invalid judge_expected={expected!r} (must be YES or NO)"

    parts = []
    if "serialized_steps" in cw:
        ser = [serialize_step(s, include_result=False) for s in trace["steps"]]
        parts.append("## Trace (one tool call per line, format `tool:args:intent`):\n" +
                     "\n".join(f"  step{i+1}: {s}" for i, s in enumerate(ser)))
    for cw_entry in cw:
        if isinstance(cw_entry, dict) and "tool_results_first_n" in cw_entry:
            n = int(cw_entry["tool_results_first_n"])
            results = []
            for i, s in enumerate(trace["steps"][:n]):
                r = s.get("result")
                if r:
                    if not isinstance(r, str):
                        r = json.dumps(r, ensure_ascii=False)
                    results.append(f"  step{i+1} ({s['tool']}) result: {r[:500]}")
            if results:
                parts.append("## First tool_results:\n" + "\n".join(results))
    if "final_answer" in cw:
        fa = trace["final_answer"] or "(empty)"
        parts.append(f"## Final answer:\n{fa[:2000]}")

    prompt = textwrap.dedent(f"""\
        You are a strict judge for a Skill-Following benchmark.
        You will read an agent execution trace and answer ONE yes/no question
        about whether a specific skill rule was followed.

        Rule (id={item.get('id')}):
        {(item.get('spec') or '').strip()}

        Question to answer (output ONLY "YES" or "NO" on the first line, then
        on the second line a short reason no longer than 25 words):
        {question.strip()}

        Trace context:
        ---
        {chr(10).join(parts)}
        ---
    """)
    try:
        verdict_text = judge_call_fn(judge_model, prompt)
    except Exception as e:
        return False, f"llm-judge call failed: {type(e).__name__}: {e}"

    head = (verdict_text or "").strip().splitlines()
    if not head:
        return False, "llm-judge returned empty"
    first = head[0].strip().upper()
    reason = head[1].strip() if len(head) > 1 else ""
    # 判定模型回答 YES/NO
    if first.startswith("YES") or "YES" in first.split():
        verdict = "YES"
    elif first.startswith("NO") or "NO" in first.split():
        verdict = "NO"
    else:
        return False, f"llm-judge unparsable: {first[:120]!r}"
    passed = (verdict == expected)
    label = "judge OK" if passed else f"judge {verdict} ≠ expected {expected}"
    return passed, f"[{label}] {reason[:200]}"


# Symbolic weight resolution (e.g., "high" → 3, "mid" → 2, "low" → 1, "zero" → 0)
_WEIGHT_SYMBOL_MAP = {"high": 3.0, "mid": 2.0, "low": 1.0, "zero": 0.0}

def _resolve_weight(val) -> float:
    """Convert weight value (numeric or symbolic string) to float."""
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        v = val.strip().lower()
        if v in _WEIGHT_SYMBOL_MAP:
            return _WEIGHT_SYMBOL_MAP[v]
        return float(v)
    return 1.0


# Lazy judge caller — thread-local Api instances
import threading as _threading
_JUDGE_TLS = _threading.local()  # 每个线程独立持有 Api 实例，避免连接池竞争

# 单次 API 调用超时秒数（httpx read timeout）
_JUDGE_CALL_TIMEOUT = int(os.environ.get("SF_JUDGE_CALL_TIMEOUT", "300"))


def _create_judge_client():
    """Create a fresh OpenAI-compatible client for the judge model.

    Reads credentials from the environment:
        OPENAI_API_KEY      : required (may be an OpenAI key or any compatible endpoint key)
        OPENAI_BASE_URL     : optional, defaults to https://api.openai.com/v1
        SF_JUDGE_CALL_TIMEOUT : optional, per-request read timeout (seconds, default 300)

    Returns a `openai.OpenAI` instance. Each call opens a new TCP connection;
    callers should close the client after use.
    """
    try:
        from openai import OpenAI
    except ImportError as e:  # pragma: no cover
        raise RuntimeError(
            "openai>=1.0 is required for the LLM judge. "
            "Install with: pip install openai"
        ) from e
    api_key = (
        os.environ.get("OPENAI_API_KEY")
        or os.environ.get("JUDGE_API_KEY")
        or ""
    ).strip()
    if not api_key:
        raise RuntimeError(
            "missing OPENAI_API_KEY (or JUDGE_API_KEY) for LLM-judge rubric items"
        )
    kwargs: dict = {"api_key": api_key, "timeout": _JUDGE_CALL_TIMEOUT}
    base_url = os.environ.get("OPENAI_BASE_URL") or os.environ.get("JUDGE_BASE_URL")
    if base_url:
        kwargs["base_url"] = base_url
    return OpenAI(**kwargs)


def make_judge_caller():
    """Return a function (model, prompt) -> response_text.

    每次调用都创建全新的 Api 实例（全新 TCP 连接），调用完毕后关闭。
    附带 SIGALRM 超时保护：单次调用最多 _JUDGE_CALL_TIMEOUT 秒，
    超时则抛出异常（上层 score 函数会 catch 并标记 item 为失败）。
    """
    import logging
    import signal

    logger = logging.getLogger("rubric_judge")
    if not logger.handlers:
        logger.addHandler(logging.NullHandler())

    class _JudgeTimeout(Exception):
        pass

    def _alarm_handler(signum, frame):
        raise _JudgeTimeout(f"Judge API call timed out after {_JUDGE_CALL_TIMEOUT}s")

    def _call(model: str, prompt: str) -> str:
        # Fresh OpenAI client per call so every judge request opens a new TCP
        # connection (avoids stale-session issues under long-running scoring).
        client = _create_judge_client()

        # SIGALRM hard timeout (main thread only; worker threads fall back to
        # the client-level `timeout` set inside _create_judge_client()).
        import threading
        is_main_thread = threading.current_thread() is threading.main_thread()
        if is_main_thread:
            old_handler = signal.signal(signal.SIGALRM, _alarm_handler)
            signal.alarm(_JUDGE_CALL_TIMEOUT)
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )
        except _JudgeTimeout:
            print(f"  [judge] TIMEOUT after {_JUDGE_CALL_TIMEOUT}s, skipping this item",
                  flush=True)
            return ""
        finally:
            if is_main_thread:
                signal.alarm(0)  # cancel alarm
                signal.signal(signal.SIGALRM, old_handler)
            # Best-effort close the underlying http client
            try:
                client.close()
            except Exception:
                pass

        try:
            choice = resp.choices[0]
        except (AttributeError, IndexError):
            return ""
        msg = getattr(choice, "message", None)
        if msg is None:
            return ""
        return str(getattr(msg, "content", "") or "")

    return _call


# ──────────────────────────────────────────────────────────────────────
# 4. Top-level scoring
# ──────────────────────────────────────────────────────────────────────
def evaluate_rubric_item(item: dict, trace: dict, job_dir: Path | None,
                         judge_model: str, judge_call_fn,
                         rubric_meta: dict | None = None) -> dict:
    verifier = (item.get("verifier") or "regex").lower()
    if verifier == "regex":
        passed, reason = _verify_regex(item, trace)
    elif verifier in ("tool-call", "tool_call", "command"):
        passed, reason = _verify_tool_call(item, trace)
    elif verifier in ("pptx-check", "pptx_check", "ooxml-check"):
        passed, reason = _verify_pptx(item, trace, job_dir)
    elif verifier == "state-diff":
        passed, reason = _verify_state_diff(item, trace, job_dir)
    elif verifier in ("state-check", "state_check"):
        passed, reason = _verify_state_check(item, trace, job_dir, rubric_meta or {})
    elif verifier == "llm-judge":
        passed, reason = _verify_llm_judge(item, trace, judge_model, judge_call_fn)
    else:
        passed, reason = False, f"unknown verifier {verifier!r}"
    return {
        "id": item.get("id"),
        "type": item.get("type"),
        "provenance": (item.get("provenance") or "skill").lower(),
        "verifier": verifier,
        "severity": item.get("severity", "soft"),
        "weight": _resolve_weight(item.get("weight", 1.0)),
        "exclusive": bool(item.get("exclusive", item.get("anti_prior", False))),
        "passed": passed,
        "reason": reason,
    }


def _detect_skill_content_access(steps: list[dict], target_skill: str | None) -> list[dict]:
    """
    检测模型是否通过任何可观测方式获取了 target skill 的实质性内容。

    合法触发路径：
      1. 调用 Skill 工具 (tool=="Skill", args.skill==target_skill)
      2. 用 Read 工具读取了 skill 文档 (路径包含 target_skill 且为 SKILL.md 或 skill 正文)
      3. 用 Bash/Grep 命令读取或搜索了 skill 文档内容
      4. 子 agent (Task) 内部执行了上述任一操作（体现为 parent_tool_use_id 下的调用）

    不算触发：
      - 仅通过 Glob/ls 发现 skill 文件存在但未读取内容
      - 仅从 system init 的 skills 列表名称推断信息
      - 行为碰巧与 skill 一致但从未接触 skill 文档 (default alignment)

    Returns: 所有触发证据 step 的列表
    """
    if not target_skill:
        return []

    evidence = []

    # skill 文档路径的可能模式（双向兼容 - 和 _）
    _variants = {target_skill, target_skill.replace('-', '_'), target_skill.replace('_', '-')}
    skill_path_patterns = [f"skills/{v}" for v in _variants]
    # Skill 工具调用时 args.skill 的可能匹配值
    skill_name_variants = _variants
    # skill 文件名模式
    skill_file_patterns = ["SKILL.md", "skill.md"]

    for s in steps:
        tool = (s.get("tool") or "").lower()
        args = s.get("args") or {}
        if isinstance(args, str):
            args_str = args
            args_dict = {}
        else:
            args_str = json.dumps(args, ensure_ascii=False)
            args_dict = args

        # 路径 1: Skill 工具调用
        if tool == "skill":
            if isinstance(args_dict, dict):
                called_skill = args_dict.get("skill", "")
                if called_skill in skill_name_variants:
                    evidence.append({"step": s, "method": "skill_tool"})

        # 路径 2: Read 工具读取 skill 文档
        elif tool == "read":
            file_path = args_dict.get("file_path", "") if isinstance(args_dict, dict) else ""
            if not file_path:
                file_path = args_str
            if _path_matches_skill(file_path, skill_path_patterns, skill_file_patterns):
                evidence.append({"step": s, "method": "read_file"})

        # 路径 3: Bash 命令读取 skill 文档
        elif tool == "bash":
            command = args_dict.get("command", "") if isinstance(args_dict, dict) else args_str
            # 检查命令是否读取了 skill 文件内容（cat/less/head/tail/grep + skill 路径）
            # 严格要求：必须同时包含 target skill 目录名（skills/<target>）和读取动作，
            # 避免把访问 baseline 官方 skill（.system/imagegen/... 等）误判为触发 target。
            read_cmds = ["cat ", "less ", "head ", "tail ", "more ", "grep ", "awk ", "sed ", "bat "]
            has_read_cmd = any(cmd in command.lower() for cmd in read_cmds)
            has_skill_path = any(p in command for p in skill_path_patterns)
            if has_read_cmd and has_skill_path:
                evidence.append({"step": s, "method": "bash_read"})

        # 路径 4: Grep 工具搜索 skill 目录
        elif tool == "grep":
            # Grep 工具参数中包含 skill 路径
            if any(p in args_str for p in skill_path_patterns):
                evidence.append({"step": s, "method": "grep_tool"})

    return evidence


def _path_matches_skill(file_path: str, skill_path_patterns: list[str],
                        skill_file_patterns: list[str]) -> bool:
    """判断文件路径是否指向 target skill 的文档。"""
    if not file_path:
        return False
    # 路径中包含 skill 目录名且指向 skill 文档
    has_skill_dir = any(p in file_path for p in skill_path_patterns)
    has_skill_file = any(f.lower() in file_path.lower() for f in skill_file_patterns)
    # 必须同时满足：在 skill 目录下 且 是 skill 文档文件
    # 或者路径直接包含 skills/<name>/SKILL.md 这样的完整路径
    return has_skill_dir and has_skill_file


def compute_trigger_score(trace: dict, *, task_kind: str,
                          target_skill: str | None,
                          trace_path: Path | None = None,
                          job_dir: Path | None = None) -> dict:
    """
    Trigger 维度评分（独立于 rubric）。

    触发定义：模型通过任何可观测的方式，获取了 target skill 文档的实质性内容。

    === Claude Code CLI 管线 ===
    模型需要主动触发：调用 Skill 工具 / Read 读取 SKILL.md / Bash cat/grep SKILL.md。
    Skill 内容不会预注入，必须通过工具调用获取。
    - skill_registered 由 trace 第一行 system_init.skills 判定
    - content_accessed 由 _detect_skill_content_access 检测 trace 中的工具调用

    === Codex CLI 管线 ===
    Skill 内容通过 .codex/instructions.md 预注入为系统指令。
    模型不需要（也无法）主动调用 Skill 工具——skill 内容已在 prompt 中。
    - skill_registered 由 _normalize_codex_stream 从 instructions.md frontmatter 提取
    - trigger 恒为 "triggered"（因为内容已预注入），trigger_method = "codex_instructions"
    - 但如果 instructions.md 不存在或不含目标 skill，仍为 "skill-not-registered"

    task_kind = "positive": 该 task 应该用 target_skill。
        score=1.0 表示触发了，score=0.0 表示漏触发。

    task_kind = "negative": 该 task 不该用 target_skill。
        score=1.0 表示成功避开，score=0.0 表示过度触发。

    返回字段：
        score:                  0 / 1
        verdict:                "triggered" / "missed" / "avoided" / "over-triggered"
                                / "skill-not-registered"  / "n/a"
        trigger_method:         触发方式 ("skill_tool" / "read_file" / "bash_read" /
                                "grep_tool" / "codex_instructions" / None)
        target_skill:           评测对应的 skill 名
        skill_registered:       skill 是否已注册/注入
        skill_tool_calls_total: 模型用 Skill 工具的总次数
        skill_tool_calls_target:模型用 Skill 工具调用 target_skill 的次数
        content_access_total:   模型通过任何方式获取 skill 内容的总次数
    """
    is_codex = trace.get("format") == "codex-stream"

    sys_skills = []
    if trace.get("system_init"):
        sys_skills = trace["system_init"].get("skills") or []

    # 旧逻辑：统计 Skill 工具调用（保留用于向后兼容报告）
    skill_calls = []
    target_calls_via_tool = []
    _target_variants = (
        {target_skill, target_skill.replace('-', '_'), target_skill.replace('_', '-')}
        if target_skill else set()
    )
    for s in trace["steps"]:
        if (s.get("tool") or "").lower() == "skill":
            skill_calls.append(s)
            args = s.get("args") or {}
            if isinstance(args, dict) and target_skill and args.get("skill") in _target_variants:
                target_calls_via_tool.append(s)

    # 新逻辑：检测所有获取 skill 内容的方式
    content_access_evidence = _detect_skill_content_access(trace["steps"], target_skill)
    content_accessed = bool(content_access_evidence)

    # ── Codex 管线：检测模型是否主动读取了 .codex/skills/*/SKILL.md ──
    # 修复后的 Codex 评测使用原生 skill 机制：
    #   - skill 放在 .codex/skills/<name>/SKILL.md
    #   - Codex 在系统提示中只展示 skill 名称 + description（不含全文）
    #   - 模型需要主动 cat/head/read SKILL.md 才能获取 skill 内容
    #   - 这与 Claude Code CLI 的 Skill 工具调用语义对等
    #
    # Trigger 判定：trace 中是否有 Bash 命令读取了 .codex/skills/*/SKILL.md
    # 这已经被 _detect_skill_content_access() 覆盖（路径 3: Bash 读取 skill 文档），
    # 但需要扩展路径匹配模式以包含 .codex/skills/ 路径。
    codex_injected = False
    if is_codex and target_skill:
        si = trace.get("system_init") or {}
        codex_skill_files = si.get("_codex_skill_files") or {}
        if codex_skill_files:
            # Skill 已注册到 .codex/skills/ → skill_registered=True
            # 但 trigger 取决于模型是否在 trace 中实际读取了 SKILL.md
            codex_injected = True

            # 扩展 content_access 检测：检查 trace 中的 Bash 命令是否读取了
            # .codex/skills/*/SKILL.md 或 .codex_home/skills/*/SKILL.md 路径
            # 严格约束：路径中必须包含 target_skill 名（含 - / _ 变体），
            # 排除 baseline 官方 skill（.system/imagegen 等）造成的假阳性。
            _tgt_variants = {
                target_skill,
                target_skill.replace('-', '_'),
                target_skill.replace('_', '-'),
            }
            for s in trace["steps"]:
                if (s.get("tool") or "").lower() == "bash":
                    args = s.get("args") or {}
                    command = args.get("command", "") if isinstance(args, dict) else str(args)
                    read_cmds = ["cat ", "less ", "head ", "tail ", "more ", "grep ",
                                 "awk ", "sed ", "bat "]
                    has_read_cmd = any(cmd in command.lower() for cmd in read_cmds)
                    in_codex_skills_dir = (
                        ".codex/skills" in command or ".codex_home/skills" in command
                    )
                    # 排除 .system/ 下的 baseline 官方 skill
                    is_system_baseline = (
                        "skills/.system/" in command or "skills\\.system\\" in command
                    )
                    # 命令中必须显式提到 target skill 名或指向该 skill 的 SKILL.md
                    hits_target = any(v in command for v in _tgt_variants if v)
                    if (has_read_cmd and in_codex_skills_dir
                            and hits_target and not is_system_baseline
                            and "SKILL.md" in command):
                        content_access_evidence.append({
                            "step": s, "method": "bash_read"
                        })
                        content_accessed = True

        # Backward compatibility: 旧的 instructions.md 注入方式
        # 如果是旧 trace（instructions.md 存在但 skills/ 不存在），仍视为已注入
        if not codex_injected:
            instructions_md = job_dir / ".codex" / "instructions.md" if (trace_path and job_dir) else None
            if instructions_md and instructions_md.exists():
                codex_injected = True
                content_accessed = True
                content_access_evidence.append({
                    "step": {"tool": "_codex_instructions",
                             "args": {"path": str(instructions_md)}},
                    "method": "codex_instructions",
                })

    # 提取触发方式
    trigger_methods = list({e["method"] for e in content_access_evidence})
    trigger_method = trigger_methods[0] if len(trigger_methods) == 1 else (
        ",".join(sorted(trigger_methods)) if trigger_methods else None
    )

    skill_registered = False
    if target_skill:
        # 双向兼容：target_skill 可能用连字符，trace 中的 skills 列表可能用下划线（或反之）
        _ts_variants = {target_skill, target_skill.replace('-', '_'), target_skill.replace('_', '-')}
        skill_registered = bool(_ts_variants & set(sys_skills))

    # Fallback: 如果 skills 数组为空（user-invocable: false 的 skill 不会出现在
    # system_init.skills 中），但 Skill 工具确实存在于 tools 列表中，说明项目内
    # .claude/skills/ 目录存在可用的 skill，视为已注册。
    # 这样即使模型未触发 skill，也能正确标记为 "missed" 而不是 "skill-not-registered"。
    if not skill_registered and bool(target_skill):
        has_skill_tool_in_tools = False
        if trace.get("system_init"):
            tools_list = trace["system_init"].get("tools") or []
            has_skill_tool_in_tools = "Skill" in tools_list or any(
                (isinstance(t, dict) and t.get("name") == "Skill") for t in tools_list
            )
        if has_skill_tool_in_tools:
            skill_registered = True

    # Codex 管线 fallback：.codex/skills/ 存在 → 视为已注册
    if not skill_registered and codex_injected:
        skill_registered = True

    if task_kind == "positive":
        if not target_skill:
            return {"score": None, "verdict": "n/a (no target skill)",
                    "trigger_method": None,
                    "target_skill": None, "skill_registered": False,
                    "skill_tool_calls_total": 0, "skill_tool_calls_target": 0,
                    "content_access_total": 0}
        if not skill_registered:
            return {"score": None, "verdict": "skill-not-registered",
                    "trigger_method": None,
                    "target_skill": target_skill,
                    "skill_registered": False,
                    "skill_tool_calls_total": len(skill_calls),
                    "skill_tool_calls_target": 0,
                    "content_access_total": len(content_access_evidence)}
        score_v = 1.0 if content_accessed else 0.0
        verdict = "triggered" if content_accessed else "missed"
        return {"score": score_v, "verdict": verdict,
                "trigger_method": trigger_method,
                "target_skill": target_skill, "skill_registered": True,
                "skill_tool_calls_total": len(skill_calls),
                "skill_tool_calls_target": len(target_calls_via_tool),
                "content_access_total": len(content_access_evidence)}

    if task_kind == "negative":
        # 不该触发 target_skill：检查模型有没有以任何方式获取其内容
        if target_skill:
            score_v = 0.0 if content_accessed else 1.0
            verdict = "over-triggered" if content_accessed else "avoided"
        else:
            # 没指定 target，则任何 Skill 工具调用都算违规（保守处理）
            triggered_any = bool(skill_calls)
            score_v = 0.0 if triggered_any else 1.0
            verdict = "over-triggered" if triggered_any else "avoided"
        return {"score": score_v, "verdict": verdict,
                "trigger_method": trigger_method,
                "target_skill": target_skill,
                "skill_registered": skill_registered,
                "skill_tool_calls_total": len(skill_calls),
                "skill_tool_calls_target": len(target_calls_via_tool),
                "content_access_total": len(content_access_evidence)}

    return {"score": None, "verdict": f"unknown task_kind={task_kind!r}",
            "trigger_method": None,
            "target_skill": target_skill, "skill_registered": skill_registered,
            "skill_tool_calls_total": len(skill_calls),
            "skill_tool_calls_target": len(target_calls_via_tool),
            "content_access_total": len(content_access_evidence)}


def score(trace_path: Path, rubric_path: Path, *, job_dir: Path | None = None,
          judge_model: str = "gpt-5",
          judge_call_fn=None,
          task_kind: str = "positive",
          target_skill: str | None = None) -> dict:
    trace = load_trace(trace_path)
    rubric_raw = _parse_yaml(rubric_path.read_text(encoding="utf-8")) or []
    rubric_meta = {}
    if isinstance(rubric_raw, dict):
        rubric_meta = {k: v for k, v in rubric_raw.items() if k not in ("rubric", "rubrics", "rules")}
        if "rules" in rubric_raw:
            rubric = rubric_raw["rules"]
        elif "rubric" in rubric_raw:
            rubric = rubric_raw["rubric"]
        elif "rubrics" in rubric_raw:
            rubric = rubric_raw["rubrics"]
        else:
            rubric = rubric_raw
    else:
        rubric = rubric_raw
    if not isinstance(rubric, list):
        raise SystemExit(f"rubric file must yield a list, got {type(rubric).__name__}")
    if judge_call_fn is None:
        judge_call_fn = make_judge_caller()

    # ── 并发评估 rubric 项 ──
    # llm-judge 类项是 I/O 密集（等 API 响应），用线程池并行加速
    # 非 llm-judge 类（regex / state-diff）是 CPU 密集且极快，同步执行
    JUDGE_CONCURRENCY = int(os.environ.get("SF_JUDGE_CONCURRENCY", "8"))

    # 先同步评估非 llm-judge 项
    items = [None] * len(rubric)
    llm_judge_indices = []
    for idx, it in enumerate(rubric):
        verifier = (it.get("verifier") or "regex").lower()
        if verifier == "llm-judge":
            llm_judge_indices.append(idx)
        else:
            items[idx] = evaluate_rubric_item(it, trace, job_dir, judge_model,
                                             judge_call_fn, rubric_meta=rubric_meta)

    # 并发评估 llm-judge 项
    if llm_judge_indices:
        def _eval_judge(idx):
            return idx, evaluate_rubric_item(rubric[idx], trace, job_dir,
                                            judge_model, judge_call_fn,
                                            rubric_meta=rubric_meta)

        with ThreadPoolExecutor(max_workers=min(JUDGE_CONCURRENCY, len(llm_judge_indices))) as pool:
            futures = {pool.submit(_eval_judge, idx): idx for idx in llm_judge_indices}
            for fut in as_completed(futures):
                try:
                    idx, result = fut.result()
                    items[idx] = result
                except Exception as e:
                    idx = futures[fut]
                    items[idx] = {
                        "id": rubric[idx].get("id"),
                        "type": rubric[idx].get("type"),
                        "provenance": (rubric[idx].get("provenance") or "skill").lower(),
                        "weight": _resolve_weight(rubric[idx].get("weight", 1.0)),
                        "passed": False,
                        "reason": f"concurrent judge error: {type(e).__name__}: {e}",
                        "exclusive": rubric[idx].get("exclusive", False),
                    }

    # 触发判断（独立于 rubric）
    trigger = compute_trigger_score(trace, task_kind=task_kind,
                                    target_skill=target_skill,
                                    trace_path=trace_path, job_dir=job_dir)

    # ──────────────────────────────────────────────────────────────
    # Provenance 过滤：核心评分目标是 skill-following，不是 instruction-
    # following / task success。仅 provenance ∈ {skill, generic} 的规则进
    # compliance/boundary 分母。
    #   - skill   ：只有读 SKILL.md 才能知道的规则（核心信号）
    #   - generic ：跨 task 通用安全护栏（git commit/push 等），并入 boundary
    #   - gate    ：可评估性闸门，不进分母；不全过则 trace 标 invalid
    #   - task    ：任务完成率 0/1，不进 skill-following 分母
    #   - instruction ：纯 prompt 指令派生的规则，本 benchmark 不评（仅记录）
    #
    # Compliance 桶 = provenance=skill 且 type 不属于 boundary 类的规则
    # Boundary 桶  = provenance ∈ {skill, generic} 且 type 属于 boundary 类
    # Task 桶      = provenance=task，仅汇报 task_completion_score
    # ──────────────────────────────────────────────────────────────
    BOUNDARY_TYPES = {"boundary", "forbidden-tool", "forbidden-arg"}
    SCORED_PROVENANCE = {"skill", "generic"}
    compliance_items = []
    boundary_items = []
    gate_items = []
    task_items = []
    instruction_items = []
    for it in items:
        prov = it.get("provenance", "skill")
        is_boundary = (it.get("type") or "").lower() in BOUNDARY_TYPES
        if prov == "gate":
            gate_items.append(it)
        elif prov == "task":
            task_items.append(it)
        elif prov == "instruction":
            instruction_items.append(it)
        elif prov in SCORED_PROVENANCE:
            if is_boundary:
                boundary_items.append(it)
            else:
                compliance_items.append(it)
        else:
            # 未知 provenance 保守归 instruction（不进分母）
            instruction_items.append(it)

    def _wscore(group):
        if not group:
            return None
        tot = sum(it["weight"] for it in group) or 1.0
        good = sum(it["weight"] for it in group if it["passed"])
        return good / tot

    compliance_score = _wscore(compliance_items)
    boundary_score = _wscore(boundary_items)

    def _process_following_score(compliance, boundary):
        """Process-following score before trigger gating.

        设计契约（C 节规范，对应 fix_recommendations_20260703.md#C）：
        - compliance 与 boundary 均为可选（None 表示 rubric 未定义此桶）。
        - 存在的桶按权重 (compliance=0.7, boundary=0.3) 加权，并在缺失时**重新归一化**，
          从而避免"缺项被隐性当作 0"。
        - 具体行为：
            * 二者都在   → 0.7*compliance + 0.3*boundary
            * boundary=None（positive 任务未写 boundary 项，105 个 task 属此情况）
                          → 只用 compliance（denom=0.7 后除自身归一化，等价于返回 compliance）
            * compliance=None（部分 negative 任务只有 boundary 规则）
                          → 只用 boundary
            * 二者都 None → None（rubric 无 scored 项，上层置 SF=None）
        - **不允许**任何调用方在 boundary=None 时把它当作 0 参与加权；
          若未来公式演进破坏此契约，请同时更新 fix_recommendations_20260703.md#C
          与 evaluation/analysis/sf_score_formula_spec.md。
        """
        parts = []
        if compliance is not None:
            parts.append((0.7, compliance))
        if boundary is not None:
            parts.append((0.3, boundary))
        if not parts:
            return None
        denom = sum(w for w, _ in parts)
        return sum(w * v for w, v in parts) / denom

    process_following_score = _process_following_score(compliance_score, boundary_score)
    if trigger["score"] is None or process_following_score is None:
        skill_following_score = None
    else:
        # 主分：没触发/误触发 target skill 时，skill-following 直接为 0。
        skill_following_score = trigger["score"] * process_following_score

    # Task completion：单独二值汇报，不进入 skill-following 分数。
    task_completion_score = (1.0 if all(it["passed"] for it in task_items) else 0.0) if task_items else None
    # Gate：所有 gate 规则全过才算 valid（gate weight 一律设 0，不参与加权）
    gate_passed = all(it["passed"] for it in gate_items) if gate_items else True
    # 计算 score 分母只用 scored 规则（与 compliance/boundary 一致）
    scored_items = compliance_items + boundary_items
    total_w = sum(it["weight"] for it in scored_items) or 1.0
    pass_w = sum(it["weight"] for it in scored_items if it["passed"])

    return {
        "trace": str(trace_path),
        "trace_format": trace["format"],
        "n_steps": len(trace["steps"]),
        "task_kind": task_kind,
        "target_skill": target_skill,

        # —— 三维主分（仅基于 skill + generic provenance）—— #
        "trigger_score": trigger["score"],
        "trigger_verdict": trigger["verdict"],
        "compliance_score": compliance_score,
        "boundary_score": boundary_score,
        "process_following_score": process_following_score,
        "skill_following_score": skill_following_score,

        # —— Gate（可评估性闸门）—— #
        "gate_passed": gate_passed,
        "gate_items_count": len(gate_items),
        "gate_failed_ids": [it["id"] for it in gate_items if not it["passed"]],

        # —— Task completion（任务完成率，不计入 skill-following）—— #
        "task_completion_score": task_completion_score,
        "task_items_count": len(task_items),
        "task_failed_ids": [it["id"] for it in task_items if not it["passed"]],

        # —— 辅助字段 —— #
        "rubric_total": len(items),
        "passed_count": sum(1 for it in items if it["passed"]),
        "score": pass_w / total_w,                # scored items 加权（兼容旧字段）
        "hard_violation_count": sum(
            1 for it in items
            if it["severity"] == "hard"
            and not it["passed"]
            and it.get("provenance", "skill") in SCORED_PROVENANCE
        ),
        "exclusive_pass_rate": (
            sum(1 for it in items if it["exclusive"] and it["passed"]) /
            max(1, sum(1 for it in items if it["exclusive"]))
            if any(it["exclusive"] for it in items) else None
        ),
        "compliance_items_count": len(compliance_items),
        "boundary_items_count": len(boundary_items),
        "instruction_items_count": len(instruction_items),

        # —— 详细 —— #
        "trigger_detail": trigger,
        "items": items,
        "meta": trace["meta"],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rubric", required=True)
    ap.add_argument("--trace", required=True, nargs="+")
    ap.add_argument("--job-dir", default=None,
                    help="batch_run_eval jobs/<model>/ dir，启用 state-diff verifier 必填")
    ap.add_argument("--judge-model", default="gpt-5")
    ap.add_argument("--task-kind", default="positive",
                    choices=["positive", "negative"],
                    help="positive=该用 skill；negative=不该用 skill")
    ap.add_argument("--target-skill", default=None,
                    help="本 task 关联的 target skill name，如 'systematic-debugging'")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    rubric_path = Path(args.rubric).resolve()
    job_dir = Path(args.job_dir).resolve() if args.job_dir else None
    judge_call = make_judge_caller()
    reports = []
    for t in args.trace:
        rep = score(Path(t).resolve(), rubric_path, job_dir=job_dir,
                    judge_model=args.judge_model, judge_call_fn=judge_call,
                    task_kind=args.task_kind, target_skill=args.target_skill)
        reports.append(rep)
        print(f"[{Path(t).name}] format={rep['trace_format']} kind={rep['task_kind']} target={rep['target_skill']}")
        print(f"  TRIGGER    : score={rep['trigger_score']} verdict={rep['trigger_verdict']!r} "
              f"(target_calls={rep['trigger_detail']['skill_tool_calls_target']}/{rep['trigger_detail']['skill_tool_calls_total']})")
        gate_mark = "PASS" if rep['gate_passed'] else f"FAIL ({','.join(rep['gate_failed_ids'])})"
        print(f"  GATE       : {gate_mark}  ({rep['gate_items_count']} items)")
        task_mark = "n/a" if rep['task_completion_score'] is None else f"{rep['task_completion_score']:.0f}"
        print(f"  TASK       : completion={task_mark}  ({rep['task_items_count']} task items, not scored)")
        sf = "n/a" if rep['skill_following_score'] is None else f"{rep['skill_following_score']:.2f}"
        pf = "n/a" if rep['process_following_score'] is None else f"{rep['process_following_score']:.2f}"
        print(f"  SF_GATED   : {sf}  (trigger × process_following; process={pf})")
        cs = f"{rep['compliance_score']:.2f}" if rep['compliance_score'] is not None else "n/a"
        bs = f"{rep['boundary_score']:.2f}" if rep['boundary_score'] is not None else "n/a"
        print(f"  COMPLIANCE : {cs}  ({rep['compliance_items_count']} skill items)")
        print(f"  BOUNDARY   : {bs}  ({rep['boundary_items_count']} skill+generic items)")
        if rep['instruction_items_count']:
            print(f"  (instruction items recorded but NOT scored: {rep['instruction_items_count']})")
        print(f"  rubric scored score={rep['score']:.2f} passed={rep['passed_count']}/{rep['rubric_total']} "
              f"hard_viol={rep['hard_violation_count']} n_steps={rep['n_steps']}")
        for it in rep["items"]:
            mark = "PASS" if it["passed"] else "FAIL"
            sev = "[hard]" if it["severity"] == "hard" else "[soft]"
            ap_mark = "[EX]" if it["exclusive"] else "    "
            v = it["verifier"][:6].ljust(6)
            prov = (it.get("provenance") or "skill")[:4].upper().ljust(4)
            is_b = (it.get("type") or "").lower() in {"boundary", "forbidden-tool", "forbidden-arg"}
            kind = "B" if is_b else "C"
            print(f"   {mark} {sev}{ap_mark} <{v}>[{prov}]{kind} {it['id']}: {it.get('reason') or ''}")
    if args.out:
        Path(args.out).write_text(
            json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
