# FlakeTrace

**Evidence-certified diagnosis of order-dependent Java test failures.**
FYP F26-214 · FAST School of Computing, Islamabad · Stream B · three members.

When a JUnit test passes alone but fails after some other test, FlakeTrace finds the test that
polluted shared state (the *polluter*), reduces the failing order to a minimal sequence,
identifies the shared resource from compiled bytecode, and reports how reliably the failure
replays — without needing application logs and without modifying the project's source.

> **Status (2026-10-09):** proposal approved with minor modifications. Iteration 1 in progress
> towards the FYP-1 Mid Evaluation. The evaluation layer (`eval/`) and seeded fixtures
> (`fixtures/`) exist and are tested; the runner (`runner/`) and evidence extractor
> (`evidence/`) are not yet built.

## Repository layout

| Path | What | Owner |
| --- | --- | --- |
| `runner/` | Ordered single-JVM runner, polluter search, minimisation, verification, CLI | Member 2 |
| `evidence/` | Static bytecode extraction of shared-resource edges | Member 1 |
| `eval/` | Statistics, outcome decision, report schema, baselines, benchmark manifest | Member 3 |
| `fixtures/` | Seeded order-dependent Maven project with pre-registered ground truth | Member 3 |
| `docs/` | Project knowledge base — **open this folder as an Obsidian vault** | Joint |
| `POC/` | Proposal-defence proof of concept (legacy, not product code) | — |

## Start here

- New to the repo, or starting an AI session: [CLAUDE.md](CLAUDE.md)
- How we branch, commit and review: [CONTRIBUTING.md](CONTRIBUTING.md)
- How the components connect: [docs/contracts/interfaces.md](docs/contracts/interfaces.md)
- What the Mid Evaluation needs: [docs/08-MidEval/README.md](docs/08-MidEval/README.md)
- Who owns what: [docs/09-Team/members.md](docs/09-Team/members.md)

## Run the checks

```bash
pip install -r eval/requirements.txt
python3 -m unittest -v $(ls eval/tests/test_*.py | sed 's#/#.#g; s#\.py$##')
mvn -B -f fixtures/od-fixture/pom.xml test-compile
python3 -m unittest -v runner.tests.test_order_runner   # needs JDK 8+ and Maven on PATH
```

CI (`.github/workflows/ci.yml`) runs these on every pull request.
