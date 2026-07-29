# Skill-Use-Bench

> Companion benchmark for **Skill-Use: Can LLMs Actually Use Skills in Agentic Harnesses?** (AAAI 2027).

Skill-Use-Bench is the data and evaluation release for the Skill-Use benchmark. It measures whether an LLM agent, on its own, can **recognize**, **retrieve**, and **follow** a skill under progressive disclosure, rather than whether a skill helps it finish a task.

- **79 real-world skills**, curated from community repositories.
- **177 executable tasks** across **9 domains**, each grounded in real files.
- **Trajectory-based rubrics** (1:1 with tasks) mixing deterministic verifiers with an LLM judge.
- **Isolated Docker sandbox**; full agent trajectories are logged and scored.
- **Two harnesses**: Claude Code and Codex; 8 frontier LLMs evaluated in the paper.

## What Skill-Use Measures

A skill is a structured document that specifies **when** it applies, **which** procedure to follow, and **which** tools are forbidden. Under progressive disclosure, an agent first sees only a skill's name and one-line description; the full procedure is loaded on demand.

Skill-Use decomposes this ability into three facets and one gated aggregate:

| Facet | What it captures |
| --- | --- |
| **Trigger** | Does the agent invoke the relevant skill from name + description alone? |
| **Compliance** | Does the trajectory follow the prescribed procedure? |
| **Boundary** | Does the trajectory avoid forbidden operations? |
| **Skill-Use (SU)** | `trigger x (0.7 * compliance + 0.3 * boundary)`. Execution earns credit only after the skill is triggered. |

Comp.† and Bound.† denote the same metrics restricted to triggered traces.

## Repository Layout

```
Skill-Use-Bench/
├── benchmark/
│   ├── skill_XX_<name>/              # one directory per skill (79 total)
│   │   ├── skill/
│   │   │   ├── skill.md              # rewritten skill document used at eval time
│   │   │   └── skill.original.md     # original seed for provenance
│   │   ├── tasks/
│   │   │   └── t*_<slug>.yaml        # task definitions (1..k per skill)
│   │   ├── rubrics/
│   │   │   └── rubric_t*_<slug>.yaml # trajectory rubric, 1:1 with tasks
│   │   └── assets/<TASK_ID>/         # real files staged into the sandbox
│   └── _scripts/
│       ├── score_trace.py            # reference scoring engine
│       ├── score_matrix.py           # aggregate SU / Trigger / Comp / Bound
│       └── verify_task_success.py    # task-completion verifier
├── evaluation/
│   ├── docker/                       # sandbox image + entrypoints (CC / Codex)
│   ├── tasks/
│   │   ├── run_task.sh               # single-task runner
│   │   └── run_batch.sh              # batch runner
│   └── evaluate/                     # judge protocol and post-processing
├── docs/                             # design principles and SOPs
└── README.md
```

### Task file (excerpt)

```yaml
# benchmark/skill_03_pdf/tasks/t1_merge_unordered.yaml
task_id: SF03_t1_merge_unordered
skill_id: skill_03_pdf
level: L2
description: |
  I am writing a compliance review. Merge these NIST and IETF PDFs
  in docs/ into a single PDF in the current directory ...
initial_state:
  files: [...]
  binary_assets:                       # real, downloadable source URLs
    - path: docs/rfc9110_http_semantics.pdf
      source_url: https://www.rfc-editor.org/rfc/rfc9110.pdf
      pages: 194
  tools_available: [bash, read, edit, grep]
expected_trigger: true
```

### Rubric file (excerpt)

```yaml
# benchmark/skill_03_pdf/rubrics/rubric_t1_merge_unordered.yaml
rules:
  - id: g1_observable_pdf_attempt        # GATE: evaluability only, not scored
    provenance: gate
    verifier: regex
    signal: { pattern: '\.(pdf|PDF)\b' }

  - id: r1_uses_pdftk_for_pdf_merge      # COMPLIANCE, skill-derived
    provenance: skill
    type: required-tool
    exclusive: true
    weight: 1.5
    signal: { command_pattern: '\bpdftk\b.*\bcat\b.*\boutput\b' }
```

