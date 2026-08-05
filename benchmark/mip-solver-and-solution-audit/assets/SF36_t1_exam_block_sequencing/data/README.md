# Exam Block Sequencing Data

This directory contains a generated block-sequencing instance for a university final-exam scheduling workflow.

Instance configuration:

- num_blocks: 12
- num_slots: 12
- schedule_layout: 3 days × 4 slots per day (slots 1-4: day 1, 5-8: day 2, 9-12: day 3)
- frontload_block_size_cutoff: 300
- frontload_slot_cutoff: 10

Files:

- `instance.json`: block labels, slot/window categories, large-block list, and early-slot list.
- `pair_counts.csv`: ordered block-pair co-enrollment counts.
- `triplet_counts.csv`: ordered block-triplet co-enrollment counts.
- `blockmap.csv`: mapping from individual exams to generated blocks.
- `block_summary.csv`: summary of block sizes and contextual block information.

Use `instance.json` as the source of truth for the block set, slot order, window categories, large blocks, and early slots.

The pair and triplet count tables are ordered. Use keys in the order induced by the submitted schedule; do not sort or symmetrize pair or triplet keys.

The objective measures student burden from close exam placements: adjacent back-to-back windows use `pair_counts.csv`, three-slot windows use `triplet_counts.csv`, and the overlapping four-slot pressure term applies when two qualifying three-slot windows start in consecutive slots. If the four consecutive assigned blocks are `a, b, c, d`, the overlap pressure uses the ordered triplets `(a,b,c)` and `(a,c,d)`. It is not the sum of all unordered triples inside the four-slot span.

The slot-window categories and front-loading lists come from `instance.json`.

Slot layout (3 days × 4 slots):
- Day 1: slots 1, 2, 3, 4
- Day 2: slots 5, 6, 7, 8
- Day 3: slots 9, 10, 11, 12
- Evening-to-morning transitions: slot 4→5 (day 1 end → day 2 start), slot 8→9 (day 2 end → day 3 start)

Recommended solver time limit: 120 seconds. A time-limit-feasible incumbent solution is acceptable.
