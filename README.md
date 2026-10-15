# FlakeTrace

**Evidence-certified diagnosis of order-dependent Java test failures.**
FYP F26-214 · FAST School of Computing, Islamabad · Stream B · three members.

When a JUnit test passes alone but fails after some other test, FlakeTrace finds the test that
polluted shared state (the *polluter*), reduces the failing order to a minimal sequence,
identifies the shared resource from compiled bytecode, and reports how reliably the failure
replays — without needing application logs and without modifying the project's source.

> **Status (2026-10-11):** proposal approved with minor modifications (defence 11 September 2026).
> Iteration 1 is built for the FYP-1 Mid Evaluation: one command, `py -m runner diagnose`, runs
> the runner (`runner/`), the static evidence extractor (`evidence/`) and the outcome decision and
> report (`eval/`) on all seven seeded fixture cases (`fixtures/`). What is and is not shown live:
> [docs/08-MidEval/demo-plan.md](docs/08-MidEval/demo-plan.md).

## Repository layout

| Path | What | Owner |
| --- | --- | --- |
| `runner/` | Ordered single-JVM runner, polluter search, minimisation, verification, CLI | Member 2 |
| `evidence/` | Static bytecode extraction of shared-resource edges | Member 1 |
| `eval/` | Statistics, outcome decision, report schema, baselines, benchmark manifest | Member 3 |
| `fixtures/` | Seeded order-dependent Maven project with pre-registered ground truth | Member 3 |
| `ui/` | Web UI and its backend; runs the runner CLI and shows its reports (ADR-009) | Member 2 |
| `docs/` | Project knowledge base — **open this folder as an Obsidian vault** | Joint |
| `POC/` | Proposal-defence proof of concept (legacy, not product code) | — |

## Start here

- New to the repo, or starting an AI session: [CLAUDE.md](CLAUDE.md)
- How we branch, commit and review: [CONTRIBUTING.md](CONTRIBUTING.md)
- How the components connect: [docs/contracts/interfaces.md](docs/contracts/interfaces.md)
- What the Mid Evaluation needs: [docs/08-MidEval/README.md](docs/08-MidEval/README.md)
- Who owns what: [docs/09-Team/members.md](docs/09-Team/members.md)

## Run the checks

Needs Python 3.11+, a JDK 8 or newer (`java`, `javac`, `javap`) and Maven on `PATH`. Run from the
repository root.

Linux, macOS, WSL or Git Bash:

```bash
pip install -r eval/requirements.txt
python3 -m unittest -v $(ls eval/tests/test_*.py | sed 's#/#.#g; s#\.py$##')
mvn -B -f fixtures/od-fixture/pom.xml test-compile
python3 -m unittest -v $(ls runner/tests/test_*.py | sed 's#/#.#g; s#\.py$##')   # starts real JVMs, a few minutes
python3 -m runner diagnose --project fixtures/od-fixture --victim odfixture.ConfigVictimTest#expectsDefaultMode
mvn -B -q -f evidence/tests/resources/m1-selftest/pom.xml test-compile
python3 -m unittest -v evidence.tests.test_extract       # needs the two compiles above and javap
```

Windows (cmd or PowerShell):

```
py -m pip install -r eval/requirements.txt
py -m unittest -v eval.tests.test_baseline eval.tests.test_examples eval.tests.test_outcome eval.tests.test_report eval.tests.test_schema_validator eval.tests.test_stats eval.tests.test_yield_report
mvn -B -f fixtures/od-fixture/pom.xml test-compile
py -m unittest -v runner.tests.test_cli runner.tests.test_diagnose runner.tests.test_discovery runner.tests.test_integrity runner.tests.test_minimise runner.tests.test_order_runner runner.tests.test_orders runner.tests.test_recording runner.tests.test_search
py -m runner diagnose --project fixtures/od-fixture --victim odfixture.ConfigVictimTest#expectsDefaultMode
py -m unittest -v ui.tests.test_server
ui\start.cmd                                   # web UI on http://127.0.0.1:5174
mvn -B -q -f evidence/tests/resources/m1-selftest/pom.xml test-compile
py -m unittest -v evidence.tests.test_extract
```

CI (`.github/workflows/ci.yml`) runs the three test suites on every pull request, on Linux with
JDK 8 and Python 3.11. The `diagnose` command writes its execution record and report to
`flaketrace-records/` (git-ignored).
