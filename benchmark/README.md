# Benchmark Data

This folder holds the released data of **Skill-Use**: the skills, tasks, rubrics, and real assets that define the benchmark, plus the scoring engine that turns an agent trajectory into a score.

> **Note on completeness.** Due to upload-size limits, this repository ships only a **subset** of the full benchmark. The full benchmark comprises 79 skills, 177 tasks, and 177 rubric files (1:1 with tasks); the directories actually present here are a representative selection. The complete set can be made available upon request.

Every task is grounded in real files and is machine-verifiable. Rubrics are the single source of truth for skill-following judgement.

## Top-level layout

```
benchmark/
├── <skill_name>/                 # one directory per skill (subset of 79)
│   ├── skill/skill.md            # the rewritten skill document
│   ├── tasks/*.yaml              # task definitions
│   ├── rubrics/rubric_*.yaml     # trajectory rubric, 1:1 with tasks
│   └── assets/<TASK_ID>/         # real files staged into the sandbox
├── _mapping.json                 # provenance map: source_dir ↔ target_name
```

## Per-skill directory

Each `<skill_name>/` directory is self-contained and follows the same four-part layout.

### `skill/skill.md`

The skill document that an agent harness installs under `.claude/skills/<name>/SKILL.md` (Claude Code) or `$CODEX_HOME/skills/<name>/SKILL.md` (Codex). It begins with a YAML frontmatter:

```yaml
---
name: pdftk-server
description: 'Skill for using the command-line tool pdftk ...'
---
```

The `name:` field is the canonical skill key used everywhere else. The body describes when to trigger, the permitted tools, step-by-step workflows, and boundary rules. Skill documents are format-compatible across Claude Code and Codex; the runtime simply renames `skill.md` to `SKILL.md` when staging.

### `tasks/*.yaml`

One YAML file per task. A task defines the user request, the initial sandbox state, the binary assets to stage, and the skill constraints being tested. Key fields:

- `task_id` — globally unique identifier (e.g. `SF03_t1_merge_unordered`).
- `skill_id` — the source skill directory this task belongs to.
- `level` — difficulty hint (`L1`/`L2`/...).
- `description` — the natural-language prompt shown to the agent.
- `initial_state.files` — text files to write into the sandbox cwd.
- `initial_state.binary_assets` — real files (PDFs, binaries, datasets) staged from `assets/`, each with a `source_url` for licensing traceability.
- `initial_state.tools_available` — tools the agent may use.
- `expected_trigger` — whether the skill should fire for this task.
- `skill_constraints_tested` — the specific skill rules the rubric will check, each with an `exclusive` note explaining how the model's default behavior diverges.

### `rubrics/rubric_*.yaml`

One rubric per task, named `rubric_<task_stem>.yaml`. The rubric is a list of `rules`, each checking one observable property of the trajectory. A rule has:

| Field | Meaning |
| :-- | :-- |
| `id` | Rule identifier. |
| `type` | `required-tool`, `forbidden-tool`, `required-arg`, `order`, `boundary`, `task-completion`, `trigger-condition`, ... |
| `provenance` | Who the rule comes from: `skill`, `generic`, `task`, or `gate`. |
| `locus` | Where the signal lives: `tool-call`, `tool-arg`, `file-state`, `final-output`. |
| `verifier` | How to check it: `regex`, `state-diff`, or `llm-judge`. |
| `severity` | `hard` or `soft`. |
| `exclusive` | `true` if the rule distinguishes skill-following from default behavior. |
| `weight` | Numeric weight. |
| `spec` | Human-readable description; also serves as the LLM-judge prompt context. |
| `signal` | Verifier-specific config (regex pattern, judge question, file path, ...). |

**Provenance controls scoring.** Only rules with `provenance ∈ {skill, generic}` enter the Compliance and Boundary sub-scores. `gate` rules only test whether the trajectory is evaluable (they never affect the score). `task` rules record task-completion rate separately and never enter skill-following.

**Three verifiers:**
- `regex` — pattern-match against serialized tool calls or the final answer. Fast and deterministic.
- `state-diff` — inspect the final state of files copied out of the container cwd (requires a job directory).
- `llm-judge` — send a Yes/No question plus a context window (serialized steps, final answer, first-N tool results) to a judge model (default `gpt-5`).

### `assets/<TASK_ID>/`

Real files that the harness copies into the sandbox for the corresponding task. Asset subdirectories are keyed by `task_id`. These are genuine binaries and datasets (PDFs from NIST/IETF, network captures, radar I/Q samples, git repositories, etc.); each binary asset lists its upstream `source_url` in the task YAML for license attribution. Third-party assets retain their original licenses.

## `_mapping.json`

A provenance map that records, for each released skill, the relationship between the internal source directory and the released target name:

```json
{
  "skills": [
    {
      "src_dir": "skill_03_pdf",
      "src_number": "03",
      "raw_name": "pdftk-server",
      "skill_md": "skill_03_pdf/skill/skill.md",
      "description": "...",
      "target_name": "pdftk-server",
      "stats": { "skill_md": 1, "tasks": 7, "rubrics": 7, "assets": 18 }
    }
    // ... entries for all released skills
  ],
  "totals": { "skill_md": 79, "tasks": 177, "rubrics": 177, "assets": 3709 }  // full-benchmark totals; this repo ships a subset
}
```

Use `target_name` as the canonical directory name in this release. `stats` gives per-skill counts; `totals` gives benchmark-wide sums.

## Naming conventions

- Skill directories are keyed by the `name:` field of `skill.md`, in lowercase.
- **Disambiguation.** Three skill names collide across sources (`docx`, `pdf-editing`, `azure-bgp`). Collisions are resolved by appending the source skill number: `docx-06` and `docx-15`, `pdf-editing-14` and `pdf-editing-30`, `azure-bgp-16` and `azure-bgp-34`.
- Rubric files are named `rubric_<task_stem>.yaml`, matching their task file `<task_stem>.yaml` one-to-one.
- Asset subdirectories are named by `task_id` (e.g. `SF03_t1_merge_unordered/`).

