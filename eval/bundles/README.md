# Evidence bundles (W23, ADR-013)

A bundle is a folder with five files that travel together, so a report can be checked by
someone who was not there and has no access to the machine that produced it:

| File | What |
| --- | --- |
| `manifest.json` | Identity, environment, command, parameters, checksums of the other four files |
| `report.json` | The diagnosis report (schema v2), with `execution_record_reference` rewritten to the relative `record.jsonl` |
| `record.jsonl` | Every JVM run, one line each — the witness `report.json` is built from |
| `replay.md` | The exact command that produced it, reconstructed from the record's own header when the CLI's argv was not recorded |
| `environment.txt` | The environment captured in the record header (today: the `java -version`/`mvn -v` summary lines the runner already extracts, not the full raw banner — see `eval/bundle.py`'s `_environment_txt` docstring for why) |

Every path inside a bundle is relative or a placeholder (`<project>`, `<home>`) — this is the
first use of the redaction rule the team committed to (ADR-013 section 1). Fixes a real,
already-documented limitation: `eval/reports/*.json`'s `execution_record_reference` was an
absolute, machine-specific path (see `eval/reports/README.md`'s "Known limitation").

## Making and checking a bundle

```
py -m eval.bundle create <report.json> <record.jsonl> --out eval/bundles
py -m eval.bundle verify eval/bundles/<case>-<timestamp>
```

`verify` reads **only the bundle** (ADR-013 section 2): it checks every checksum, validates
`report.json` against the schema, then **recounts every tally in the report from `record.jsonl`
alone** — the reference signature, the alone tally, the sequence tally and each deletion
check — and **re-decides** with `eval.outcome.decide()`, comparing the outcome too. Any
difference is printed and the command exits non-zero. This is the certificate idea made
concrete: the report is the output, the record is the witness, `verify-bundle` is the checker,
and a wrong count in the runner cannot hide behind a correct-looking summary.

## What's here so far

| Bundle | Case | Real result | How it was made |
| --- | --- | --- | --- |
| `odfixture.ConfigVictimTest#expectsDefaultMode-20261120T193202Z/` | F1 | `VERIFIED` (20/20 reproduced, 0/20 alone) | `python -m runner diagnose --project fixtures/od-fixture --victim odfixture.ConfigVictimTest#expectsDefaultMode`, real JDK 8/Maven, then `python -m eval.bundle create`. Verified clean: `python -m eval.bundle verify` exits 0. Also used to confirm the recount independently catches a tamper: changing `reproduction.matched` in a copy was caught by both the checksum and the recount |

**Not yet done** (ADR-013's own "Consequences" list): F2–F4 and N1–N4 are not bundled yet, and
`eval/reports/*.json` has not been replaced — those are the next step, not part of W23's own
"done when" (ADR-013's tests, and one independent reproduction recorded in `docs/evidence-m1.md`).
`python -m runner replay` (ADR-013 section 3, M2's) does not exist yet; `replay.md` inside each
bundle names the manual command in the meantime.

## Recount coverage

`eval/bundle.py`'s module docstring states exactly which report shapes the recount covers today
(POLLUTER_FOUND/CANDIDATE/VERIFIED, VICTIM_FAILS_ALONE/_DIFFERENTLY, NOT_REPRODUCED with no
reference ever established) and which it does not yet (INCONSISTENT, BUDGET_EXHAUSTED) —
`verify_bundle` says so explicitly for those rather than guessing at a number.
