#!/usr/bin/env bash
# tasks/run_task.sh -- run one (skill, task, model) triple in a Docker sandbox.
#
# Usage:
#   bash evaluation/tasks/run_task.sh \
#       --skill pdftk-server \
#       --task  SF03_t1_merge_unordered \
#       --model claude-opus-4-8 \
#       --harness cc                 # cc | codex | codex-native
#
# Optional:
#   --max-turns N        agent max-turns (default 20)
#   --timeout SEC        single-container timeout in seconds (default 900)
#   --out-dir DIR        override output directory
#   --rebuild            docker build --no-cache before running
#   --build-only         only build the images, don't run
#
# Environment (forwarded into the container):
#   ANTHROPIC_API_KEY    required for --harness cc
#   OPENAI_API_KEY       required for --harness codex / codex-native
#   ANTHROPIC_BASE_URL   optional override for Anthropic-compatible endpoints
#   OPENAI_BASE_URL      optional override for OpenAI-compatible endpoints
#
# Output layout:
#   runs/<harness>/<model>/<task_id>/
#     ├── trace.jsonl        normalised agent trajectory
#     ├── answer.txt         final text response
#     ├── run.log            container-side log
#     ├── meta.json          exit code, num_turns, timings
#     ├── launch.log         host-side launcher log
#     ├── initial_prompt.json   (codex-native only)
#     └── skill_manifest.json   (codex-native only)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

SKILL=""
TASK=""
MODEL=""
HARNESS="cc"
MAX_TURNS=20
TIMEOUT_SEC=900
OUT_DIR=""
DO_REBUILD=0
BUILD_ONLY=0

usage() {
    cat >&2 <<EOF
usage: $0 --skill <skill_name> --task <task_id> --model <model> [--harness cc|codex|codex-native]
       [--max-turns N] [--timeout SEC] [--out-dir DIR] [--rebuild] [--build-only]
EOF
    exit 2
}

while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --skill)        SKILL="$2"; shift 2 ;;
        --task)         TASK="$2"; shift 2 ;;
        --model)        MODEL="$2"; shift 2 ;;
        --harness)      HARNESS="$2"; shift 2 ;;
        --max-turns)    MAX_TURNS="$2"; shift 2 ;;
        --timeout)      TIMEOUT_SEC="$2"; shift 2 ;;
        --out-dir)      OUT_DIR="$2"; shift 2 ;;
        --rebuild)      DO_REBUILD=1; shift ;;
        --build-only)   BUILD_ONLY=1; shift ;;
        -h|--help)      usage ;;
        *)              echo "[ERROR] unknown arg: $1" >&2; usage ;;
    esac
done

[[ -z "${SKILL}" || -z "${TASK}" || (${BUILD_ONLY} -eq 0 && -z "${MODEL}") ]] && usage
command -v python3 >/dev/null || { echo "[ERROR] python3 required" >&2; exit 2; }
command -v docker  >/dev/null || { echo "[ERROR] docker required"  >&2; exit 2; }

case "${HARNESS}" in
    cc|codex|codex-native) ;;
    *) echo "[ERROR] --harness must be one of: cc | codex | codex-native" >&2; exit 2 ;;
esac

SKILL_DIR="${ROOT_DIR}/benchmark/${SKILL}"
[[ -d "${SKILL_DIR}" ]] || { echo "[ERROR] skill not found: ${SKILL_DIR}" >&2; exit 2; }

