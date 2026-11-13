# ADR-013 — Evidence bundle: a report that travels with its record, a recount and a replay

**Date:** 2026-11-13 · **Status:** `ACCEPTED` by M1, M2 and M3 on 2026-11-13 (in person; PR #101) ·
**Owner:** M3 (bundle format, recount checker) with M2 (capture, replay command) ·
**Verifier:** M1 (reproduces a bundle on her own machine) ·
**Closes:** FT009, and gives FT020 its handover exercise · **Work package:** W23 ·
**Builds on:** [[03-Design/decisions/ADR-004-w7-diagnosis-runs]],
[[03-Design/decisions/ADR-010-verdict-contract-v2]]

## Context

Each of the seven committed reports in `eval/reports/` has an `execution_record_reference` that
is an absolute path on the machine that produced it. The JSON-lines records are not committed. A
reader can see the summary and cannot audit one run behind it.

[[03-Design/certificate-contract]] promised more: a **witness** that a third party can check
without trusting the tool, an **exact replay command**, and an evidence bundle (FR-6). None of the
three exists yet.

## Decision

### 1. A bundle is a folder with five files

```
<case>-<utc-timestamp>/
  manifest.json     identity, environment, command, checksums
  report.json       the diagnosis report (schema v2)
  record.jsonl      every JVM run, one line each
  replay.md         the exact commands to run it again
  environment.txt   output of `java -version` and `mvn -v`
```

`manifest.json`:

| Field | Content |
| --- | --- |
| `bundle_version` | `1` |
| `tool` | FlakeTrace git commit, dirty flag |
| `subject` | repository URL or `fixture`, commit, dirty flag, module path |
| `victim`, `command` | The test diagnosed and the full command line |
| `parameters` | `n`, shuffles, seed, budget, policy, lifecycle mode, workspace mode |
| `environment` | OS, JDK, Maven, JUnit, Python, timezone, locale, encoding, container digest or `null` |
| `reset_assumptions` | The contract sentence from ADR-012 section 1 |
| `fresh_run` | `true`, with the date — these are new runs, not the Mid's measurements |
| `files` | SHA-256 of the other four files |

Inside a bundle every path is **relative**: `execution_record_reference` is `record.jsonl`, the
project folder is written `<project>`. User names and home paths are replaced before export; this
is the first use of the redaction rule we committed to.

### 2. `verify-bundle` — an independent recount

```
python -m eval.bundle verify <bundle-folder>
```

It reads **only the bundle**, never the runner's state:

1. Every checksum in the manifest matches.
2. `report.json` validates against the schema.
3. **Recount.** From `record.jsonl` alone it recomputes every tally in the report — the reference
   signature from the first real failure, then alone, sequence and each deletion check from the
   lines labelled with those steps — and compares them with the report's numbers.
4. **Re-decide.** It feeds the recounted tallies to `decide()` and compares the outcome.

Any difference is printed and the command exits non-zero.

This is the certificate idea made concrete: the report is the output, the record is the witness,
and `verify-bundle` is the checker. It also means a wrong count in the runner cannot hide — the
kind of error FT003 was.

For the recount to work, every record line already has what is needed (step, order, each test's
outcome and signature). One addition: deletion runs carry the removed test (ADR-011).

### 3. `replay` — run it again somewhere else

```
python -m runner replay <bundle-folder> --project <checkout of the subject at the recorded commit>
```

It re-runs the kept sequence, the victim alone and the deletion checks with the recorded `n`, in
the recorded lifecycle mode, writes a new bundle, and prints a comparison:

```
verdict:     VERIFIED  ->  VERIFIED          same
sequence:    20/20 matched  ->  20/20 matched
alone:       20/20 passed   ->  20/20 passed
environment: JDK 1.8.0_502 -> 1.8.0_452      DIFFERENT (noted)
```

The tolerance is the verdict class and the claims of ADR-010, not identical counts: 20/20 and
19/20 are the same claim.

### 4. Where bundles live

| Bundle | Where |
| --- | --- |
| Fixture cases (small) | `eval/bundles/<case>/`, committed. They replace the path-bound `eval/reports/*.json` |
| Real-project runs | Committed if small (under about 1 MB); otherwise a zip attached to a GitHub release, with its checksum in `eval/bundles/README.md` |

Third-party source is never in a bundle — only our records, reports and manifests.

### 5. The peer-reproduction record

Closing FT009 needs a person, not a script. For one fixture bundle and, later, the real case:

| | |
| --- | --- |
| Who | Member 1, on her own machine, without Member 2 or 3 at the keyboard |
| Steps | Clone at the recorded tool commit · `verify-bundle` · `replay` |
| Record | `docs/evidence-m1.md`: date, machine, JDK, both commands' output, every difference, every step that was unclear |
| If it fails | The failure is the finding. It is recorded and the instructions are fixed, not explained away |

The same exercise is FT020's handover: a member who did not build the pipeline runs it end to end
from the written instructions alone.

## Tests

| Test | Expected |
| --- | --- |
| Verify a freshly made fixture bundle | exit 0 |
| Change one count in `report.json` | recount mismatch, exit non-zero |
| Change one byte of `record.jsonl` | checksum mismatch, exit non-zero |
| Delete one `alone` line from the record (and fix the checksum) | recount mismatch |
| A bundle made on Windows verified on Linux | exit 0 — no absolute paths, LF line endings |

## Consequences

- `execution_record_reference` becomes a relative path in bundled reports. The schema field stays
  a string, so this is not a schema change.
- `eval/reports/README.md` and the report's evidence section are updated to point at bundles.
- The UI reads reports from the records folder today and is unaffected; reading bundles is a
  later option.

## Agreement

| Member | Agree? | Comment |
| --- | --- | --- |
| M1 | ☑ | Agreed in person 2026-11-13, recorded by M2; confirmed by approving PR #101 |
| M2 | ☑ | Agreed 2026-11-13 in person with M1 and M3; recorded their agreement in PR #101 |
| M3 | ☑ | Agreed in person 2026-11-13, recorded by M2; confirmed by approving PR #101 |
