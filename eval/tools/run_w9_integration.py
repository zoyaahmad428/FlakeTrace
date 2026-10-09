"""W9 end-to-end integration: produce real, pipeline-assembled diagnosis reports for F1, F2
and N1.

One-off script, not part of the unit test suite (it shells out to real Maven/JDK via
runner.diagnose and runner.OrderRunner, and takes a few minutes). Run manually:

    py eval/tools/run_w9_integration.py

Writes eval/reports/{f1,f2,n1}.json -- genuinely produced by calling runner.diagnose.diagnose()
and evidence.extract's real find_edges/report_fields for real, then
eval.report.assemble_report(), not hand-written. See eval/reports/README.md.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from eval.baseline import TestIdentifier
from eval.report import assemble_report
from evidence.extract import DEFAULT_DEPTH, Project, analyse_test, find_edges, report_fields
from runner.diagnose import diagnose

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = REPO_ROOT / "fixtures" / "od-fixture"
REPORTS_DIR = REPO_ROOT / "eval" / "reports"
RECORD_DIR = REPO_ROOT / "eval" / "reports" / "flaketrace-records"


def run_f1():
    victim = TestIdentifier("odfixture.ConfigVictimTest", "expectsDefaultMode")
    print("=== F1: running diagnose() for real (n=20) ===")
    diagnosis = diagnose(FIXTURE, victim, n=20, record_dir=str(RECORD_DIR))
    print(diagnosis)

    print("=== F1: running evidence.extract's real pair mode (find_edges/report_fields) ===")
    project = Project([str(FIXTURE / "target" / "classes"), str(FIXTURE / "target" / "test-classes")])
    polluter_id = "odfixture.ConfigPolluterTest#pollute"
    victim_id = "odfixture.ConfigVictimTest#expectsDefaultMode"
    polluter_access = analyse_test(project, polluter_id, depth=DEFAULT_DEPTH)
    victim_access = analyse_test(project, victim_id, depth=DEFAULT_DEPTH)
    pair = find_edges(polluter_id, polluter_access, victim_id, victim_access)
    fields = report_fields(pair)
    print("resource fields:", fields)

    report = assemble_report(diagnosis, fields)
    print("=== F1 report ===")
    print(json.dumps(report, indent=2))
    (REPORTS_DIR / "f1.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def run_f2():
    victim = TestIdentifier("odfixture.FeatureVictimTest", "expectsTurboDisabled")
    print("=== F2: running diagnose() for real (n=20) ===")
    diagnosis = diagnose(FIXTURE, victim, n=20, record_dir=str(RECORD_DIR))
    print(diagnosis)

    print("=== F2: running evidence.extract's real pair mode (find_edges/report_fields) ===")
    project = Project([str(FIXTURE / "target" / "classes"), str(FIXTURE / "target" / "test-classes")])
    polluter_id = "odfixture.FeaturePolluterTest#enableTurbo"
    victim_id = "odfixture.FeatureVictimTest#expectsTurboDisabled"
    polluter_access = analyse_test(project, polluter_id, depth=DEFAULT_DEPTH)
    victim_access = analyse_test(project, victim_id, depth=DEFAULT_DEPTH)
    pair = find_edges(polluter_id, polluter_access, victim_id, victim_access)
    fields = report_fields(pair)
    print("resource fields:", fields)

    report = assemble_report(diagnosis, fields)
    print("=== F2 report ===")
    print(json.dumps(report, indent=2))
    (REPORTS_DIR / "f2.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def run_n1():
    victim = TestIdentifier("odfixture.NegativeAloneFailTest", "alwaysFails")
    print("=== N1: running diagnose() for real (n=20) ===")
    diagnosis = diagnose(FIXTURE, victim, n=20, record_dir=str(RECORD_DIR))
    print(diagnosis)

    report = assemble_report(diagnosis)  # no resource edge: N1 needs none
    print("=== N1 report ===")
    print(json.dumps(report, indent=2))
    (REPORTS_DIR / "n1.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    REPORTS_DIR.mkdir(exist_ok=True)
    f1 = run_f1()
    f2 = run_f2()
    n1 = run_n1()
    print("\n=== SUMMARY ===")
    print("F1 outcome:", f1["outcome"], f1["unresolved_reason"])
    print("F2 outcome:", f2["outcome"], f2["unresolved_reason"])
    print("N1 outcome:", n1["outcome"], n1["unresolved_reason"])
