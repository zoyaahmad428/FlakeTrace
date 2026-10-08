# Benchmark run logs

Empty by design. This directory is where a real run of Member 2's pipeline
against a case from `eval/benchmark/manifest.json` writes `<case_id>.json`,
one per case. `eval/benchmark/yield_report.py` reads whatever is here (and
only here) to produce the yield report — it never hand-types a count.

**No file in this directory yet means no case has actually been run.** The
yield report must show `not_yet_run` for every case rather than invent a
number, and today it does, because this directory is empty.

## Expected shape of `<case_id>.json`

```json
{
  "case_id": "F1",
  "built": true,
  "victim_passes_alone": true,
  "reproduced": true,
  "excluded_reason": null
}
```

Each of `built`, `victim_passes_alone`, `reproduced` is one of:

- `true` — that stage ran and succeeded.
- `false` — that stage ran and failed (the case is excluded at this stage;
  `excluded_reason` should explain why, e.g. `"build failed"` or
  `"VICTIM_FAILS_ALONE"`).
- `null` / absent — that stage was never reached (e.g. the build failed, so
  `victim_passes_alone` and `reproduced` are both `null`).

The funnel is strictly sequential: `built` must be resolved before
`victim_passes_alone` is meaningful, which must be resolved before
`reproduced` is. `yield_report.py` does not enforce this ordering itself (it
just reads whatever is there), so whatever writes these files is
responsible for keeping it consistent.
