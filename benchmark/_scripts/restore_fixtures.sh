#!/usr/bin/env bash
# Restore git-history fixtures for tasks that need a live .git directory.
#
# Some benchmark tasks (code-review-expert, git-workflows, using-git-worktrees)
# depend on nested Git repositories in their `assets/<task>/input/` directories.
# Nested `.git` directories cannot be tracked directly by an outer Git repo, so
# each affected `input/` folder is shipped as `input.tgz` and expanded here.
#
# Usage:
#   bash benchmark/_scripts/restore_fixtures.sh          # extract, keep tarballs
#   bash benchmark/_scripts/restore_fixtures.sh --clean  # extract then remove tarballs
#
# Idempotent: if `input/` already exists next to `input.tgz`, that task is skipped.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CLEAN=0
if [[ "${1:-}" == "--clean" ]]; then
    CLEAN=1
fi

count=0
skipped=0

while IFS= read -r -d '' tgz; do
    dir="$(dirname "$tgz")"
    if [[ -d "$dir/input" ]]; then
        echo "  skip (already restored): $tgz"
        skipped=$((skipped + 1))
        continue
    fi
    echo "  extracting: $tgz"
    tar -xzf "$tgz" -C "$dir"
    if [[ "$CLEAN" -eq 1 ]]; then
        rm -f "$tgz"
    fi
    count=$((count + 1))
done < <(find "$REPO_ROOT/benchmark" -type f -name 'input.tgz' -print0)

echo
echo "Restored: $count  Skipped: $skipped"
