#!/usr/bin/env bash
# codex_entrypoint.sh -- Codex CLI pre-load harness for Skill-Use-Bench.
#
# Skill loading channel: pre-load.
#   Skill content is concatenated into .codex/instructions.md, which Codex
#   appends to its system prompt. Every turn the model sees the full skill
#   body. This is useful for measuring the "execution ceiling" while
#   bypassing discovery. For the full skill-following measurement (discovery
#   + execution) use codex_native_skill_entrypoint.sh instead.
#
# Required environment variables:
#   AGENT_MODEL          Model name accepted by Codex CLI (e.g. gpt-5).
#   AGENT_PROMPT_FILE    Absolute path (inside the container) to the prompt file.
#   AGENT_TASK_ID        Task identifier.
#   OPENAI_API_KEY       Credential for the OpenAI (or compatible) API.
#
# Optional:
#   AGENT_MAX_TURNS      Default 20 (Codex has no native max-turns; used for meta only).
#   AGENT_OUT_DIR        Default /workspace/runtime.
#   OPENAI_BASE_URL      Override for OpenAI-compatible endpoints.

set -uo pipefail

START_TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
START_EPOCH=$(date +%s)

: "${AGENT_MODEL:?AGENT_MODEL is required}"
: "${AGENT_PROMPT_FILE:?AGENT_PROMPT_FILE is required}"
: "${AGENT_TASK_ID:?AGENT_TASK_ID is required}"
: "${OPENAI_API_KEY:?OPENAI_API_KEY is required (forward from host)}"

AGENT_MAX_TURNS="${AGENT_MAX_TURNS:-20}"
AGENT_OUT_DIR="${AGENT_OUT_DIR:-/workspace/runtime}"

mkdir -p "${AGENT_OUT_DIR}"
META_FILE="${AGENT_OUT_DIR}/meta.json"
TRACE_FILE="${AGENT_OUT_DIR}/trace.jsonl"
ANSWER_FILE="${AGENT_OUT_DIR}/answer.txt"
RUN_LOG="${AGENT_OUT_DIR}/run.log"

_log() { echo "[$(date -u +%H:%M:%S)Z][codex-entry] $*" | tee -a "${RUN_LOG}"; }

