# eval — Member 3 (Evaluation & Repair)

Dependency-free Python unless noted. `pip install -r eval/requirements.txt`
for the schema validator's `jsonschema` dependency.

| Module | Purpose |
| --- | --- |
| `stats.py` | Wilson score confidence intervals; `compare_sequence_to_isolation`. |
| `schema/report.schema.json` | The diagnosis report contract (see `docs/contracts/report-schema.md`). |
| `outcome.py` | `decide()` — the VERIFIED/CANDIDATE/UNRESOLVED decision table. |
| `schema_validator.py` | Validates a report dict/file against the schema. |
| `baseline.py` | Random-order baseline — **see status below.** |
| `examples/` | Hand-written example reports, one per decision-table row. Not results. |
| `tests/` | Unit tests for everything above. |

Run everything: `python3 -m unittest discover -s eval/tests -v`

## Random-order baseline status: NOT YET RUN ON REAL TESTS

`baseline.py` defines the `OrderRunner` interface Member 2's real Docker
builder / single-JVM order runner must implement (`run_ordered(order) ->
{test: outcome}`), and `run_random_order_baseline()` is built entirely
against that interface. **No implementation of `OrderRunner` exists in this
repo yet** — Member 2's runner is a separate, not-yet-built component.

Consequently this baseline:

- Has been unit-tested with `eval/tests/fake_runner.py`'s `FakeOrderRunner`
  — a scriptable fake that never launches a JVM or runs real Maven/JUnit.
  That fake lives **only** under `eval/tests/`; `baseline.py` does not
  import it, and no real CLI should ever import it either.
- Has **never been executed against `fixtures/od-fixture` or any other real
  project.** Any number you might expect to see here (e.g. "it took N
  random shuffles to reproduce F1") does not exist yet and must not be
  invented. Once Member 2's order runner is integrated, this baseline can
  be run for real and its results feed into Phase 5's yield report.
