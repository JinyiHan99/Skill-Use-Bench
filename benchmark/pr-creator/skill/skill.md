---
name: pr-creator
description: 'Use this skill when asked to create a Pull Request. Ensures all PRs follow the repository established template and standards, including branch management, commit formatting, preflight checks, and proper PR creation via the gh CLI.'
---

# Pull Request Creator

This skill defines the workflow for creating pull requests that comply with repository standards. When this skill is active, PRs must be created through the exact sequence below — do not use the GitHub web interface, IDE-integrated PR tools, or create PRs manually via the API, even if they seem faster for simple changes.

## When to Use This Skill

- When asked to "create a PR", "open a pull request", or "submit changes"
- After completing a feature or fix that needs review
- When preparing changes for merge into the main branch

## Prerequisites

| Tool | Purpose | Verify |
|------|---------|--------|
| `git` | Version control | `git --version` |
| `gh` | GitHub CLI for PR creation | `gh --version` |
| `npm` | Running preflight scripts | `npm --version` |

Verify the GitHub CLI is authenticated: `gh auth status`. If not authenticated, stop and report — do not attempt to create PRs without proper authentication.

## Step-by-Step Workflow

### Step 1: Branch Verification

Before any other action, verify you are NOT on the `main` or `master` branch. Creating commits or PRs from the default branch is the single most dangerous mistake in this workflow:

```bash
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
    echo "ERROR: Cannot create PR from default branch. Create a feature branch first."
    exit 1
fi
```

If currently on `main`/`master`, create a new descriptive branch before proceeding:
```bash
git checkout -b feat/descriptive-branch-name
```

Branch naming convention: `type/short-description` where type is one of: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`. Use hyphens between words, not underscores. Keep under 50 characters total.

### Step 2: Stage and Commit Changes

Check the working tree status and stage changes:
```bash
git status
git add -A
```

Commit messages must follow the Conventional Commits specification exactly:
```
type(scope): description

[optional body]
[optional footer]
```

Valid types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`

The scope is optional but recommended — it should be the module or component name in lowercase. The description (after the colon and space) must:
- Start with a lowercase letter
- Not end with a period
- Be 50 characters or fewer
- Use imperative mood ("add" not "adds" or "added")

```bash
# Correct
git commit -m "feat(auth): add JWT refresh token rotation"
git commit -m "fix(api): handle null response from payment gateway"

# Incorrect — these will fail PR review
git commit -m "Fixed the bug"              # No type, past tense, vague
git commit -m "feat: Add new feature."     # Uppercase, period, vague
git commit -m "FEAT(auth): added login"    # Uppercase type, past tense
```

### Step 3: Locate PR Template

Search for the PR template in standard locations, checking each in order until one is found:

```bash
# Check in order of priority
TEMPLATE=""
for path in \
    ".github/pull_request_template.md" \
    ".github/PULL_REQUEST_TEMPLATE.md" \
    ".github/PULL_REQUEST_TEMPLATE/default.md" \
    "docs/pull_request_template.md"; do
    if [ -f "$path" ]; then
        TEMPLATE="$path"
        break
    fi
done

if [ -z "$TEMPLATE" ]; then
    echo "WARNING: No PR template found. Creating PR with minimal structure."
fi
```

If multiple templates exist in `.github/PULL_REQUEST_TEMPLATE/` directory, list them and select the most appropriate one based on the change type (feature, bugfix, documentation, etc.).

### Step 4: Read and Understand Template

Read the located template to understand its structure:
```bash
cat "$TEMPLATE"
```

Note the sections, checkboxes, and required fields. The template structure must be preserved exactly — do not add, remove, or reorder sections.

### Step 5: Draft PR Description

Fill in the PR template following these rules:
- Preserve all section headers exactly as written
- Fill in every section with relevant content (no empty sections)
- For checkbox lists (`- [ ]`), check only items that are genuinely complete — do not check boxes for work that hasn't been done
- Link to related issues using `Closes #123` or `Relates to #123` syntax
- Include a concise summary of what changed and why in the first section

Write the completed description to a temporary file (required for the `gh` command):
```bash
cat > /tmp/pr_description.md << 'EOF'
## Summary
Brief description of the changes...

## Changes Made
- First change
- Second change

## Testing
- [x] Unit tests added
- [x] Integration tests pass
- [ ] Manual testing performed

Closes #42
EOF
```

### Step 6: Run Preflight Checks

Execute the project's preflight script to ensure all quality gates pass before creating the PR:

```bash
npm run preflight
```

The preflight script typically runs: build compilation, linting, type checking, and test suite. All checks must pass — if any check fails, fix the issue and re-commit before proceeding. Do not create a PR with known failing checks.

If `npm run preflight` is not defined in `package.json`, fall back to running checks individually:
```bash
npm run lint && npm run typecheck && npm run test
```

### Step 7: Push Branch

Verify once more that you're not on the default branch, then push:

```bash
# Safety check before push
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
    echo "CRITICAL: About to push to default branch. Aborting."
    exit 1
fi

git push -u origin HEAD
```

Always use `HEAD` rather than the branch name to avoid typos. The `-u` flag sets the upstream tracking reference for future pushes.

### Step 8: Create PR via gh CLI

Create the pull request using the GitHub CLI with the description file. Never pass the description as an inline string — multi-line Markdown with special characters will break shell escaping:

```bash
gh pr create \
    --title "feat(auth): add JWT refresh token rotation" \
    --body-file /tmp/pr_description.md \
    --base main
```

The PR title must match the commit message format (Conventional Commits). If multiple commits exist on the branch, the PR title should summarize the overall change using the same format.

After creation, clean up the temporary file:
```bash
rm -f /tmp/pr_description.md
```

## Core Principles

1. **Never push to main** — This is the highest priority rule. Verify branch at Step 1 AND Step 7.
2. **Template compliance** — Never skip or ignore the PR template structure.
3. **Honest checkboxes** — Only mark items as complete when they actually are.
4. **Preflight before PR** — All automated checks must pass before PR creation.
5. **CLI over UI** — Use `gh pr create` with `--body-file`, not web interface or inline `--body`.

## Multi-Template Repositories

Some repositories have multiple PR templates for different change types:
```
.github/PULL_REQUEST_TEMPLATE/
├── feature.md
├── bugfix.md
├── documentation.md
└── dependency-update.md
```

When multiple templates exist, select based on the branch prefix:
| Branch Prefix | Template |
|--------------|----------|
| `feat/` | feature.md |
| `fix/` | bugfix.md |
| `docs/` | documentation.md |
| `chore/deps-` | dependency-update.md |

If the prefix doesn't match any template, ask the user which template to use rather than guessing.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `gh` not authenticated | Run `gh auth login` and follow prompts |
| Preflight script missing | Check `package.json` scripts; fall back to individual lint/test |
| PR template not found | Check repository settings; some use CODEOWNERS-based templates |
| Push rejected | Pull latest from remote; rebase if needed |
| Commit format rejected | Amend the commit message to follow Conventional Commits |

## References

- Conventional Commits specification (conventionalcommits.org)
- GitHub CLI (`gh`) documentation
- GitHub PR template documentation
