# evidence/ — resource evidence (Member 1)

**Owner:** Member 1 · **State:** Phases 2–6 done and ADR-006 implemented (2026-10-10): lifecycle attribution, call depth 1–5 (default 2), single-test mode, polluter→victim edges with pair-mode auto-deepening, validated against the fixture's ground truth and real fastjson. W25 (2026-11-20): `rank_candidates` orders candidate polluters by static evidence, with a per-test cache. Built and tested on M1's own classes only, and not yet measured on any case.

Reports the resources a polluter may write and a victim may read, from **compiled bytecode
only**: a **static overlap — a possible mechanism, not confirmed as the cause** (claims ledger G3).
It reads `.class` files with `javap` and writes nothing into the analysed project; it needs no
application logs.
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
| `tests/resources/ft005-controls/` | Two FT005 controls (W21): write-then-restore, and unrelated overlap. Expected results in its `EXPECTED.md`, written before the first run |
| `tools/measure_depth.py` | Measures accesses, unsupported observations, javap calls and time per depth |
| `javap-dumps/` | Saved `javap` output used as evidence in docs |

## Run it

Needs Python 3 and a JDK 8+ (`javap` on `PATH`, or set `FLAKETRACE_JAVAP` to another javap).

```bash
# polluter -> victim: resources the polluter writes and the victim reads
python3 -m evidence.extract --classes fixtures/od-fixture/target/classes \
    --test-classes fixtures/od-fixture/target/test-classes \
    --polluter odfixture.FeaturePolluterTest#enableTurbo \
    --victim odfixture.FeatureVictimTest#expectsTurboDisabled
# pair mode starts at --depth (default 2) and goes one level deeper, up to 5, only while it finds
# no edge and a walk was cut off; the pair records depth_requested and depth_used (ADR-006).
# --no-deepen analyses at exactly --depth.

# one test method (default --depth 2; 1-5 accepted; never deepens)
python3 -m evidence.extract --classes fixtures/od-fixture/target/classes \
    --test-classes fixtures/od-fixture/target/test-classes \
    --test odfixture.FeatureVictimTest#expectsTurboDisabled

# tests: compile the self-test classes and the fixture once, then run
mvn -B -q -f evidence/tests/resources/m1-selftest/pom.xml test-compile
mvn -B -q -f evidence/tests/resources/ft005-controls/pom.xml test-compile
mvn -B -q -f fixtures/od-fixture/pom.xml test-compile
python3 -m unittest evidence.tests.test_extract -v
# in CI: fail instead of skipping when classes or javap are missing
FLAKETRACE_REQUIRE_JVM=1 python3 -m unittest evidence.tests.test_extract -v

# what each depth adds on a compiled project
python3 -m evidence.tools.measure_depth --classes fixtures/od-fixture/target/classes \
    --test-classes fixtures/od-fixture/target/test-classes
```

An empty edge list comes with `no_supported_resource_evidence: true`. That means no *supported*
static evidence was found, not that the tests are independent. `extract.report_fields(pair)` gives
the three fields of Member 3's report (`shared_resource`, `polluter_write_location`,
`victim_read_location`) as the contract's projection defines, plus `resource_edges`: every edge
in the contract's order, each with its first write and read location and its depth (W21, ADR-010).
Every edge is a static overlap, not a confirmed cause. In-process callers use
`extract.analyse_pair(project, polluter_id, victim_id)` to get the pair with deepening.

**Ranking (W25, ADR-014 §5).** `extract.rank_candidates(project, victim, candidates, depth=2,
cache=None)` returns one `RankedCandidate(test, score, reasons, note)` per candidate, ordered by
a fixed rule with no weights:
1. the most resources the candidate writes and the victim reads;
2. then the shallowest such edge;
3. then the original position.

`score` is `(resources shared, shallowest depth or None, original position)`; `reasons` are the
edges in `resource_edges` form. With no evidence the order is unchanged. No candidate is ever
dropped: one that cannot be analysed is kept and its `note` says why. An `AnalysisCache` analyses
each test once per depth, so N candidates cost N + 1 analyses; its `analysed` and `seconds` fields
feed the budget's `analysis_seconds`. Ranking orders the search; it never says what caused a
failure. This function does not deepen: when to deepen is the planner's decision (ADR-014 §6,
Member 2).

Depth follows calls into the project's own classes only (never the JDK or other jars),
breadth-first, each method once per root. A virtual call follows only the method it names;
an override in a subclass is reported as `VIRTUAL_DISPATCH`, not guessed.

