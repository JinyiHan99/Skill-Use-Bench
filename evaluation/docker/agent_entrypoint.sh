#!/usr/bin/env bash
# agent_entrypoint.sh -- Claude Code harness entrypoint for Skill-Use-Bench.
#
# Behaviour (one container = one model = one task):
#   1. Prepare /workspace/runtime/ as the agent cwd; stage the task asset
#      directory (/opt/template/assets/<TASK_ID>/) and the skill directory
#      (/opt/template/.claude/skills/<name>/) into it.
#   2. Point Claude Code CLI at the Anthropic API using the credentials
#      forwarded from the host (ANTHROPIC_API_KEY / optional ANTHROPIC_BASE_URL).
#   3. Run `claude -p ...` in stream-json mode; write the trace to trace.jsonl
#      and the extracted final reply to answer.txt.
#   4. Write meta.json summarising exit code, ok/fail, num_turns.
#
# Required environment variables:
#   AGENT_MODEL          Model name accepted by Claude Code (e.g. claude-opus-4-8).
#   AGENT_PROMPT_FILE    Absolute path (inside the container) to the prompt file.
#   AGENT_TASK_ID        Task identifier; controls which assets/ subtree to stage.
#   ANTHROPIC_API_KEY    Credential for the Anthropic API.
#
# Optional:
#   AGENT_MAX_TURNS      Default 20.
#   AGENT_OUT_DIR        Default /workspace/runtime.
#   ANTHROPIC_BASE_URL   Override for Anthropic-compatible endpoints.

set -uo pipefail   # do NOT enable -e; we always want to persist artefacts

START_TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
START_EPOCH=$(date +%s)

: "${AGENT_MODEL:?AGENT_MODEL is required}"
: "${AGENT_PROMPT_FILE:?AGENT_PROMPT_FILE is required}"
: "${AGENT_TASK_ID:?AGENT_TASK_ID is required}"
: "${ANTHROPIC_API_KEY:?ANTHROPIC_API_KEY is required (forward from host)}"

AGENT_MAX_TURNS="${AGENT_MAX_TURNS:-20}"
AGENT_OUT_DIR="${AGENT_OUT_DIR:-/workspace/runtime}"

mkdir -p "${AGENT_OUT_DIR}"
META_FILE="${AGENT_OUT_DIR}/meta.json"
TRACE_FILE="${AGENT_OUT_DIR}/trace.jsonl"
ANSWER_FILE="${AGENT_OUT_DIR}/answer.txt"
RUN_LOG="${AGENT_OUT_DIR}/run.log"

_log() { echo "[$(date -u +%H:%M:%S)Z][cc-entry] $*" | tee -a "${RUN_LOG}"; }

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

result_subtype = ""
result_is_error = None
num_turns = None
result_text = ""
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
            if ev.get("type") == "result":
                result_subtype = str(ev.get("subtype") or "")
                if "is_error" in ev:
                    result_is_error = bool(ev.get("is_error"))
                num_turns = ev.get("num_turns")
                if isinstance(ev.get("result"), str):
                    result_text = ev["result"]
except FileNotFoundError:
    pass

ok = (exit_code == 0)
if result_is_error is True:
    ok = False
if result_subtype.startswith("error"):
    ok = False
if "API Error" in result_text:
    ok = False

meta = {
    "task_id":         task_id,
    "model":           model,
    "harness":         "claude-code",
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
print(f"[cc-entry] meta.json ok={ok} subtype={result_subtype!r} "
      f"is_error={result_is_error} turns={num_turns}/{max_turns}")
PY
}

trap '_finalize $?' EXIT

# ── 1. Prepare cwd and stage assets + skill ──────────────────────────
_log "step 1/4: prepare ${AGENT_OUT_DIR}/, stage assets and skill from /opt/template/"
cd "${AGENT_OUT_DIR}"

if [[ -d "/opt/template/assets/${AGENT_TASK_ID}" ]] \
        && [[ -n "$(ls -A /opt/template/assets/${AGENT_TASK_ID} 2>/dev/null)" ]]; then
    mkdir -p assets
    cp -r "/opt/template/assets/${AGENT_TASK_ID}" assets/
    _log "assets staged: $(ls assets/${AGENT_TASK_ID}/ | head)"
else
    _log "WARN: /opt/template/assets/${AGENT_TASK_ID} is missing or empty"
fi

if [[ -d /opt/template/.claude/skills ]]; then
    mkdir -p .claude
    cp -r /opt/template/.claude/skills .claude/skills
    # Claude Code expects SKILL.md (uppercase). Our source-of-truth on disk is
    # skill.md, so copy the file under both names if only lowercase exists.
    for sd in .claude/skills/*/; do
        if [[ -f "${sd}skill.md" ]] && [[ ! -f "${sd}SKILL.md" ]]; then
            cp "${sd}skill.md" "${sd}SKILL.md"
        fi
    done
    _log "skills installed: $(ls .claude/skills/ | grep -v '^INSTALLED')"
fi

# Don't set CLAUDE_PROJECT_DIR; cwd is the project root.
unset CLAUDE_PROJECT_DIR

# ── 2. Configure Claude Code CLI to hit the Anthropic API directly ───
_log "step 2/4: point Claude Code at ${ANTHROPIC_BASE_URL:-https://api.anthropic.com}"
# ANTHROPIC_API_KEY is already exported by run_task.sh via -e.
# ANTHROPIC_BASE_URL is optional; when unset the CLI uses the official endpoint.
export CLAUDE_CODE_AUTO_APPROVE_TOOL_USE="${CLAUDE_CODE_AUTO_APPROVE_TOOL_USE:-1}"

# ── 3. Run Claude Code (non-interactive, stream-json) ────────────────
_log "step 3/4: claude -p --model ${AGENT_MODEL} (max-turns=${AGENT_MAX_TURNS})"
PROMPT_CONTENT="$(cat "${AGENT_PROMPT_FILE}")"

set +e
claude \
    --model "${AGENT_MODEL}" \
    --max-turns "${AGENT_MAX_TURNS}" \
    --output-format stream-json \
    --verbose \
    --include-partial-messages \
    --permission-mode bypassPermissions \
    -p "${PROMPT_CONTENT}" \
    > "${TRACE_FILE}" 2>>"${RUN_LOG}"
CLAUDE_EXIT=$?
set -e
_log "claude exit code: ${CLAUDE_EXIT}"

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
            t = ev.get("type")
            if t == "result" and isinstance(ev.get("result"), str):
                chunks.append(ev["result"])
            elif t == "assistant" and "message" in ev:
                for block in (ev["message"].get("content") or []):
                    if isinstance(block, dict) and block.get("type") == "text":
                        chunks.append(block.get("text", ""))
except FileNotFoundError:
    pass

answer = "\n".join(t for t in chunks if t).strip()
with open(answer_path, "w", encoding="utf-8") as f:
    f.write(answer)
print(f"[cc-entry] answer.txt: {len(answer)} chars")
PY

ls -la "${AGENT_OUT_DIR}" | tee -a "${RUN_LOG}"

exit "${CLAUDE_EXIT}"
