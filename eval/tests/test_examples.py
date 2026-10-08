import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from eval.outcome import DecisionInput, decide
from eval.schema_validator import validate_report

EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "examples"

# For each example file: the DecisionInput kwargs that should reproduce its
# outcome/unresolved_reason via eval.outcome.decide(). Keeps the hand-written
# JSON honest against the actual decision function.
EXPECTED_INPUTS = {
    "example_f1_verified.json": dict(
        source_integrity_passed=True,
        isolation_successes=0, isolation_n=20,
        sequence_successes=20, sequence_n=20, sequence_failures_any=20,
        resource_edge_exists=True,
    ),
    "example_f3_candidate.json": dict(
        source_integrity_passed=True,
        isolation_successes=0, isolation_n=20,
        sequence_successes=12, sequence_n=20, sequence_failures_any=12,
        resource_edge_exists=True,
    ),
    "example_victim_fails_alone.json": dict(
        source_integrity_passed=True,
        isolation_successes=20, isolation_n=20,
        sequence_successes=20, sequence_n=20, sequence_failures_any=20,
        resource_edge_exists=False,
    ),
    "example_not_reproduced.json": dict(
        source_integrity_passed=True,
        isolation_successes=0, isolation_n=20,
        sequence_successes=0, sequence_n=20, sequence_failures_any=0,
        resource_edge_exists=True,
    ),
    "example_signature_mismatch.json": dict(
        source_integrity_passed=True,
        isolation_successes=0, isolation_n=20,
        sequence_successes=0, sequence_n=20, sequence_failures_any=5,
        resource_edge_exists=True,
    ),
    "example_no_resource_evidence.json": dict(
        source_integrity_passed=True,
        isolation_successes=0, isolation_n=20,
        sequence_successes=18, sequence_n=20, sequence_failures_any=18,
        resource_edge_exists=False,
    ),
    "example_source_integrity_failed.json": dict(
        source_integrity_passed=False,
        isolation_successes=0, isolation_n=20,
        sequence_successes=20, sequence_n=20, sequence_failures_any=20,
        resource_edge_exists=True,
    ),
}


class TestExamples(unittest.TestCase):
    def test_every_schema_row_has_an_example(self):
        example_files = {p.name for p in EXAMPLES_DIR.glob("*.json")}
        self.assertEqual(example_files, set(EXPECTED_INPUTS.keys()))

    def test_examples_validate_against_schema(self):
        for filename in EXPECTED_INPUTS:
            with self.subTest(filename=filename):
                with open(EXAMPLES_DIR / filename, encoding="utf-8") as f:
                    report = json.load(f)
                validate_report(report)  # must not raise

    def test_examples_match_decide_output(self):
        for filename, kwargs in EXPECTED_INPUTS.items():
            with self.subTest(filename=filename):
                with open(EXAMPLES_DIR / filename, encoding="utf-8") as f:
                    report = json.load(f)
                decision = decide(DecisionInput(**kwargs))
                self.assertEqual(
                    decision.outcome, report["outcome"],
                    f"{filename}: decide() gave {decision.outcome}, file says {report['outcome']}",
                )
                self.assertEqual(
                    decision.unresolved_reason, report["unresolved_reason"],
                    f"{filename}: decide() gave reason {decision.unresolved_reason}, "
                    f"file says {report['unresolved_reason']}",
                )

    def test_examples_wilson_numbers_match_the_formula(self):
        for filename, kwargs in EXPECTED_INPUTS.items():
            with self.subTest(filename=filename):
                with open(EXAMPLES_DIR / filename, encoding="utf-8") as f:
                    report = json.load(f)
                decision = decide(DecisionInput(**kwargs))
                self.assertAlmostEqual(report["reproduction"]["lower"], decision.sequence_interval[0], places=9)
                self.assertAlmostEqual(report["reproduction"]["upper"], decision.sequence_interval[1], places=9)
                self.assertAlmostEqual(report["victim_alone"]["lower"], decision.isolation_interval[0], places=9)
                self.assertAlmostEqual(report["victim_alone"]["upper"], decision.isolation_interval[1], places=9)


if __name__ == "__main__":
    unittest.main()
