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

**Two F1 bundles, kept deliberately, not a duplicate to clean up.** M2 asked whether to keep
both or remove the dirty one; decided (M3, 2026-11-21) to keep both: they are the same case
reproducing the same verdict under two different environments (JDK 8/working-copy vs.
JDK 21/clean checkout), which is a genuine cross-check, not noise -- `tool.dirty` is accurate,
transparently-reported metadata about which one ran, not a defect to hide. The clean one is the
W32 practitioner case (M2's choice, below).

| Bundle | Case | Real result | How it was made |
| --- | --- | --- | --- |
| `20261121T093338Z-odfixture.ConfigVictimTest#expectsDefaultMode/` | F1 | `VERIFIED` (20/20 reproduced, 0/20 alone) | Added by M2 for the W32 practitioner case: `--bundle`, from a clean checkout of `main` at `03ada56` (`tool.dirty: false`), JDK 21. `python -m runner replay` on it → `VERIFIED -> VERIFIED same`, exit 0 ([[evidence-m2]]) |
| `20261121T094724Z-odfixture.ConfigVictimTest#expectsDefaultMode/` | F1 | `VERIFIED` (20/20 reproduced, 0/20 alone) | `python -m runner diagnose --project fixtures/od-fixture --victim odfixture.ConfigVictimTest#expectsDefaultMode --bundle eval/bundles`, real JDK 8/Maven, from a working copy with uncommitted changes (`tool.dirty: true`). Verified clean: `python -m eval.bundle verify` exits 0, zero occurrences of the machine username in any of the 5 files. Also used to confirm the checker independently catches a tamper: changing `reproduction.matched` in a copy was caught immediately by `read_bundle`'s own checksum check, exit 1 |
| `20261121T152045Z-odfixture.FeatureVictimTest#expectsTurboDisabled/` | F2 | `VERIFIED` (20/20 reproduced, 0/20 alone) | Real `diagnose --bundle`, JDK 8. Verified clean |
| `20261121T152110Z-odfixture.ToggleVictimTest#expectsNotBothFlagsSet/` | F3 | `VERIFIED` (two polluters, both `NEEDED`) | Real `diagnose --bundle`, JDK 8. Verified clean |
| `20261121T152152Z-odfixture.AlwaysEarlyVictimTest#expectsLateFlagUnset/` | F4 | `VERIFIED` (found via a shuffled order, seed 6) | Real `diagnose --bundle`, JDK 8. Verified clean |
| `20261121T152241Z-odfixture.NegativeAloneFailTest#alwaysFails/` | N1 | `UNRESOLVED (VICTIM_FAILS_ALONE)` | Real `diagnose --bundle`, JDK 8. Verified clean |
| `20261121T152302Z-odfixture.NegativeFlakyTest#sometimesFails/` | N2 | `UNRESOLVED (VICTIM_FAILS_ALONE)` (13/20 this run -- intermittent by design, the rate varies run to run) | Real `diagnose --bundle`, JDK 8. Verified clean |
| `20261121T152321Z-odfixture.EnvDependentNegativeTest#onlyFailsUnderCI/` | N3 | `UNRESOLVED (NOT_REPRODUCED)` | Real `diagnose --bundle`, JDK 8. Found and fixed a real recount bug on this one (see "A real bug" below). Verified clean after the fix |
| `20261121T152513Z-odfixture.DualFailureVictimTest#expectsStateTwo/` | N4 | `UNRESOLVED (VICTIM_FAILS_ALONE_DIFFERENTLY)` | Real `diagnose --bundle`, JDK 8 (first attempt hit a transient Windows file-lock on the bundle's final rename, no partial bundle left behind, succeeded identically on retry). Verified clean |

All 9 bundles (two F1, one each of F2–F4 and N1–N4) are committed and `verify` clean. F2–F4
and N1–N4 done 2026-11-21 ([[evidence-m3]]); `eval/reports/*.json` has not been replaced yet --
not part of W23's own "done when" (ADR-013's tests, and one independent reproduction recorded
in `docs/evidence-m1.md`). M1's independent reproduction (clone, `verify`, `replay`, alone) has
not happened.

**A real bug found and fixed bundling N3**: `eval/bundle.py`'s recount, for a diagnosis where
no reference was ever established, folded "shuffle" lines into the same pool used for
`reproduction`'s fallback tally -- but `runner.diagnose._steps` itself counts only the
"reproduce" phase there (ADR-008's shuffle fallback is a separate phase). N3's real record has
20 "reproduce" lines and 31 "shuffle" lines; the recount said 51, the real report correctly
said 20. Caught by `verify` on the real bundle, not by a unit test (the existing test for this
shape happened to have no shuffle lines, so it never exercised the bug) -- a regression test
with both phases present was added before fixing it.

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
