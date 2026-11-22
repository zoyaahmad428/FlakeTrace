# W35 — pair mode: short design

**Status:** approved by M2 on 2026-11-22. Built against ADR-016 (revised, accepted by M1, M2, M3) and Interface 9
(agreed, with the `search_mode` rename).

## Intent

A known victim that never fails in any order FlakeTrace can find (FJ-03; IDoFT's victims, listed with polluters but
no failing order) is diagnosed from the victim alone by running `[candidate, victim]` pairs, the setting where the POC
and RankF measured ranking. Order mode stays exactly as it is.

## Goals, non-goals, anti-goals

- Goals: `--search pairs`; one re-run before a failing pair is adopted; the normal certification after it; the pair
  scan under the budget ledger and the search policy; `reproduced_by`; a `next:` line when order mode ends
  `NOT_REPRODUCED`.
- Non-goals (ADR-016 §4): automatic switching, "all before" orders, cleaner-aware search, a real case with a recorded
  failing order (next iteration).
- Anti-goals: the dataset's polluters reaching the tool (`--order` is refused in pair mode); a one-off failure ending
  the scan; any change to order mode's verdicts.

## Approaches considered

| | Approach | Trade-off | Chosen |
| --- | --- | --- | --- |
| A | Pair mode as its own branch in `run_steps`, sharing the certification tail with order mode | One certification path for both modes; a small refactor of `_steps` | **Yes** |
| B | Pair scan feeding a fake "failing order" into today's `_steps` | No refactor, but the reproduce phase would re-run the pair and the record would mislabel it | No |
| C | A separate `diagnose_pairs` entry point | Duplicates input checks, recording, integrity and the CLI path | No |

## The how (decided)

- `runner/search.py` gains `find_pair(runner, candidates, victim)` next to `find_polluter` (M2's call: same family of
  search functions, so the new `runner/pairs.py` named in the brainstorm is not needed).
- `runner/budget.py`: a `pair` phase, in `EXPLORE`.
- `runner/diagnose.py`: `run_steps(search_mode=…)`, `diagnose(search_mode=…)`; `_steps`' certification tail
  (deletion checks, verify) becomes `_certify`, used by both modes; `DiagnosisRuns` gains `search_mode`,
  `reproduced_by`, `pairs_tried`, `scope_size`.
- `runner/cli.py`: `--search order|pairs`; `--order` with `--search pairs` exits 2; the `next:` line; a `pairs:`
  summary line.

## Calls made by the builder (M2's, for review)

1. `reproduced_by` is `"order"` whenever the reference came from an order FlakeTrace ran in full (the starting
   order, a shuffle, or the victim alone), `"pair"` for an adopted pair, `None` when nothing reproduced.
2. Pair-mode `NOT_REPRODUCED` tallies the pairs' first runs with no reference (a one-off real failure counts as
   `other`); crashes in those runs count as infrastructure failures, as in order mode's reproduce runs. With no
   candidate at all, the alone runs are the tally (M3's code refuses an empty one).
3. A crash in a pair while a polluter is then found is not counted, as in order mode's single search.
4. The budget minimum in pair mode is the reserve plus one pair (no starting order is run).
5. The `next:` line says "re-run with --search pairs" rather than rebuilding the whole command.

## Verification

ADR-016's scripted tests first, seen failing; then the full runner suite; real F1–F4, N1–N4 unchanged; real FJ-03
`--search pairs --scope package` from the victim alone with a bundle (needs JDK 8 and the fastjson checkout).
