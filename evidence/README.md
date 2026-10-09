# evidence/ — resource evidence (Member 1)

**Owner:** Member 1 · **State:** Phase 2 done: depth-1 extraction with lifecycle attribution, single-test mode (2026-10-09). Depth 2/3 (Phase 3) and polluter→victim edges (Phase 4) not yet built.

Finds the shared resource a polluter writes and a victim reads, from **compiled bytecode
only** — the target project's source is never modified and no application logs are needed.
Contract: [docs/contracts/interfaces.md](../docs/contracts/interfaces.md) (Interface 2) and
[docs/contracts/resource-evidence.md](../docs/contracts/resource-evidence.md) (output format, invocation).

## Iteration 1 scope

| Resource kind | Bytecode signal | Fixture case |
| --- | --- | --- |
| `static-field` | `putstatic` in polluter, `getstatic` in victim (incl. through called methods, `setUp`, `<clinit>`) | F1 (`Config.mode`), F3 (`Toggles.flagA/flagB`) |
| `system-property` | `System.setProperty(key, …)` in polluter, `System.getProperty(key)` in victim | F2 (`odfixture.turbo`) |

Out of Iteration 1: filesystem paths (Iteration 2), runtime instrumentation (see
[ADR-001](../docs/03-Design/decisions/ADR-001-iteration1-evidence-without-instrumentation.md)).

The POC's `extract_static.py` (javap-based getstatic/putstatic extraction with bytecode offsets)
is the reference idea; per the vault, the code itself does not carry over. `extract.py` is
written fresh ([ADR-002](../docs/03-Design/decisions/ADR-002-evidence-extractor-implementation.md)).

## Files

| File | What |
| --- | --- |
| `extract.py` | The extractor: runs `javap -v -p -c`, parses classes, finds the test's lifecycle roots, scans them |
| `tests/test_extract.py` | Unit tests (standard-library `unittest`) |
| `tests/resources/m1-selftest/` | Member 1's own test input classes (a tiny Maven project), **not** a project fixture |
| `javap-dumps/` | Saved `javap` output used as evidence in docs |

## Run it

Needs Python 3 and a JDK 8+ (`javap` on `PATH`, or set `FLAKETRACE_JAVAP` to another javap).

```bash
# one test method, depth 1 (the only depth implemented so far)
python3 -m evidence.extract --classes fixtures/od-fixture/target/classes \
    --test-classes fixtures/od-fixture/target/test-classes \
    --test odfixture.ConfigPolluterTest#pollute --depth 1

# tests: compile the self-test classes once, then run
mvn -B -q -f evidence/tests/resources/m1-selftest/pom.xml test-compile
python3 -m unittest evidence.tests.test_extract -v
```

Without `--depth 1` the command currently exits with code 2: the contract default is 2,
and depth 2 arrives in Phase 3.