Every rubric item carries a `provenance` (`skill` / `generic` / `task` / `gate`) and a `type` (`required-tool`, `boundary`, `forbidden-tool`, `forbidden-arg`, ...). Only `provenance ∈ {skill, generic}` items with a scored `type` enter Compliance and Boundary; `gate` items only test whether a trace is evaluable.

## Quick Start

### 1. Clone

```bash
git clone https://github.com/<org>/Skill-Use-Bench.git
cd Skill-Use-Bench
```

### 2. Browse a skill

```bash
ls benchmark/skill_03_pdf
# skill/  tasks/  rubrics/  assets/  reports/
cat benchmark/skill_03_pdf/skill/skill.md
cat benchmark/skill_03_pdf/tasks/t1_merge_unordered.yaml
cat benchmark/skill_03_pdf/rubrics/rubric_t1_merge_unordered.yaml
```

### 3. Run one task

```bash
# builds the sandbox image, stages assets, runs the agent, collects trace
bash evaluation/tasks/run_task.sh \
    --skill skill_03_pdf \
    --task  SF03_t1_merge_unordered \
    --model claude-opus-4.8 \
    --harness cc               # cc | codex | codex-native
```

Outputs are written to `runs/<harness>/<model>/<task_id>/`:

- `trace.jsonl`           – normalized agent trajectory
- `gateway_logs/`         – raw LLM I/O, latency, budget
- `meta.json`             – exit code and wall-clock

### 4. Score a trace

```bash
python benchmark/_scripts/score_trace.py \
    --trace runs/cc/claude-opus-4.8/SF03_t1_merge_unordered/trace.jsonl \
    --rubric benchmark/skill_03_pdf/rubrics/rubric_t1_merge_unordered.yaml \
    --out    runs/cc/claude-opus-4.8/SF03_t1_merge_unordered/score.json
```

### 5. Aggregate the leaderboard

```bash
python benchmark/_scripts/score_matrix.py --runs-root runs/ --out leaderboard.csv
```

`score_matrix.py` emits per-model **Trigger**, **Compliance**, **Boundary**, and gated **SU**, matching the paper.

## Reference Numbers

Paper results (best per harness, over 79 skills / 177 tasks):

| Harness      | Best model         | Trigger | Comp.† | Bound.† |   SU   |
| ------------ | ------------------ | :-----: | :----: | :-----: | :----: |
| Claude Code  | GPT-5.5            |  0.972  | 0.625  |  0.740  | **0.613** |
| Codex        | Claude Opus 4.8    |  0.966  | 0.626  |  0.739  |  0.594  |

Full per-model table, harness-delta correlations, and category-level Compliance / Boundary are in the paper's main results and appendix.

## Extending the Benchmark

Adding a new skill follows the pipeline in `docs/`:

1. Seed a skill from a community repo, rewrite it against the constraints in `docs/skill_rewrite_design_principles.md`.
2. Author 1–k executable tasks with real assets (`docs/task_construction_rules.md`).
3. Author a trajectory rubric (`docs/rubric_design_principles.md`), one item per verifiable requirement.
4. Run the three-stage validation: masked-skill screening, multi-agent adversarial review, end-to-end dry-run.

`docs/BATCH_SYNTHESIS_SOP.md` walks through the full seven-stage SOP.

## License

- **Code** (`benchmark/_scripts/`, `evaluation/`): MIT.
- **Skill documents, tasks, rubrics**: CC BY 4.0.
- **Third-party assets** under `benchmark/*/assets/`: retain their original licenses; source URLs are listed in each task's `binary_assets.source_url`.

## Citation

```bibtex
@inproceedings{skilluse2027,
  title     = {Skill-Use: Can LLMs Actually Use Skills in Agentic Harnesses?},
  author    = {Anonymous},
  booktitle = {Proceedings of AAAI},
  year      = {2027}
}
```

## Acknowledgments

Skills are curated from public community repositories; each `skill.original.md` preserves the seed for attribution. We thank the maintainers of Claude Code and OpenAI Codex for the harness specifications that made cross-harness evaluation possible.
