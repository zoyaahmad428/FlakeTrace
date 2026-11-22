# W35 follow-up: short design

**Status:** approved by M2 on 2026-11-22.

**Intent.** A pair-mode diagnosis must read the same everywhere: in a replay, in the contract and in the claims
ledger. M3 found (PR #164) that `replay_steps` never sets `reproduced_by`/`search_mode`, so a replayed pair-mode
bundle would be reported as `"order"`, with `order_exploration` and without the constructed-pair line.

**Goals:** (1) replay carries the original's `search_mode` (record header, checksummed) and `reproduced_by` (original
report); a replay where the victim fails alone is `"order"`; the replay's record header has `search_mode`.
(2) Interface 9's limitation sentence and ADR-016 §3's `"order"` definition take the wording agreed by M1, M2, M3 on
2026-11-22. (3) Claim E16 settled (M1 #163, M3 #164). **Non-goal:** M3's zero-pairs `verify` edge (her code).

**Approaches.** (A, chosen) pass the two values into `replay_steps` from `replay()`. (B) infer pair mode in
`eval/report.py` from the sequence shape: M3's file, and a guess where the record already says. (C) re-derive from
the record's `pair` lines in replay: duplicates `verify`'s walk for a value the record header already holds.

**Verification.** Tests fail first; a fake-runner pair-mode bundle replayed end to end through `assemble_report`
(`reproduced_by "pair"`, the constructed-pair line, no `order_exploration`); `runner.tests.test_replay` and
`eval/tests` pass.
