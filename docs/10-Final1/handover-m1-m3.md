# Handover from M2 to M1 and M3 — Iteration 2

*Kept current by M2 at every hand-over. Newest first. A package marked "built" is **not** closed:
it closes only when its verifier has reproduced it ([[10-Final1/iteration-2-plan]]).*

## Waiting on you

| For | What | Where | Why it matters |
| --- | --- | --- | --- |
| **M1** | **Run the lifecycle control (W22 verification)** — steps under "W22 job 3" below, on your own machine. When it matches, M2 makes `class-grouped` the default | branch `m2/w22-record-env` | ADR-012 §3; FT006 closes only with your independent run |
| **M1** | Verify W18: run the commands under "W18" below on your machine and record the result in [[evidence-m1]] | PR from `m2/w18-tallies` | You are W18's verifier; FT003 needs an independent reproduction |
| **M3** | W19 can now read `alone_tally` / `sequence_tally` from `DiagnosisRuns`. When it does, remove the old count fields and the `NO_SINGLE_POLLUTER` alias (or ask M2 to) | `runner/diagnose.py`, your `eval/report.py`, `eval/outcome.py` | Until then the verdict for FT003 is still the Mid's |
| **M3** | Review W19 step 1 in **your** file `eval/baseline.py`: `classify`, `RunTally`, `tally`, `SYNTHETIC_PREFIX`, and 14 tests in `eval/tests/test_baseline.py` | PR from `m2/w19-runtally` | Written for you by agreement (2026-11-13); W18 and your W19 build on it |
| **M3** | Add a line for the new types to `eval/README.md` (your file; M2 did not edit it) | `eval/README.md` | Keep your README true |
| **M3** | Check W16 consistency: run the phrase search below over `runner/` and `ui/`, read the new CLI and UI wording against claims ledger G1–G4 | PR from `m2/w16-retire-claims` | You are W16's verifier |
| **M3** | Your part of W16: the `VERIFIED` rationale in `eval/outcome.py` line 218 still says "victim never failed alone, and a resource edge supports it" — G1 and G3 | `eval/` | W16's "Done when" covers every folder; M2 must not edit `eval/` except `eval/baseline.py` |
| **M1** | Your part of W16: check the resource wording `evidence/` puts in reports (`FIXED_LIMITATIONS`, `report_fields`) against ledger G3. A search by M2 found no "cause" or "mechanism" in `evidence/extract.py`, so this may need no change — your call | `evidence/` | Same reason |

## Changes, newest first

### W22 job 4 — diagnose on a disposable copy (2026-11-14) · built

**What changed for you:** by default (`--workspace copy`) the command now copies the project to a
temporary folder, builds and runs everything there — including **M1's evidence extraction**, which
now reads the copy's `target/` — and deletes the copy afterwards. The project folder is no longer
written to, not even `target/`. `source_integrity.details` now has two parts:
`"copy: …; original project: …"`; the schema field is unchanged. `--workspace in-place` gives the
old behaviour. **M3:** the reports you regenerate in W19 will carry the two-part details text.
In the UI, each job's copy now lives in the job's own folder (`--copy-parent`) and is removed
even when the job times out. A multi-module child module may need `--workspace in-place` (its
parent `pom.xml` is outside the copied folder); the error message says so.
**M1:** while running the lifecycle control (job 3 steps), also run step 4 once more and check
that `fixtures/od-fixture` gained no new files — or better, run it on a fresh copy of the fixture
without `target/` and confirm `target/` is still absent afterwards.


### W22 job 3 — class-grouped execution and the lifecycle control (2026-11-14) · built, awaiting M1

**What changed for you:** a new option, `--lifecycle class-grouped`. With it, consecutive tests of
the same JUnit 4 class run as one JUnit request, so `@BeforeClass`/`@AfterClass` run once per
block, as under Maven Surefire. The default is still `per-method` (the Mid behaviour). Nothing in
`evidence/` or `eval/` changed; the result format is the same. The record header's `lifecycle`
now says which mode ran.

**M1 — the control run, step by step** (do each step, write down what you see):