# ── Locate task yaml by scanning tasks/*.yaml for `task_id: <TASK>` ────
TASK_YAML=""
for y in "${SKILL_DIR}/tasks"/*.yaml; do
    [[ -f "${y}" ]] || continue
    if grep -q "^task_id:[[:space:]]*${TASK}[[:space:]]*$" "${y}"; then
        TASK_YAML="${y}"
        break
    fi
done
[[ -n "${TASK_YAML}" ]] || { echo "[ERROR] task_id=${TASK} not found under ${SKILL_DIR}/tasks/" >&2; exit 2; }

ASSETS_DIR="${SKILL_DIR}/assets/${TASK}"
if [[ ! -d "${ASSETS_DIR}" ]]; then
    echo "[WARN] assets dir missing: ${ASSETS_DIR} (task may not need any)"
fi

# ── Ensure images exist ───────────────────────────────────────────────
BASE_IMAGE="skill-use-bench:latest"
RUNNER_IMAGE="skill-use-bench-runner:latest"

if [[ "${DO_REBUILD}" -eq 1 ]] || ! docker image inspect "${BASE_IMAGE}" >/dev/null 2>&1; then
    echo "[run_task] building base image ${BASE_IMAGE}"
    BUILD_FLAGS=()
    [[ "${DO_REBUILD}" -eq 1 ]] && BUILD_FLAGS+=(--no-cache)
    docker build "${BUILD_FLAGS[@]}" \
        -t "${BASE_IMAGE}" \
        -f "${ROOT_DIR}/evaluation/docker/Dockerfile" \
        "${ROOT_DIR}"
fi

if [[ "${DO_REBUILD}" -eq 1 ]] || ! docker image inspect "${RUNNER_IMAGE}" >/dev/null 2>&1; then
    echo "[run_task] building runner image ${RUNNER_IMAGE}"
    BUILD_FLAGS=()
    [[ "${DO_REBUILD}" -eq 1 ]] && BUILD_FLAGS+=(--no-cache)
    docker build "${BUILD_FLAGS[@]}" \
        -t "${RUNNER_IMAGE}" \
        -f "${ROOT_DIR}/evaluation/docker/Dockerfile.task" \
        "${ROOT_DIR}"
fi

if [[ "${BUILD_ONLY}" -eq 1 ]]; then
    echo "[run_task] --build-only complete"
    exit 0
fi

# ── Stage per-task template dir (skill + assets + prompt) ─────────────
_STAGE_SUFFIX="${STAGE_SUFFIX:-$$}"
STAGE_ROOT="${ROOT_DIR}/.staged/${SKILL}_${TASK}_${_STAGE_SUFFIX}"
TEMPLATE_ROOT="${STAGE_ROOT}/template"
rm -rf "${STAGE_ROOT}"
mkdir -p "${TEMPLATE_ROOT}/.claude/skills/${SKILL}" "${TEMPLATE_ROOT}/assets"

# Skill body (staged as SKILL.md so both Anthropic and Codex CLIs are happy).
if [[ -f "${SKILL_DIR}/skill/skill.md" ]]; then
    cp "${SKILL_DIR}/skill/skill.md" "${TEMPLATE_ROOT}/.claude/skills/${SKILL}/SKILL.md"
elif [[ -f "${SKILL_DIR}/skill/SKILL.md" ]]; then
    cp "${SKILL_DIR}/skill/SKILL.md" "${TEMPLATE_ROOT}/.claude/skills/${SKILL}/SKILL.md"
else
    echo "[ERROR] skill body missing: ${SKILL_DIR}/skill/skill.md" >&2
    exit 2
fi
# Extras (references/, scripts/, top-level .py) that some skills bundle.
for extra in references scripts; do
    if [[ -d "${SKILL_DIR}/skill/${extra}" ]]; then
        cp -r "${SKILL_DIR}/skill/${extra}" "${TEMPLATE_ROOT}/.claude/skills/${SKILL}/"
    fi
done
for pyfile in "${SKILL_DIR}/skill"/*.py; do
    [[ -f "${pyfile}" ]] && cp "${pyfile}" "${TEMPLATE_ROOT}/.claude/skills/${SKILL}/"
done
echo "${TASK}|${SKILL}" > "${TEMPLATE_ROOT}/.claude/skills/INSTALLED.txt"

# Task assets
if [[ -d "${ASSETS_DIR}" ]]; then
    mkdir -p "${TEMPLATE_ROOT}/assets/${TASK}"
    cp -r "${ASSETS_DIR}/." "${TEMPLATE_ROOT}/assets/${TASK}/"
fi

# Rendered prompt.txt
python3 "${SCRIPT_DIR}/_build_prompt_from_task.py" \
    --task "${TASK_YAML}" \
    --task-id "${TASK}" \
    --out "${STAGE_ROOT}/prompt.txt"

# ── Prepare output directory ─────────────────────────────────────────
SAFE_MODEL="${MODEL//\//_}"
: "${OUT_DIR:="${ROOT_DIR}/runs/${HARNESS}/${SAFE_MODEL}/${TASK}"}"
TS="$(date +%Y%m%d-%H%M%S)"
CONTAINER="sub-${HARNESS}-${SAFE_MODEL}-${TASK}-${TS}-$$"
CONTAINER="${CONTAINER//./_}"
LAUNCH_LOG="${OUT_DIR}/launch.log"

# Archive any previous run
if [[ -d "${OUT_DIR}" ]] && [[ -f "${OUT_DIR}/trace.jsonl" ]]; then
    ARCH="${OUT_DIR}/_archive/run_$(date -r "${OUT_DIR}/trace.jsonl" +%Y%m%d-%H%M%S 2>/dev/null || echo old)"
    mkdir -p "${ARCH}"
    mv "${OUT_DIR}/trace.jsonl" "${OUT_DIR}/meta.json" "${OUT_DIR}/answer.txt" \
       "${OUT_DIR}/run.log" "${OUT_DIR}/launch.log" "${ARCH}/" 2>/dev/null || true
fi

mkdir -p "${OUT_DIR}"
chmod 777 "${OUT_DIR}"   # container runs as uid 1000 and must write here

# Clean any root-owned stale files from previous runs
rm -rf "${OUT_DIR}/.codex_home" "${OUT_DIR}/assets" 2>/dev/null || true
rm -f  "${OUT_DIR}/skill_manifest.json" "${OUT_DIR}/initial_prompt.json" \
       "${OUT_DIR}/answer.txt" "${OUT_DIR}/trace.jsonl" "${OUT_DIR}/meta.json" \
       "${OUT_DIR}/run.log" 2>/dev/null || true

# ── Harness selection ────────────────────────────────────────────────
case "${HARNESS}" in
    cc)           ENTRYPOINT="/opt/agent/agent_entrypoint.sh" ;;
    codex)        ENTRYPOINT="/opt/agent/codex_entrypoint.sh" ;;
    codex-native) ENTRYPOINT="/opt/agent/codex_native_skill_entrypoint.sh" ;;
esac

# ── API key forwarding ───────────────────────────────────────────────
ENV_ARGS=(
    -e "AGENT_MODEL=${MODEL}"
    -e "AGENT_TASK_ID=${TASK}"
    -e "AGENT_PROMPT_FILE=/workspace/prompt.txt"
    -e "AGENT_MAX_TURNS=${MAX_TURNS}"
    -e "HOME=/home/agent"
)
case "${HARNESS}" in
    cc)
        [[ -z "${ANTHROPIC_API_KEY:-}" ]] && { echo "[ERROR] ANTHROPIC_API_KEY not set" >&2; exit 2; }
        ENV_ARGS+=(-e "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}")
        [[ -n "${ANTHROPIC_BASE_URL:-}" ]] && ENV_ARGS+=(-e "ANTHROPIC_BASE_URL=${ANTHROPIC_BASE_URL}")
        ;;
    codex|codex-native)
        [[ -z "${OPENAI_API_KEY:-}" ]] && { echo "[ERROR] OPENAI_API_KEY not set" >&2; exit 2; }
        ENV_ARGS+=(-e "OPENAI_API_KEY=${OPENAI_API_KEY}")
        [[ -n "${OPENAI_BASE_URL:-}" ]] && ENV_ARGS+=(-e "OPENAI_BASE_URL=${OPENAI_BASE_URL}")
        ;;
esac

# ── Run ──────────────────────────────────────────────────────────────
{
    echo "[$(date -u +%H:%M:%S)Z] start"
    echo "  container : ${CONTAINER}"
    echo "  skill     : ${SKILL}"
    echo "  task      : ${TASK}"
    echo "  model     : ${MODEL}"
    echo "  harness   : ${HARNESS}"
    echo "  out_dir   : ${OUT_DIR}"
} > "${LAUNCH_LOG}"

rc=0
if command -v timeout >/dev/null 2>&1; then
    timeout --preserve-status --signal=TERM "${TIMEOUT_SEC}s" \
        docker run --rm \
        --name "${CONTAINER}" \
        --user 1000:1000 \
        "${ENV_ARGS[@]}" \
        -v "${STAGE_ROOT}/prompt.txt:/workspace/prompt.txt:ro" \
        -v "${OUT_DIR}:/workspace/runtime" \
        -v "${TEMPLATE_ROOT}:/opt/template:ro" \
        "${RUNNER_IMAGE}" \
        "${ENTRYPOINT}" \
        >> "${LAUNCH_LOG}" 2>&1 || rc=$?
else
    docker run --rm \
        --name "${CONTAINER}" \
        --user 1000:1000 \
        "${ENV_ARGS[@]}" \
        -v "${STAGE_ROOT}/prompt.txt:/workspace/prompt.txt:ro" \
        -v "${OUT_DIR}:/workspace/runtime" \
        -v "${TEMPLATE_ROOT}:/opt/template:ro" \
        "${RUNNER_IMAGE}" \
        "${ENTRYPOINT}" \
        >> "${LAUNCH_LOG}" 2>&1 || rc=$?
fi

docker rm -f "${CONTAINER}" >/dev/null 2>&1 || true
echo "[$(date -u +%H:%M:%S)Z] end rc=${rc}" >> "${LAUNCH_LOG}"

# ── Post-run sanity checks ───────────────────────────────────────────
if [[ "${rc}" -eq 0 ]]; then
    if [[ ! -s "${OUT_DIR}/trace.jsonl" ]]; then
        rc=90
        echo "[$(date -u +%H:%M:%S)Z] silent-fail: trace.jsonl empty" >> "${LAUNCH_LOG}"
    elif [[ ! -f "${OUT_DIR}/meta.json" ]]; then
        rc=90
        echo "[$(date -u +%H:%M:%S)Z] silent-fail: meta.json missing" >> "${LAUNCH_LOG}"
    elif ! grep -q '"ok"[[:space:]]*:[[:space:]]*true' "${OUT_DIR}/meta.json" 2>/dev/null; then
        rc=90
        echo "[$(date -u +%H:%M:%S)Z] silent-fail: meta.ok != true" >> "${LAUNCH_LOG}"
    fi
fi

# Clean up the stage dir on success (leave it for debugging on failure)
if [[ "${rc}" -eq 0 ]]; then
    rm -rf "${STAGE_ROOT}"
fi

if [[ "${rc}" -eq 0 ]]; then
    echo "[run_task] OK   ${SKILL}/${TASK} @ ${MODEL} (${HARNESS})"
else
    echo "[run_task] FAIL ${SKILL}/${TASK} @ ${MODEL} (${HARNESS}) rc=${rc}; see ${LAUNCH_LOG}"
fi
exit "${rc}"