_finalize() {
    local exit_code=$1
    local end_epoch
    end_epoch=$(date +%s)
    local duration=$(( end_epoch - START_EPOCH ))

    python3 - "${TRACE_FILE}" "${META_FILE}" \
        "${AGENT_TASK_ID}" "${AGENT_MODEL}" "${START_TS}" \
        "${duration}" "${exit_code}" "${AGENT_MAX_TURNS}" <<'PY'
import json, sys
trace_path, meta_path = sys.argv[1], sys.argv[2]
task_id, model, started_at = sys.argv[3], sys.argv[4], sys.argv[5]
duration = int(sys.argv[6]); exit_code = int(sys.argv[7])
max_turns = int(sys.argv[8])

result_subtype, result_is_error, num_turns, result_text = "", None, 0, ""
try:
    with open(trace_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except Exception:
                continue
            t = ev.get("type", "")
            if t == "message" and ev.get("role") == "assistant":
                num_turns += 1
            if t == "error":
                result_is_error = True
                result_subtype = "error"
                if isinstance(ev.get("message"), str):
                    result_text = ev["message"]
except FileNotFoundError:
    pass

ok = (exit_code == 0)
if result_is_error is True:
    ok = False
if "API Error" in result_text or "ECONNREFUSED" in result_text:
    ok = False

meta = {
    "task_id":         task_id,
    "model":           model,
    "harness":         "codex",
    "skill_channel":   "preload",
    "started_at":      started_at,
    "duration_sec":    duration,
    "exit_code":       exit_code,
    "ok":              ok,
    "result_subtype":  result_subtype,
    "result_is_error": result_is_error,
    "num_turns":       num_turns,
    "max_turns":       max_turns,
    "files": {
        "trace":  "trace.jsonl",
        "answer": "answer.txt",
        "log":    "run.log",
    },
}
with open(meta_path, "w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)
print(f"[codex-entry] meta.json ok={ok} subtype={result_subtype!r} "
      f"turns={num_turns}/{max_turns}")
PY
}

trap '_finalize $?' EXIT

# ── 1. Prepare cwd and stage assets ──────────────────────────────────
_log "step 1/4: prepare ${AGENT_OUT_DIR}/"
cd "${AGENT_OUT_DIR}"

if [[ -d "/opt/template/assets/${AGENT_TASK_ID}" ]] \
        && [[ -n "$(ls -A /opt/template/assets/${AGENT_TASK_ID} 2>/dev/null)" ]]; then
    mkdir -p assets
    cp -r "/opt/template/assets/${AGENT_TASK_ID}" assets/
    _log "assets staged: $(ls assets/${AGENT_TASK_ID}/ | head)"
else
    _log "WARN: /opt/template/assets/${AGENT_TASK_ID} is missing or empty"
fi

# ── 2. Pre-load skill body into .codex/instructions.md ───────────────
# The pre-load channel concatenates every staged skill's body into a single
# instructions.md that Codex appends to the system prompt each turn.
if [[ -d /opt/template/.claude/skills ]]; then
    mkdir -p .codex
    {
        echo "# Project Skills"
        echo ""
        for skill_dir in /opt/template/.claude/skills/*/; do
            [[ -d "${skill_dir}" ]] || continue
            body=""
            if [[ -f "${skill_dir}SKILL.md" ]]; then
                body="${skill_dir}SKILL.md"
            elif [[ -f "${skill_dir}skill.md" ]]; then
                body="${skill_dir}skill.md"
            fi
            if [[ -n "${body}" ]]; then
                echo "## $(basename "${skill_dir}")"
                echo ""
                cat "${body}"
                echo ""
                echo "---"
                echo ""
            fi
        done
    } > .codex/instructions.md
    _log "skills preloaded -> .codex/instructions.md ($(wc -l < .codex/instructions.md) lines)"
fi

# ── 3. Run Codex CLI (non-interactive) ───────────────────────────────
_log "step 3/4: codex exec --model ${AGENT_MODEL} --json"
PROMPT_CONTENT="$(cat "${AGENT_PROMPT_FILE}")"

# Codex refuses to run outside a git repo by default.
if [[ ! -d .git ]]; then
    git init -q
    git add -A 2>/dev/null || true
    git commit -q -m "init" --allow-empty 2>/dev/null || true
fi

# OPENAI_API_KEY / OPENAI_BASE_URL are already exported.
# Codex reads OPENAI_API_KEY natively; no custom model_provider needed.
set +e
codex exec \
    --model "${AGENT_MODEL}" \
    -c "approval_policy=\"never\"" \
    --dangerously-bypass-approvals-and-sandbox \
    --skip-git-repo-check \
    --json \
    "${PROMPT_CONTENT}" \
    > "${TRACE_FILE}" 2>>"${RUN_LOG}"
CODEX_EXIT=$?
set -e
_log "codex exit code: ${CODEX_EXIT}"

# ── 4. Extract the final answer from trace.jsonl ─────────────────────
_log "step 4/4: extract final answer -> answer.txt"
python3 - "${TRACE_FILE}" "${ANSWER_FILE}" <<'PY'
import json, sys
trace_path, answer_path = sys.argv[1], sys.argv[2]
chunks = []
try:
    with open(trace_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except Exception:
                continue
            if ev.get("type") == "message" and ev.get("role") == "assistant":
                content = ev.get("content")
                if isinstance(content, str):
                    chunks.append(content)
                elif isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") in ("output_text", "text"):
                            chunks.append(block.get("text", ""))
                        elif isinstance(block, str):
                            chunks.append(block)
except FileNotFoundError:
    pass

answer = "\n".join(t for t in chunks if t).strip()
with open(answer_path, "w", encoding="utf-8") as f:
    f.write(answer)
print(f"[codex-entry] answer.txt: {len(answer)} chars")
PY

ls -la "${AGENT_OUT_DIR}" | tee -a "${RUN_LOG}"

exit "${CODEX_EXIT}"
