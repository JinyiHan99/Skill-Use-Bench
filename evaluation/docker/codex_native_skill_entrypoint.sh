#!/usr/bin/env bash
# codex_native_skill_entrypoint.sh -- Codex CLI on-demand skill harness.
#
# Skill loading channel: native progressive disclosure.
#   Skills are installed under $CODEX_HOME/skills/<name>/SKILL.md. Codex
#   scans that directory at startup and injects only the frontmatter
#   (name + description + short path) into the developer prompt. To use a
#   skill the model must actively read SKILL.md via its shell tool. This
#   channel measures the full skill-following ability: discovery + execution.
#
# Required environment variables:
#   AGENT_MODEL          Model name accepted by Codex CLI.
#   AGENT_PROMPT_FILE    Absolute path (inside the container) to the prompt file.
#   AGENT_TASK_ID        Task identifier.
#   OPENAI_API_KEY       Credential for the OpenAI (or compatible) API.
#
# Optional:
#   AGENT_MAX_TURNS      Default 20.
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
SKILL_MANIFEST_FILE="${AGENT_OUT_DIR}/skill_manifest.json"

_log() { echo "[$(date -u +%H:%M:%S)Z][codex-native][cli] $*" | tee -a "${RUN_LOG}"; }

_finalize() {
    local exit_code=$1
    local end_epoch
    end_epoch=$(date +%s)
    local duration=$(( end_epoch - START_EPOCH ))

    python3 - "${TRACE_FILE}" "${META_FILE}" \
        "${AGENT_TASK_ID}" "${AGENT_MODEL}" "${START_TS}" \
        "${duration}" "${exit_code}" "${AGENT_MAX_TURNS}" \
        "${SKILL_MANIFEST_FILE}" "${AGENT_OUT_DIR}/initial_prompt.json" <<'PY'
import json, sys

(trace_path, meta_path, task_id, model, started_at,
 duration_s, exit_s, max_turns_s,
 skill_manifest_path, initial_prompt_path) = sys.argv[1:11]

duration = int(duration_s); exit_code = int(exit_s); max_turns = int(max_turns_s)

result_subtype, result_is_error, num_turns, result_text = "", None, 0, ""
skill_read_events, tool_calls_by_name = [], {}
saw_skill_root_hint = False
enabled_skills = []

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
            if t == "function_call":
                nm = ev.get("name") or (ev.get("function") or {}).get("name") or ""
                tool_calls_by_name[nm] = tool_calls_by_name.get(nm, 0) + 1
                args_raw = ev.get("arguments") or (ev.get("function") or {}).get("arguments") or ""
                if isinstance(args_raw, dict):
                    args_str = json.dumps(args_raw, ensure_ascii=False)
                else:
                    args_str = str(args_raw)
                if "SKILL.md" in args_str:
                    skill_read_events.append({"tool": nm, "args_snippet": args_str[:400]})
            if t == "message" and ev.get("role") == "system":
                content = ev.get("content")
                text = ""
                if isinstance(content, str):
                    text = content
                elif isinstance(content, list):
                    text = "\n".join(
                        b.get("text", "") for b in content
                        if isinstance(b, dict) and b.get("type") in ("text", "output_text")
                    )
                if "Available skills" in text or "Skill roots" in text:
                    saw_skill_root_hint = True
except FileNotFoundError:
    pass

try:
    with open(skill_manifest_path, "r", encoding="utf-8") as f:
        m = json.load(f)
        enabled_skills = m.get("skills", [])
except Exception:
    pass

initial_prompt_has_skills_section = False
initial_prompt_injected_names = []
initial_prompt_all_available = []
try:
    prompt = json.load(open(initial_prompt_path))
    all_text = ""
    for msg in prompt if isinstance(prompt, list) else []:
        for block in msg.get("content", []) if isinstance(msg, dict) else []:
            if isinstance(block, dict):
                all_text += block.get("text", "") + "\n"
    initial_prompt_has_skills_section = "### Available skills" in all_text
    if initial_prompt_has_skills_section:
        section = all_text.split("### Available skills", 1)[1].split("### How to use skills", 1)[0]
        for line in section.splitlines():
            line = line.lstrip()
            if line.startswith("- "):
                head = line[2:].split(":", 1)[0].strip()
                if head and head not in initial_prompt_all_available:
                    initial_prompt_all_available.append(head)
    for sk in enabled_skills:
        nm = sk.get("name", "")
        if nm and nm in all_text:
            initial_prompt_injected_names.append(nm)
except FileNotFoundError:
    pass
except Exception:
    pass

ok = (exit_code == 0)
if result_is_error is True:
    ok = False
if "API Error" in result_text or "ECONNREFUSED" in result_text:
    ok = False

injection_ok = None
if enabled_skills:
    injection_ok = len(initial_prompt_injected_names) > 0

meta = {
    "task_id":         task_id,
    "model":           model,
    "harness":         "codex-native",
    "skill_channel_mode": "codex_home_native",
    "started_at":      started_at,
    "duration_sec":    duration,
    "exit_code":       exit_code,
    "ok":              ok,
    "result_subtype":  result_subtype,
    "result_is_error": result_is_error,
    "num_turns":       num_turns,
    "max_turns":       max_turns,
    "skill_channel": {
        "mode":                          "codex_home_native",
        "install_root":                  "$CODEX_HOME/skills/",
        "builtin_noise_present":         True,
        "enabled_skills":                enabled_skills,
        "skill_root_injected":           saw_skill_root_hint,
        "skill_read_events":             skill_read_events,
        "skill_read_count":              len(skill_read_events),
        "initial_prompt_verified":       initial_prompt_has_skills_section,
        "initial_prompt_injected_names": initial_prompt_injected_names,
        "initial_prompt_all_available":  initial_prompt_all_available,
        "injection_ok":                  injection_ok,
    },
    "tool_calls": tool_calls_by_name,
    "files": {
        "trace":          "trace.jsonl",
        "answer":         "answer.txt",
        "log":            "run.log",
        "skill_manifest": "skill_manifest.json",
        "initial_prompt": "initial_prompt.json",
    },
}
with open(meta_path, "w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)
print(f"[codex-native] meta.json ok={ok} "
      f"turns={num_turns}/{max_turns} "
      f"injected={initial_prompt_injected_names} "
      f"skill_reads={len(skill_read_events)}")
PY
}

trap '_finalize $?' EXIT

# ── 1. Per-task isolated CODEX_HOME ──────────────────────────────────
CODEX_HOME_DIR="${AGENT_OUT_DIR}/.codex_home"
rm -rf "${CODEX_HOME_DIR}" 2>/dev/null || true
mkdir -p "${CODEX_HOME_DIR}"
export CODEX_HOME="${CODEX_HOME_DIR}"
_log "step 1/6: CODEX_HOME=${CODEX_HOME}"

# Minimal config.toml. No custom model_provider is defined; Codex uses the
# built-in OpenAI provider (or whatever OPENAI_BASE_URL points at).
cat > "${CODEX_HOME}/config.toml" <<TOML
approval_policy    = "never"
sandbox_mode       = "workspace-write"
disable_response_storage = true
TOML

# ── 2. Register skills into $CODEX_HOME/skills/ ──────────────────────
_log "step 2/6: register skills under \$CODEX_HOME/skills/"
mkdir -p "${CODEX_HOME}/skills"

python3 - "${CODEX_HOME}/skills" "/opt/template/.claude/skills" "${SKILL_MANIFEST_FILE}" <<'PY'
"""Copy .claude/skills/<name>/ into $CODEX_HOME/skills/<name>/.

Codex scans the directory, reads each <name>/SKILL.md YAML frontmatter, and
injects (name + description + short path) into the developer prompt.
"""
import json, os, re, shutil, sys

dst_root, src_root, manifest_out = sys.argv[1], sys.argv[2], sys.argv[3]
manifest = {"skills": [], "warnings": []}

if not os.path.isdir(src_root):
    manifest["warnings"].append(f"source not found: {src_root}")
    with open(manifest_out, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print("[skill-register] no skills to register (src missing)")
    sys.exit(0)

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

def parse_frontmatter(md_path):
    try:
        with open(md_path, "r", encoding="utf-8", errors="replace") as f:
            head = f.read(8192)
    except Exception:
        return None
    m = FRONTMATTER_RE.match(head)
    if not m:
        return None
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith((" ", "\t")):
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm

for entry in sorted(os.listdir(src_root)):
    src_dir = os.path.join(src_root, entry)
    if not os.path.isdir(src_dir):
        continue
    src_md = os.path.join(src_dir, "SKILL.md")
    if not os.path.isfile(src_md):
        # Fall back to lowercase skill.md and stage it as SKILL.md.
        alt = os.path.join(src_dir, "skill.md")
        if os.path.isfile(alt):
            shutil.copy2(alt, src_md)
        else:
            manifest["warnings"].append(f"skip {entry}: no SKILL.md nor skill.md")
            continue
    fm = parse_frontmatter(src_md)
    if not fm or "name" not in fm or "description" not in fm:
        manifest["warnings"].append(f"skip {entry}: missing YAML frontmatter name/description")
        continue

    skill_name = fm["name"]
    dst_dir = os.path.join(dst_root, skill_name)
    if os.path.exists(dst_dir):
        shutil.rmtree(dst_dir)
    shutil.copytree(src_dir, dst_dir)
    manifest["skills"].append({
        "name":         skill_name,
        "description":  fm["description"][:300],
        "source_dir":   src_dir,
        "installed_at": dst_dir,
    })
    print(f"[skill-register] registered: {skill_name} <- {src_dir}")

with open(manifest_out, "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)
print(f"[skill-register] total registered: {len(manifest['skills'])}")
PY

# ── 3. Prepare cwd + stage assets ────────────────────────────────────
_log "step 3/6: prepare ${AGENT_OUT_DIR}/"
cd "${AGENT_OUT_DIR}"

if [[ -d "/opt/template/assets/${AGENT_TASK_ID}" ]] \
        && [[ -n "$(ls -A /opt/template/assets/${AGENT_TASK_ID} 2>/dev/null)" ]]; then
    mkdir -p assets
    cp -r "/opt/template/assets/${AGENT_TASK_ID}" assets/
    _log "assets staged: $(ls assets/${AGENT_TASK_ID}/ | head)"
else
    _log "WARN: /opt/template/assets/${AGENT_TASK_ID} is missing or empty"
fi

# Do NOT create .codex/instructions.md here; that would defeat the point of
# on-demand discovery.

# ── 4. Init a throw-away git repo (Codex requires one) ───────────────
if [[ ! -d .git ]]; then
    git init -q
    git add -A 2>/dev/null || true
    git commit -q -m "init" --allow-empty 2>/dev/null || true
fi

_log "\$CODEX_HOME/skills content:"
ls -la "${CODEX_HOME}/skills/" 2>&1 | tee -a "${RUN_LOG}"
if [[ -f "${SKILL_MANIFEST_FILE}" ]]; then
    cat "${SKILL_MANIFEST_FILE}" | tee -a "${RUN_LOG}"
fi

# ── 5. Snapshot the initial prompt for post-hoc discovery verification ─
_log "step 5/6: snapshot Codex initial prompt -> initial_prompt.json"
codex debug prompt-input \
    -c "approval_policy=\"never\"" \
    "$(cat "${AGENT_PROMPT_FILE}")" \
    > "${AGENT_OUT_DIR}/initial_prompt.json" 2>>"${RUN_LOG}" || \
    _log "WARN: codex debug prompt-input failed (non-fatal)"

python3 - "${AGENT_OUT_DIR}/initial_prompt.json" "${SKILL_MANIFEST_FILE}" "${RUN_LOG}" <<'PY'
import json, sys
prompt_path, manifest_path, log_path = sys.argv[1:4]
try:
    prompt = json.load(open(prompt_path))
    manifest = json.load(open(manifest_path))
except Exception as e:
    open(log_path, "a").write(f"[skill-verify] load failed: {e}\n"); sys.exit(0)

all_text = ""
for m in prompt if isinstance(prompt, list) else []:
    for c in m.get("content", []) if isinstance(m, dict) else []:
        if isinstance(c, dict):
            all_text += c.get("text", "") + "\n"

msg = [
    f"[skill-verify] initial_prompt.json size={len(all_text)}",
    f"[skill-verify] has '### Available skills' : {'### Available skills' in all_text}",
]
registered = [s['name'] for s in manifest.get('skills', [])]
for name in registered:
    msg.append(f"[skill-verify]   {name:40s} injected={name in all_text}")
if not registered:
    msg.append("[skill-verify] WARN: no skills registered by skill_manifest.json")
open(log_path, "a").write("\n".join(msg) + "\n")
print("\n".join(msg))
PY

# ── 6. Run Codex CLI ─────────────────────────────────────────────────
_log "step 6/6: codex exec --model ${AGENT_MODEL} --json (native skill mode)"
PROMPT_CONTENT="$(cat "${AGENT_PROMPT_FILE}")"

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

# Extract the final answer
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
print(f"[codex-native] answer.txt: {len(answer)} chars")
PY

ls -la "${AGENT_OUT_DIR}" | tee -a "${RUN_LOG}"

exit "${CODEX_EXIT}"
