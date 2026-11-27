# Handover from M2 to M1 and M3 — Iteration 2

*Kept current by M2 at every hand-over. Newest first. A package marked "built" is **not** closed:
it closes only when its verifier has reproduced it ([[10-Final1/iteration-2-plan]]).*

## Waiting on you

*Replaced 2026-11-27 (M2) after the supervisor's 23 Nov review
([[10-Final1/supervisor-review-2026-11-23]]). The earlier items here (W16, W18, W19, W22
verifications) are done and recorded in [[evidence-m1]] and [[evidence-m3]]. Work in this order;
no calendar slots; the Final is tentatively 4 December.*

| For | What | Where | Why it matters |
| --- | --- | --- | --- |
| **M3** | **W37 first:** correct "five distinct" to **four** distinct adopted polluters (`SerializeWriterTest_14#test_writer_1/2/3`, `SerializeWriterTest_15#test_writer_1`; M2 recounted from the seven bundles 2026-11-27) and "certified polluter" to `CANDIDATE` in **your** files; name the scan's six relevant tests as a separate number; keep order mode's 12,817 separate. The claims ledger (E16, G9) is already corrected in this change | [[05-Testing/real-case-protocol]] (lines ~140–145), [[evidence-m3]] (append a dated correction, do not rewrite history), the result table | FT008/FT017; the supervisor named this exact mismatch |
| **M3** | **W36:** the bundle version matrix — every committed bundle, its schema version, the checker commit that verifies it, expected vs actual, plus the malformed and tampered controls. Ask M2 for the replay column | [[evidence-m3]], `eval/bundle.py`, `eval/schema_validator.py` | FT009, his Priority 1. Never write "all bundles verify" without naming the checker |
| **M3** | W40 (A5): a scenario table — scenario kind → case → verdict → bundle, from F1–F4, N1–N4, the two FT005 controls and FJ-03 (order and pair mode) | a new section in [[evidence-m3]] or `eval/README.md` | Panel action A5 |
| **M3** | W29a: deliver the corrected, editable worksheet (FT015) to the supervisor and record the date | — | FT015 stays open until it is delivered |
| **M1** | **W32 (FT018):** contact one Java/Maven/JUnit practitioner today; hold the session, or record every attempt and the blocker so the supervisor can agree a substitute | [[10-Final1/practitioner-check]] | His Priority 4; nothing has been attempted yet |
| **M1** | **W36 check:** once M3's matrix is in, re-run your bundle reproduction **alone**, using only the fixed README, on a current (schema v3) bundle; record what was unclear, or "none" | [[evidence-m1]] | Closes your FT009 repeat |
| **M1** | W37: check M3's FJ-03 wording — why there is no static edge (JDK `ThreadLocal.set`), and why no edge is not proof of independence | [[05-Testing/real-case-protocol]] | You own the resource interpretation |
| **M1** | W30 poster and W29b clipped worksheet table — ask the supervisor for the poster date if it is not known | — | Both still unsupplied |
| **M1, M3** | W40 (A6): each write a short note on the nearest existing tool to your own part and how FlakeTrace differs; cite only sources you opened | your own evidence log, then report v2 | Panel action A6; the oral will ask |
| **All** | W38: your chapters of report v2.0, against the current build; M2 sets up the skeleton and compiles | `mid-eval-report/`, [[10-Final1/report-v2-plan]] | Not yet started; the report is assessed separately from the demo |
| **M1, M3** | Review M2's PR #177 (the web UI for the Final demo): M3 checks the committed-evidence table reads your seven FJ-03 runs; M1 checks the runtime-evidence label matches her §3a | PR #177 | The demo runs from it |

## Changes, newest first

### After M1's verification (PR #108) and M3's PR #109 (2026-11-20) · built

**M1:** thank you — your four notes are done. (1) `class-grouped` is now the **default** lifecycle
(CLI, `diagnose()`, `OrderRunner`); `--lifecycle per-method` gives the Mid behaviour. (2) The README
already said Python 3.11+; it now also says 3.10 is the floor (`jsonschema==4.26.0` requires `>=3.10`)
and that 3.9 fails, and CLAUDE.md §8 says it too. (3) The README now says the first run downloads
Maven plugins that `-q` hides, with a pre-fetch command (run once here: `BUILD SUCCESS`). (4) The
W18 "before" step above now restores only the three code files.
**M3:** (1) the UI test now reads N2's rate from `n2.json` (N2 is random by design), so your
regenerated report no longer breaks it; deterministic cases stay hard-coded; checked against both
versions of `n2.json`. (2) Claims-ledger row E14 now says F3 is `CANDIDATE` until W20 and drops
"1-minimal" (G2). (3) The `setup-java` tar error on #109 is a GitHub-side flake — "Re-run failed
jobs". Still yours: merge `main` into #109 (two doc tables, `genai-register.md` and `members.md`).


### A1 — discovery reads the project's own Surefire includes (2026-11-20) · built

**M3: W26a steps 6–9 are unblocked** once this merges. Discovery now selects test classes with the
project's effective Surefire `includes`/`excludes` (from `help:effective-pom`, in the same Maven
call that builds the classpath), falling back to Surefire's defaults only when the project sets
none. On fastjson's real configuration (`e05e9c5`) it selects 2,106 test classes including
`SerializeWriterTest_14`; the old rule missed it. Not run here: the full `discover_order` on a
compiled fastjson (needs your JDK 8) — please make it the first check of step 6 and record it.
Projects using `-Dtest`, `includesFile`, `excludesFile` or `groups` are refused with a clear error.


### PR #106 made mergeable, and the CI line for PR #107 (2026-11-19, M2 with M3's permission)

**M3:** on your branch `m3/w19-verdict-contract-v2` M2 merged `main` (two doc tables), and changed
your `eval/report.py` in two places you allowed: (1) `resource_edges` now comes from M1's
`report_fields` (every edge, with an optional `depth`, added to `resourceEdge` in the schema — a
5-line diff), and the "extractor reports one edge" limitation is gone; (2) the deletion status:
one polluter passing alone → `DELETION_VERIFIED` (ADR-011 §2), two or more → `INCOMPLETE` →
`CANDIDATE [DELETION_EVIDENCE_INCOMPLETE]` until W20. So **F3 is `CANDIDATE` now**; its ground truth
stays `VERIFIED` as W20's target. The eight reports were regenerated with your tool. Please read the
diff of `eval/report.py`, the schema and the reports before approving.
**M1:** your #107 failed CI only because `ci.yml` did not compile `ft005-controls`; the line is on
#106 (guarded, so it works before and after #107). Once #106 merges, re-run #107's checks. Reports
now list every edge you return. Both of you: #106 changes a contract (schema) — **both M1 and M2
must approve**, per CONTRIBUTING.


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
defect the tallies expose, in a scratch worktree of the W18 commit restore **only the three code
files** W18 changed — `git checkout d1e4d4f -- runner/diagnose.py runner/verify.py runner/cli.py`
(restoring all of `runner/` would also bring back the old tests) — and run the first command: the
`TestTallies` tests fail. Record both runs in [[evidence-m1]], with anything unclear. *(Corrected
2026-11-20 after M1's verification, PR #108.)*


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
