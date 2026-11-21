# Evidence bundles (W23, ADR-013, Interface 8)

A bundle is a folder with five files that travel together, so a report can be checked by
someone who was not there and has no access to the machine that produced it. The runner writes
and replays bundles (`runner/bundle.py`, `runner/replay.py`; M2); `eval/bundle.py`'s
`verify_bundle` reads one and checks it (M3) — one writer, so the format has one owner in code.

| File | What |
| --- | --- |
| `manifest.json` | Identity, environment, command, parameters, checksums of the other four files |
| `report.json` | The diagnosis report (schema v2), with `execution_record_reference` rewritten to the relative `record.jsonl` |
| `record.jsonl` | Every JVM run, one line each — the witness `report.json` is built from |
| `replay.md` | The commands to check and re-run the bundle |
| `environment.txt` | The real output of `java -version` and `mvn -v` |

Every path inside a bundle is relative or a placeholder (`<project>`, `<records>`, `<home>`,
`<user>`) — the first use of the redaction rule the team committed to (ADR-013 section 1,
Interface 8). A bundle that would still contain the home folder or the user name as a path
component is refused outright (`runner.bundle.assert_clean`), not written with a gap. Fixes a
real, already-documented limitation: `eval/reports/*.json`'s `execution_record_reference` was
an absolute, machine-specific path (see `eval/reports/README.md`'s "Known limitation").

**Line endings.** `.gitattributes` marks `eval/bundles/**` as `-text`: Git must never turn a bundle's LF into CRLF (`core.autocrlf` on Windows), or every checksum fails. `runner/tests/test_bundle.py` reads every committed bundle back.

## Making and checking a bundle

```
python -m runner diagnose --project <project> --victim <Class#method> --bundle eval/bundles
python -m eval.bundle verify eval/bundles/<timestamp>-<victim>
python -m runner replay eval/bundles/<timestamp>-<victim> --project <checkout>
```

`verify` (M3's half) reads **only the bundle** (ADR-013 section 2, Interface 8): it checks
every checksum (`runner.bundle.read_bundle`, which refuses a bundle whose files don't match
their manifest), validates `report.json` against the schema, then **recounts every tally in
the report from `record.jsonl` alone** — the reference signature, the alone tally, the
sequence tally and each deletion check — and **re-decides** with `eval.outcome.decide()`,
comparing the outcome too. Any difference is printed and the command exits non-zero. This is
the certificate idea made concrete: the report is the output, the record is the witness,
`verify` is the checker, and a wrong count in the runner cannot hide behind a correct-looking
summary.

## What's here so far

| Bundle | Case | Real result | How it was made |
| --- | --- | --- | --- |
| `20261121T094724Z-odfixture.ConfigVictimTest#expectsDefaultMode/` | F1 | `VERIFIED` (20/20 reproduced, 0/20 alone) | `python -m runner diagnose --project fixtures/od-fixture --victim odfixture.ConfigVictimTest#expectsDefaultMode --bundle eval/bundles`, real JDK 8/Maven. Verified clean: `python -m eval.bundle verify` exits 0, zero occurrences of the machine username in any of the 5 files. Also used to confirm the checker independently catches a tamper: changing `reproduction.matched` in a copy was caught immediately by `read_bundle`'s own checksum check, exit 1 |
| `20261121T093338Z-odfixture.ConfigVictimTest#expectsDefaultMode/` | F1 | `VERIFIED` (20/20 reproduced, 0/20 alone) | Added by M2 with M3's agreement (the W32 practitioner case): the same command, from a clean checkout of `main` at `03ada56`, so `tool.dirty` is `false` (the one above was made from a working copy with uncommitted changes, `tool.dirty: true`); JDK 21. `python -m runner replay` on it → `VERIFIED -> VERIFIED same`, exit 0 |

**Not yet done**: F2–F4 and N1–N4 are not bundled yet, and `eval/reports/*.json` has not been
replaced — the next step, not part of W23's own "done when" (ADR-013's tests, and one
independent reproduction recorded in `docs/evidence-m1.md`). M1's independent reproduction
(clone, `verify`, `replay`, alone) has not happened.

## History: the format changed mid-build

A first version of `eval/bundle.py` (2026-11-20) was built straight from ADR-013, with its own
writer (`create_bundle`) and manifest shape, before the team agreed **Interface 8**
(`docs/contracts/interfaces.md`, 2026-11-21) — a more detailed, different manifest, and M2's
real writer/replay code built against it. That first version, and the bundle it committed
here, are superseded; this module now reads only `runner.bundle`'s real format. See
`docs/evidence-m3.md`'s 2026-11-21 entry for the full account, including a design mismatch
found and fixed, not just a text merge conflict.

## Recount coverage

`eval/bundle.py`'s module docstring states exactly which report/bundle shapes the recount
covers today (POLLUTER_FOUND/CANDIDATE/VERIFIED, VICTIM_FAILS_ALONE/_DIFFERENTLY,
NOT_REPRODUCED with no reference ever established, and a `kind: "replay"` bundle's own shape)
and which it does not yet (INCONSISTENT, BUDGET_EXHAUSTED) — `verify_bundle` says so explicitly
for those rather than guessing at a number.
