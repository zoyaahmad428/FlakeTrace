# Replay: the mode comes from the record (short design)

**Status:** approved by M2 on 2026-11-24 (design B).

**Intent.** M1 (PR #169) replayed a pair-mode bundle written between #160 (the runner writes `search_mode`) and
#164 (the report has `reproduced_by`); replay labelled it `"order"`, because `runner/replay.py` trusted the report's
field and fell back to `"order"` when it was missing, although the checksummed record header said `"pairs"`.

**The fact the design rests on.** Replay only accepts a report that blames polluters (R1). In order mode the only
way to blame one is a failing starting or shuffled order (`"order"`); in pair mode, an adopted pair (`"pair"`). So
for every replayable bundle `reproduced_by` is determined by the record header's `search_mode`.

**Approaches.** (A) trust the report, fall back to the header: two sources with a precedence rule; a disagreement is
silently believed. (B, chosen) derive from the header (`"pairs"` → `"pair"`, else `"order"`); a report whose field
disagrees is refused, exit 2, "the bundle was changed" — the R2 rule replay already applies to `n` and `lifecycle`.
(C) walk the record's `pair` lines: recomputes what `verify` checks, for a fact the header states.

**Goals:** M1's in-between bundle replays as `"pair"`; new pair and pre-W35 order bundles unchanged; a disagreement is
refused. **Non-goals:** M3's schema fix (pre-W35 bundles fail `verify`); the CI guard (after her fix).

**Verification.** The three tests fail first where expected; `runner.tests.test_replay` and `eval/tests` pass.
