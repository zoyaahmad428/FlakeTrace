"""Generates a yield report (attempted -> built -> victim passes alone ->
reproduced -> excluded with reason) for every case in manifest.json.

Reads ONLY from eval/benchmark/logs/<case_id>.json. Never hand-types a
count: a case with no log file is reported as not_yet_run, not guessed at.
See eval/benchmark/logs/README.md for the log file format.
"""

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

BENCHMARK_DIR = Path(__file__).resolve().parent
MANIFEST_PATH = BENCHMARK_DIR / "manifest.json"
LOGS_DIR = BENCHMARK_DIR / "logs"


@dataclass(frozen=True)
class CaseYield:
    case_id: str
    attempted: bool
    not_yet_run: bool
    built: Optional[bool]
    victim_passes_alone: Optional[bool]
    reproduced: Optional[bool]
    excluded_reason: Optional[str]


def load_manifest(manifest_path=MANIFEST_PATH) -> list:
    with open(manifest_path, encoding="utf-8") as f:
        return json.load(f)["cases"]


def load_log(case_id: str, logs_dir=LOGS_DIR) -> Optional[dict]:
    log_path = Path(logs_dir) / f"{case_id}.json"
    if not log_path.exists():
        return None
    with open(log_path, encoding="utf-8") as f:
        return json.load(f)


def compute_case_yield(case_id: str, log: Optional[dict]) -> CaseYield:
    if log is None:
        return CaseYield(
            case_id=case_id,
            attempted=True,
            not_yet_run=True,
            built=None,
            victim_passes_alone=None,
            reproduced=None,
            excluded_reason=None,
        )
    return CaseYield(
        case_id=case_id,
        attempted=True,
        not_yet_run=False,
        built=log.get("built"),
        victim_passes_alone=log.get("victim_passes_alone"),
        reproduced=log.get("reproduced"),
        excluded_reason=log.get("excluded_reason"),
    )


def generate_yield_report(manifest_path=MANIFEST_PATH, logs_dir=LOGS_DIR) -> dict:
    manifest = load_manifest(manifest_path)
    case_yields = [compute_case_yield(case["case_id"], load_log(case["case_id"], logs_dir)) for case in manifest]

    def count(predicate) -> int:
        return sum(1 for cy in case_yields if predicate(cy))

    return {
        "total_cases": len(case_yields),
        "attempted": count(lambda cy: cy.attempted),
        "not_yet_run": count(lambda cy: cy.not_yet_run),
        "built": count(lambda cy: cy.built is True),
        "build_failed": count(lambda cy: cy.built is False),
        "victim_passes_alone": count(lambda cy: cy.victim_passes_alone is True),
        "victim_fails_alone": count(lambda cy: cy.victim_passes_alone is False),
        "reproduced": count(lambda cy: cy.reproduced is True),
        "not_reproduced": count(lambda cy: cy.reproduced is False),
        "excluded": count(lambda cy: cy.excluded_reason is not None),
        "cases": [asdict(cy) for cy in case_yields],
    }


if __name__ == "__main__":
    print(json.dumps(generate_yield_report(), indent=2))
    sys.exit(0)