1. `git fetch` then `git checkout m2/w22-record-env` (or `main` once it is merged).
2. Surefire, the normal Maven run:
   `mvn -B -q -f runner/tests/resources/lifecycle-control/pom.xml test`
   Expected: exit code 0. Open
   `runner/tests/resources/lifecycle-control/target/surefire-reports/TEST-LifecycleControlTest.xml`:
   `tests="2" failures="0"`.
3. FlakeTrace's harness, both modes:
   `py -m unittest -v runner.tests.test_order_runner.TestLifecycleControl`
   Expected: 3 tests OK. They assert that `per-method` makes `second` fail with
   `expected:<1> but was:<2>` (class setup ran twice) and that `class-grouped` passes both.
4. The real command on fixture F1 in the new mode:
   `py -m runner diagnose --project fixtures/od-fixture --victim odfixture.ConfigVictimTest#expectsDefaultMode --lifecycle class-grouped --records %TEMP%\ft-records`
   Expected: `VERIFIED (sequence)` with polluter `odfixture.ConfigPolluterTest#pollute`.
5. Write in `docs/evidence-m1.md`: date, your JDK (`java -version`), each command, what it printed,
   the three-row table (Surefire / per-method / class-grouped), and **anything unclear in these
   steps**. Tell M2; M2 then flips the default in a one-line commit.


### W22 job 2 — JUnit spike result (2026-11-14) · findings only

JUnit 4 classes can run as one request filtered and sorted to any order, with `@BeforeClass` once;
JUnit 3 classes cannot be sorted that way and stay one test per request. Today's harness runs
`@BeforeClass` once per test — measured on the control class. **M1:** this is the behaviour your
W22 control run (ADR-012 §3) will compare against Surefire. Details in ADR-012 §2.


### W22 job 1 — the record header says what the runs ran under (2026-11-14) · built

**What changed for you:** every execution record's first line gains `tool_commit`, `tool_dirty`,
`maven_version`, `python_version`, `jvm` (the test JVM's `java.version`, `timezone`, `locale`,
`file.encoding`, `junit.version`), `lifecycle`, `workspace`, `container_image` and `command`.
Nothing was removed. **M3:** these are the values ADR-013's manifest `environment` needs for
`verify-bundle` and `replay` (W23). They hold absolute paths (`project`, `command`) that the bundle
export must redact.

**To look at it:** run any diagnosis and read the first line of the `.jsonl` record.


### W18 — the runner counts every phase as a tally (2026-11-14) · built, awaiting M1

**What changed for you:**

| | Before | After |
| --- | --- | --- |
| `DiagnosisRuns` | `alone_n`, `alone_successes`, `sequence_n`, `sequence_successes`, `sequence_any_failures` | **same fields, same values**, plus `alone_tally` and `sequence_tally` (`RunTally`). The old fields are now filled from the tallies |
| Status for "seen once, never again" | `NO_SINGLE_POLLUTER` | `INCONSISTENT`. `NO_SINGLE_POLLUTER` still imports and equals `"INCONSISTENT"` |
| `runner.verify.repeat()` | `(matching, any)` | a `RunTally` |

No `eval/` file changed; your 99 tests pass as they are. **M3:** `eval/report.py` still raises
`UnhandledStatus` for `INCONSISTENT`, so the command still exits 3 — W19 gives it a report.
**Names:** `alone_tally` / `sequence_tally`, not ADR-010's `alone` / `sequence`, because
`sequence` is already the test list (note in ADR-010).

**What it does not fix yet:** in T1 the runner still names P, and `decide()` still says `VERIFIED`,
because it reads `alone_successes` (0). The tallies now hold what `decide()` needs (W19).

**To verify (M1):**

```
git fetch && git checkout m2/w18-tallies
py -m unittest -v runner.tests.test_diagnose.TestTallies runner.tests.test_search.TestRepeat
py -m unittest eval.tests.test_report
```

Expected: 9 tests OK (T1–T4 and the tally checks), then M3's report tests OK unchanged. To see the
defect the tallies expose, `git checkout d1e4d4f -- runner` in a scratch clone and run the first
command: the `TestTallies` tests fail. Record both runs in [[evidence-m1]], with anything unclear.


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
