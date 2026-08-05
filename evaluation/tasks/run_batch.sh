#!/usr/bin/env bash
# tasks/run_batch.sh -- convenience wrapper to run many (task, model) pairs.
#
# Usage:
#   bash evaluation/tasks/run_batch.sh \
#       --tasks tasks.jsonl \
#       --models "claude-opus-4-8,gpt-5" \
#       --harness cc \
#       [--concurrency N] [--max-turns N] [--timeout SEC]
#
# tasks.jsonl format (one JSON object per line):
#   {"skill": "pdftk-server", "task": "SF03_t1_merge_unordered"}
#   {"skill": "git-workflows", "task": "SF101_t1_recover_deleted_branch"}
#
# Fails-open: individual failures are logged; the batch continues.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

TASKS_FILE=""
MODELS=""
HARNESS="cc"
CONCURRENCY=1
MAX_TURNS=20
TIMEOUT_SEC=900

usage() {
    cat >&2 <<EOF
usage: $0 --tasks <tasks.jsonl> --models "a,b,c" [--harness cc|codex|codex-native]
       [--concurrency N] [--max-turns N] [--timeout SEC]
EOF
    exit 2
}

while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --tasks)        TASKS_FILE="$2"; shift 2 ;;
        --models)       MODELS="$2"; shift 2 ;;
        --harness)      HARNESS="$2"; shift 2 ;;
        --concurrency)  CONCURRENCY="$2"; shift 2 ;;
        --max-turns)    MAX_TURNS="$2"; shift 2 ;;
        --timeout)      TIMEOUT_SEC="$2"; shift 2 ;;
        -h|--help)      usage ;;
        *)              echo "[ERROR] unknown arg: $1" >&2; usage ;;
    esac
done

[[ -z "${TASKS_FILE}" || -z "${MODELS}" ]] && usage
[[ -f "${TASKS_FILE}" ]] || { echo "[ERROR] tasks file not found: ${TASKS_FILE}" >&2; exit 2; }

IFS=',' read -ra MODEL_LIST <<<"${MODELS}"

# Build the job list as (skill, task, model) triples
JOBS=()
while IFS= read -r line; do
    [[ -z "${line// }" ]] && continue
    skill=$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['skill'])" "$line")
    task=$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['task'])" "$line")
    for m in "${MODEL_LIST[@]}"; do
        JOBS+=("${skill}|${task}|${m}")
    done
done < "${TASKS_FILE}"

echo "[run_batch] ${#JOBS[@]} jobs, concurrency=${CONCURRENCY}, harness=${HARNESS}"

run_one() {
    local spec="$1"
    IFS='|' read -r skill task model <<<"${spec}"
    bash "${SCRIPT_DIR}/run_task.sh" \
        --skill "${skill}" \
        --task "${task}" \
        --model "${model}" \
        --harness "${HARNESS}" \
        --max-turns "${MAX_TURNS}" \
        --timeout "${TIMEOUT_SEC}"
}

FAIL=0
if [[ "${CONCURRENCY}" -le 1 ]]; then
    for j in "${JOBS[@]}"; do
        run_one "${j}" || FAIL=$((FAIL+1))
    done
else
    # Simple GNU parallel-free fan-out
    for j in "${JOBS[@]}"; do
        run_one "${j}" &
        while [[ "$(jobs -rp | wc -l)" -ge "${CONCURRENCY}" ]]; do
            sleep 1
        done
    done
    wait
fi

echo "[run_batch] done. failures=${FAIL}/${#JOBS[@]}"
exit "${FAIL}"
