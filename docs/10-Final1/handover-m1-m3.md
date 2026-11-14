# Handover from M2 to M1 and M3 — Iteration 2

*Kept current by M2 at every hand-over. Newest first. A package marked "built" is **not** closed:
it closes only when its verifier has reproduced it ([[10-Final1/iteration-2-plan]]).*

## Waiting on you

| For | What | Where | Why it matters |
| --- | --- | --- | --- |
| **M3** | Review W19 step 1 in **your** file `eval/baseline.py`: `classify`, `RunTally`, `tally`, `SYNTHETIC_PREFIX`, and 14 tests in `eval/tests/test_baseline.py` | PR from `m2/w19-runtally` | Written for you by agreement (2026-11-13); W18 and your W19 build on it |
| **M3** | Add a line for the new types to `eval/README.md` (your file; M2 did not edit it) | `eval/README.md` | Keep your README true |
| **M3** | Check W16 consistency: run the phrase search below over `runner/` and `ui/`, read the new CLI and UI wording against claims ledger G1–G4 | PR from `m2/w16-retire-claims` | You are W16's verifier |
| **M3** | Your part of W16: the `VERIFIED` rationale in `eval/outcome.py` line 218 still says "victim never failed alone, and a resource edge supports it" — G1 and G3 | `eval/` | W16's "Done when" covers every folder; M2 must not edit `eval/` except `eval/baseline.py` |
| **M1** | Your part of W16: check the resource wording `evidence/` puts in reports (`FIXED_LIMITATIONS`, `report_fields`) against ledger G3. A search by M2 found no "cause" or "mechanism" in `evidence/extract.py`, so this may need no change — your call | `evidence/` | Same reason |

## Changes, newest first

### W19 step 1 — `RunTally` and the classifier in `eval/baseline.py` (2026-11-14) · built, awaiting M3's review

**What changed for you (M3):** your file gained, after `RunOutcome`:

```python
SYNTHETIC_PREFIX = "flaketrace."
PASS, MATCH, OTHER, INFRA = "PASS", "MATCH", "OTHER", "INFRA"
classify(outcome, reference) -> str      # INFRA checked first; real failure + reference None -> ValueError
RunTally(n, passed, matched, other, infra)  # frozen; counts >= 0 and must add up to n
tally(outcomes, reference) -> RunTally
```

Nothing existing in the file changed except `Iterable` added to the `typing` import. The runner now imports `SYNTHETIC_PREFIX` from here instead
of defining it. No schema or contract file changed; `DiagnosisRuns` is unchanged until W18.

**Choices M2 made, for you to accept or change:** tests in your `test_baseline.py`; strict
`ValueError` with no reference; the `tally` helper (your recount checker can reuse it).

**To review:**

```
git fetch && git checkout m2/w19-runtally
py -m unittest eval.tests.test_baseline
```

Expected: 27 tests OK. Read `eval/baseline.py` from `SYNTHETIC_PREFIX` to `tally`.


### W16 — retired claims qualified in `runner/` and `ui/` (2026-11-14) · built, awaiting M3

**What changed for you:** nothing in your folders, no contract or schema field. Only text:

| Where | Before | After |
| --- | --- | --- |
| CLI headline, UI outcome | `VERIFIED` | `VERIFIED (sequence)` (ADR-010 Q3) |
| CLI under a shown resource, UI Evidence graph | — / "the shared state that links…" | "static overlap: a possible mechanism, not confirmed as the cause" |
| CLI and UI alone count | `alone: 0/20` / "Victim alone fails" | `alone (same failure): 0/20` / "Victim alone fails with the same failure" — it counts only matching failures (G1) |
| CLI after `ddmin` | "1-minimal, not necessarily the minimum" | "reduced by single-trial delta debugging; not deletion-verified" (G2) |
| UI Source integrity panel | badge only | adds the narrow statement: same SHA-256 outside `target/` and `.git/`, no sandbox (G4) |

**To verify (M3):**

```
git fetch && git checkout m2/w16-retire-claims
py -m unittest runner.tests.test_cli
py -m runner diagnose --project fixtures/od-fixture --victim odfixture.ConfigVictimTest#expectsDefaultMode
git grep -n -i -E "1-minimal|never modified|sandboxed|found mechanism|root cause|caused by|explains the failure|passes alone" -- runner ui .github docs/04-Implementation
```

Expected: tests OK; the command prints the four lines above; the search finds only
`runner/minimise.py:4` ("1-minimal only for the single trials ddmin saw"). Record what you see in
[[evidence-m3]], including anything unclear.

## Coming next from M2

- **W19 step 1** (agreed 2026-11-13): `RunTally` and the outcome classifier in `eval/baseline.py`,
  written by M2 for M3. **M3 reviews it when back** — it is your file.
- **W18**: the runner counts with tallies. M3's `eval/report.py` and `eval/outcome.py` read the
  runner's current count fields by name; how W18 lands without breaking them is a decision M2
  will record here before building.
