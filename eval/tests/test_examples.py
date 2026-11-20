import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from eval.baseline import RunTally
from eval.outcome import DELETION_VERIFIED, DecisionInput, decide
from eval.schema_validator import validate_report

EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "examples"
LOGS_DIR = Path(__file__).resolve().parents[1] / "benchmark" / "logs"


def alone(n, passed, matched=0, other=0, infra=0):
    return RunTally(n=n, passed=passed, matched=matched, other=other, infra=infra)


def sequence(n, passed, matched=0, other=0, infra=0):
    return RunTally(n=n, passed=passed, matched=matched, other=other, infra=infra)


# For each example file: the DecisionInput kwargs that should reproduce its outcome/
# unresolved_reason via eval.outcome.decide(). Keeps the hand-written JSON honest against the
# actual decision function. Each tally's other/infra is 0 unless the filename/row needs it.
EXPECTED_INPUTS = {
    "example_f1_verified.json": dict(
        source_integrity_passed=True, reference_established=True, infrastructure_failures_anywhere=0,
        alone=alone(20, 20), sequence=sequence(20, 0, matched=20),
        resource_edge_exists=True, deletion_status=DELETION_VERIFIED,  # one kept polluter: free (ADR-011 s.2)
    ),
    "example_f3_verified.json": dict(
        source_integrity_passed=True, reference_established=True, infrastructure_failures_anywhere=0,
        alone=alone(20, 20), sequence=sequence(20, 0, matched=20),
        resource_edge_exists=True, deletion_status=DELETION_VERIFIED,  # W20: both kept polluters NEEDED, real check (ADR-011 T3)
    ),
    "example_candidate.json": dict(
        source_integrity_passed=True, reference_established=True, infrastructure_failures_anywhere=0,
        alone=alone(20, 20), sequence=sequence(20, 8, matched=12),
        resource_edge_exists=True, deletion_status=DELETION_VERIFIED,
    ),
    "example_victim_fails_alone.json": dict(
        source_integrity_passed=True, reference_established=True, infrastructure_failures_anywhere=0,
        alone=alone(20, 0, matched=20), sequence=sequence(20, 0, matched=20),
        resource_edge_exists=False,
    ),
    "example_victim_fails_alone_intermittent.json": dict(
        source_integrity_passed=True, reference_established=True, infrastructure_failures_anywhere=0,
        alone=alone(20, 8, matched=12), sequence=sequence(20, 8, matched=12),
        resource_edge_exists=False,
    ),
    "example_victim_fails_alone_differently.json": dict(
        source_integrity_passed=True, reference_established=True, infrastructure_failures_anywhere=0,
        alone=alone(20, 0, other=20), sequence=sequence(20, 0, matched=20),
        resource_edge_exists=False,
    ),
    "example_not_reproduced.json": dict(
        source_integrity_passed=True, reference_established=False, infrastructure_failures_anywhere=0,
        alone=alone(20, 20), sequence=sequence(20, 20),
        resource_edge_exists=True,
    ),
    "example_signature_mismatch.json": dict(
        source_integrity_passed=True, reference_established=True, infrastructure_failures_anywhere=0,
        alone=alone(20, 20), sequence=sequence(20, 15, other=5),
        resource_edge_exists=False,
    ),
    "example_no_resource_evidence.json": dict(
        source_integrity_passed=True, reference_established=True, infrastructure_failures_anywhere=0,
        alone=alone(20, 20), sequence=sequence(20, 1, matched=19),
        resource_edge_exists=False, deletion_status=DELETION_VERIFIED,
    ),
    "example_source_integrity_failed.json": dict(
        source_integrity_passed=False, reference_established=True, infrastructure_failures_anywhere=0,
        alone=alone(20, 20), sequence=sequence(20, 0, matched=20),
        resource_edge_exists=True,
    ),
}

# Example files whose reproduction/victim_alone counts are REAL measurements
# (eval/tools/run_real_reps.sh, 2026-10-09), cross-checked here against the
# real log file that recorded that run -- not just internally self-consistent. The real logs
# predate the ADR-010 other/infra breakdown, so this only checks the matched/n counts they do
# have (named isolation_successes/sequence_successes there -- "matched" now, same meaning).
REAL_EXAMPLE_TO_LOG_CASE = {
    "example_f1_verified.json": "F1",
    "example_f3_verified.json": "F3",
    "example_victim_fails_alone.json": "N1",
    "example_victim_fails_alone_intermittent.json": "N2",
}


class TestExamples(unittest.TestCase):
    def test_every_schema_row_has_an_example(self):
        example_files = {p.name for p in EXAMPLES_DIR.glob("*.json") if p.name != "README.md"}
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
                self.assertEqual(
                    list(decision.candidate_reasons), report["candidate_reasons"],
                    f"{filename}: decide() gave candidate_reasons {decision.candidate_reasons}, "
                    f"file says {report['candidate_reasons']}",
                )

    def test_examples_wilson_numbers_match_the_formula(self):
        for filename, kwargs in EXPECTED_INPUTS.items():
            with self.subTest(filename=filename):
                with open(EXAMPLES_DIR / filename, encoding="utf-8") as f:
                    report = json.load(f)
                decision = decide(DecisionInput(**kwargs))
                self.assertAlmostEqual(report["reproduction"]["lower"], decision.sequence_interval[0], places=9)
                self.assertAlmostEqual(report["reproduction"]["upper"], decision.sequence_interval[1], places=9)
                self.assertAlmostEqual(report["victim_alone"]["lower"], decision.alone_interval[0], places=9)
                self.assertAlmostEqual(report["victim_alone"]["upper"], decision.alone_interval[1], places=9)

    def test_real_examples_match_the_real_log_files(self):
        """The 4 examples claiming to be real measurements must match the
        raw_counts actually recorded in eval/benchmark/logs/, not just be
        internally self-consistent with EXPECTED_INPUTS above."""
        for filename, case_id in REAL_EXAMPLE_TO_LOG_CASE.items():
            with self.subTest(filename=filename, case_id=case_id):
                kwargs = EXPECTED_INPUTS[filename]
                with open(LOGS_DIR / f"{case_id}.json", encoding="utf-8") as f:
                    log = json.load(f)
                raw = log["raw_counts"]
                self.assertEqual(kwargs["alone"].matched, raw["isolation_successes"])
                self.assertEqual(kwargs["alone"].n, raw["isolation_n"])
                if "sequence_successes" in raw:
                    self.assertEqual(kwargs["sequence"].matched, raw["sequence_successes"])
                    self.assertEqual(kwargs["sequence"].n, raw["sequence_n"])


if __name__ == "__main__":
    unittest.main()
