"""W9 command line (ADR-005): py -m runner diagnose --project DIR --victim Class#method.

Runs runner.diagnose.diagnose(), Member 1's resource evidence for a found polluter and
Member 3's assemble_report(), then writes the report next to its execution record.
Exit codes: 0 report written, 2 input wrong, 1 tool failed, 3 no report can be built yet.
`replay` (W23): 0 the verdict is the same, 4 it differs, 2 input wrong, 1 tool failed.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from eval.baseline import TestIdentifier
from eval.report import UnhandledStatus, assemble_report
from evidence.extract import DEFAULT_DEPTH, ExtractError, Project, analyse_pair, report_fields
from runner.budget import Budget
from runner.bundle import BundleError, write_bundle
from runner.diagnose import INCONSISTENT, NOT_REPRODUCED, POLLUTER_FOUND, DiagnoseInputError, diagnose
from runner.deletion import DELETION_RUN, INCONCLUSIVE, NEEDED, NOT_NEEDED, NOT_RUN
from runner.order_runner import LIFECYCLES, ToolError
from runner.policy import POLICIES, SCOPES
from runner.workspace import WORKSPACES, WorkspaceError, workspace

_VICTIM = re.compile(r"[\w.$]+#[\w$]+")

_NO_REPORT_WHY = {
    INCONSISTENT: "the victim failed in the original order but not again (alone, after any single "
                        "earlier test, or in the full order once more), so no test is blamed; likely flaky",
    NOT_REPRODUCED: "the victim never failed with a real failure in n runs of the original order",
}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="py -m runner")
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("diagnose", help="diagnose one failing test and write its report")
    command.add_argument("--project", required=True, help="Maven project folder (contains pom.xml)")
    command.add_argument("--victim", required=True, help="failing test as Class#method")
    command.add_argument("--n", type=int, default=20, help="repeat count (default 20)")
    command.add_argument("--records", default="flaketrace-records",
                         help="folder for the execution record and the report")
    command.add_argument("--order", default=None,
                         help="file with the real failing order, one Class#method per line (ADR-008)")
    command.add_argument("--shuffles", type=int, default=31,
                         help="distinct shuffled orders to try if the order never fails (default 31)")
    command.add_argument("--seed", type=int, default=0, help="first shuffle seed (default 0)")
    command.add_argument("--lifecycle", choices=LIFECYCLES, default="class-grouped",
                         help="class-grouped (default): @BeforeClass once per run of same-class tests, as under "
                              "Maven Surefire (ADR-012; verified by M1); per-method: once per test, as at the Mid")
    command.add_argument("--workspace", choices=WORKSPACES, default="copy",
                         help="copy (default): build and run in a temporary copy of the project, deleted "
                              "afterwards, so the project folder is never written to; in-place: as at the Mid")
    command.add_argument("--copy-parent", default=None,
                         help="folder to make the temporary copy in (default: the system temp folder)")
    command.add_argument("--budget-invocations", type=int, default=None,
                         help="stop after this many test-method invocations; 3 x n of them are kept for "
                              "verification (W24, ADR-014). Default: no limit, still counted")
    command.add_argument("--budget-seconds", type=float, default=None,
                         help="stop searching after this many seconds; verification still runs (W24)")
    command.add_argument("--policy", choices=POLICIES, default="original",
                         help="order of the single-polluter search: original (default), ranked by static evidence "
                              "(M1's ranking, ADR-014), or random (seeded by --seed; for evaluation) (W25)")
    command.add_argument("--scope", choices=SCOPES, default="module",
                         help="module (default): every discovered test; package: only tests in the victim's "
                              "package (the real-case protocol's scope rule; not with --order) (W25)")
    command.add_argument("--bundle", default=None,
                         help="also write an evidence bundle (report, record, environment, replay commands; "
                              "personal paths removed) into this folder (W23, ADR-013)")
    again = commands.add_parser("replay", help="re-check a bundle's evidence on a checkout and compare the verdict")
    again.add_argument("bundle", help="a bundle folder written by diagnose --bundle")
    again.add_argument("--project", required=True, help="checkout of the subject at the bundle's commit")
    again.add_argument("--bundle", dest="out", default="flaketrace-bundles",
                       help="folder for the replay's own bundle (default flaketrace-bundles)")
    again.add_argument("--records", default="flaketrace-records", help="folder for the replay's record")
    arguments = list(argv if argv is not None else sys.argv[1:])
    args = parser.parse_args(arguments)
    if args.command == "replay":
        return run_replay(Path(args.bundle), Path(args.project), args.out, args.records, arguments)
    if args.budget_invocations is not None and args.budget_invocations < 1:
        return _error(f"--budget-invocations must be >= 1, got {args.budget_invocations}", 2)
    if args.budget_seconds is not None and args.budget_seconds <= 0:
        return _error(f"--budget-seconds must be > 0, got {args.budget_seconds:g}", 2)
    if args.scope == "package" and args.order:
        return _error("--scope package cannot be combined with --order: the order file already fixes the tests", 2)
    budget = (Budget(args.budget_invocations, args.budget_seconds)
              if args.budget_invocations is not None or args.budget_seconds is not None else None)
    return run_diagnose(Path(args.project), args.victim, args.n, args.records,
                        Path(args.order) if args.order else None, args.shuffles, args.seed, arguments, args.lifecycle,
                        args.workspace, Path(args.copy_parent) if args.copy_parent else None, budget,
                        args.policy, args.scope, args.bundle)


def run_diagnose(project: Path, victim_id: str, n: int, records: str, order_path: Optional[Path] = None,
                 shuffles: int = 31, seed: int = 0, command: Optional[List[str]] = None,
                 lifecycle: str = "class-grouped", workspace_mode: str = "copy",
                 copy_parent: Optional[Path] = None, budget: Optional[Budget] = None,
                 policy: str = "original", scope: str = "module", bundle: Optional[str] = None) -> int:
    # Java names only: the victim also becomes part of the record's file name.
    if not _VICTIM.fullmatch(victim_id):
        return _error(f"--victim must be Class#method (Java names, no spaces), got {victim_id!r}", 2)
    class_name, _, method = victim_id.partition("#")
    if not (project / "pom.xml").is_file():
        return _error(f"no pom.xml in {project}; --project must be a Maven project folder", 2)
    if shuffles < 0:
        return _error(f"--shuffles must be >= 0, got {shuffles}", 2)
    victim = TestIdentifier(class_name, method)
    order = None
    if order_path is not None:
        try:
            order = read_order(order_path, victim)
        except OrderFileError as error:
            return _error(str(error), 2)

    # ADR-012 section 4: build, run and extract evidence in `work`, a disposable copy by default.
    try:
        with workspace(project, workspace_mode, copy_parent) as work:
            work_path = Path(work).resolve()
            outcome = _diagnose_in(work, project, victim, n, records, order, shuffles, seed, command, lifecycle,
                                   workspace_mode, budget, policy, scope)
    except WorkspaceError as error:
        return _error(str(error), 1)
    if isinstance(outcome, int):
        return outcome
    runs, fields = outcome

    try:
        report = assemble_report(runs, fields)
    except UnhandledStatus:
        why = _NO_REPORT_WHY.get(runs.status, "eval.report cannot build this report yet")
        print(f"No report: {runs.status} - {why}\n  record: {runs.execution_record}")
        if runs.budget is not None:
            print(budget_line(runs.budget))
        return 3

    report_path = Path(runs.execution_record).with_suffix(".report.json")
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    ddmin_ran = runs.minimise_runs and runs.polluters
    crashes = runs.infrastructure_failures + runs.shuffle_infrastructure_failures + runs.alone_infrastructure_failures
    print(summary(report, report_path, (len(runs.original_order) - 1, runs.minimise_runs) if ddmin_ran else None,
                  crashes, runs.deletion_checks, runs.budget, runs.search))
    if bundle is not None:
        try:
            folder = write_bundle(bundle, report, runs.execution_record, environment_text=_environment_text(),
                                  paths={str(work_path): "<project>", str(project.resolve()): "<project>",
                                         str(Path(records).resolve()): "<records>"},
                                  **_subject(project))
        except BundleError as error:
            return _error(str(error), 1)
        print(f"  bundle:     {folder}")
    return 0


def run_replay(bundle: Path, project: Path, out: str, records: str, command: Optional[List[str]] = None) -> int:
    """W23 (Interface 8 R1-R7). Exit codes: 0 same verdict, 4 the verdict differs, 2 input, 1 tool failed."""
    from runner.replay import replay
    if not (project / "pom.xml").is_file():
        return _error(f"no pom.xml in {project}; --project must be a checkout of the bundle's subject", 2)
    try:
        # Interface 8 R2: a replay always runs on a copy of the checkout.
        code, lines, folder = replay(bundle, project, out, records, 120.0, "copy", command)
    except DiagnoseInputError as error:
        return _error(str(error), 2)
    except (BundleError, WorkspaceError, ToolError) as error:
        return _error(str(error), 1)
    except ExtractError as error:
        return _error(f"resource evidence failed: {error}", 1)
    except subprocess.CalledProcessError as error:
        return _error(f"{Path(str(error.cmd[0])).name} failed with exit code {error.returncode} on {project}", 1)
    if code == 2:
        return _error(lines[0], 2)
    print("\n".join(lines))
    print(f"  bundle:     {folder}")
    return code


def _diagnose_in(work: Path, project: Path, victim, n, records, order, shuffles, seed, command, lifecycle,
                 workspace_mode, budget=None, policy="original", scope="module"):
    """The diagnosis and Member 1's evidence, run in `work`. Returns (runs, fields), or an exit code
    after printing the error. Messages name the user's project, never the temporary copy."""
    def own(text: str) -> str:
        return text.replace(str(Path(work).resolve()), str(project))
    # A copy holds only the project folder: a module whose build reads ../pom.xml fails in it.
    hint = ("; if the build needs files outside the project folder (e.g. a parent pom.xml), "
            "try --workspace in-place") if workspace_mode == "copy" else "; run it there to see why"
    try:
        runs = diagnose(work, victim, n=n, record_dir=records, original_order=order,
                        shuffles=shuffles, seed=seed, command=command, lifecycle=lifecycle,
                        workspace=workspace_mode, origin=project if workspace_mode == "copy" else None,
                        budget=budget, policy=policy, scope=scope)
    except DiagnoseInputError as error:
        return _error(own(str(error)), 2)
    except subprocess.CalledProcessError as error:
        tool = Path(str(error.cmd[0])).name
        return _error(f"{tool} failed with exit code {error.returncode} on {project}{hint}", 1)
    except subprocess.TimeoutExpired as error:
        return _error(f"{Path(str(error.cmd[0])).name} timed out after {error.timeout:g} s on {project}", 1)
    except ToolError as error:
        return _error(own(str(error)), 1)
    try:
        fields = resource_fields(work, runs) if runs.status == POLLUTER_FOUND else None
    except ExtractError as error:
        return _error(f"resource evidence failed: {own(str(error))}", 1)
    return runs, fields


def resource_fields(project: Path, runs) -> dict:
    """Member 1's pair-mode evidence for each polluter and the victim, combined (ADR-007).
    analyse_pair deepens each pair on its own when nothing is found at the default depth (ADR-006)."""
    classes = Project([str(project / "target" / "classes"), str(project / "target" / "test-classes")])
    victim = str(runs.victim)
    return combine_fields([analyse_pair(classes, str(p), victim) for p in runs.polluters])


def combine_fields(pairs: list) -> dict:
    """Report fields from one pair per polluter. One polluter: M1's report_fields unchanged.
    Several: the first polluter's edge is shown and the others named in limitations, but only if
    every polluter has an edge -- VERIFIED needs a static overlap for every blamed test."""
    fields = [report_fields(pair) for pair in pairs]
    if len(fields) == 1:
        return fields[0]
    # W21: every polluter's edges, in polluter order, each once.
    edges = []
    for single in fields:
        edges += [edge for edge in single.get("resource_edges", []) if edge not in edges]
    # The first polluter's projected lines, plus only M1's fixed lines from the others: their own
    # "not shown" lines would name a resource a second time.
    lines = list(fields[0]["limitations"])
    for pair in pairs[1:]:
        lines += [line for line in pair["limitations"] if line not in lines]
    if all(pair["edges"] for pair in pairs):
        shown = pairs[0]["edges"][0]["resource_id"]
        # Schema v2 shows every edge in resource_edges, so these are named, not hidden (A2, 2026-11-20).
        others = [f"Polluter {_test(pair['polluter'])}: shared resource {edge['resource_id']} is not the headline "
                  "resource; it is listed in resource_edges"
                  + _depth_note(edge) for pair in pairs[1:] for edge in pair["edges"] if edge["resource_id"] != shown]
        return dict(fields[0], limitations=lines + others, resource_edges=edges)
    found = [f"Polluter {_test(pair['polluter'])}: shared resource {edge['resource_id']} was found, "
             "but not every polluter has evidence" + _depth_note(edge) for pair in pairs for edge in pair["edges"]]
    missing = [f"No polluter-write/victim-read resource edge was found for polluter {_test(pair['polluter'])}"
               for pair in pairs if not pair["edges"]]
    # any_edge_found tells M3's assemble_report not to add its generic "no edge was found" line.
    return dict(fields[0], shared_resource=None, polluter_write_location=None, victim_read_location=None,
                resource_edges=edges,
                limitations=lines + found + missing, any_edge_found=bool(found))


def search_line(search, candidates: int, searched: bool = True) -> List[str]:
    """W25 (Interface 7): how the search ordered its candidates. A rank orders the search; it never says
    what caused the failure (claims ledger G3)."""
    scope = ", victim's package only" if search.scope == "package" else ""
    if not searched:
        lines = [f"  search:     no single-polluter search ran (policy {search.policy}){scope}"]
        if search.scope == "package" and candidates == 0:
            lines.append("              the victim's package has no other test; re-run with --scope module")
        return lines
    if search.policy == "random":
        return [f"  search:     random order (seed {search.seed}){scope}"]
    if search.policy == "ranked" and search.note:
        return [f"  search:     ranked, fell back to the original order{scope}", "              " + search.note]
    if search.policy == "ranked" and search.depths and not search.candidates_with_evidence:
        depths = "->".join(str(depth) for depth in search.depths)
        return [f"  search:     ranked at depth {depths}: no candidate had evidence, original order kept{scope}"]
    if search.policy == "ranked" and search.depths:
        depths = "->".join(str(depth) for depth in search.depths)
        return [f"  search:     ranked by static evidence at depth {depths} ({search.candidates_with_evidence} of "
                f"{candidates} candidates with evidence){scope}"]
    return [f"  search:     original order{scope}"]


def _environment_text() -> str:
    """ADR-013's environment.txt: what `java -version` and `mvn -v` print (a missing tool says so)."""
    parts = []
    for command in (["java", "-version"], ["mvn", "-v"]):
        try:
            done = subprocess.run([shutil.which(command[0]) or command[0], *command[1:]], capture_output=True,
                                  text=True, timeout=60)
            parts.append(f"$ {' '.join(command)}\n{done.stdout}{done.stderr}")
        except (OSError, subprocess.SubprocessError) as error:
            parts.append(f"$ {' '.join(command)}\nnot available: {error}\n")
    return "\n".join(parts)


def _subject(project: Path) -> dict:
    """Interface 8's subject: "fixture" for a project inside this repository, else its origin URL."""
    project = project.resolve()
    repository_root = Path(__file__).resolve().parents[1]
    top = subprocess.run(["git", "-C", str(project), "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    root = Path(top.stdout.strip()).resolve() if top.returncode == 0 and top.stdout.strip() else None
    module_path = project.relative_to(root).as_posix() if root and root in [project, *project.parents] else None
    if repository_root == project or repository_root in project.parents:
        return {"repository": "fixture", "module_path": module_path}
    origin = subprocess.run(["git", "-C", str(project), "remote", "get-url", "origin"], capture_output=True, text=True)
    return {"repository": origin.stdout.strip() if origin.returncode == 0 else None, "module_path": module_path}


def budget_line(account) -> str:
    """W24 (Interface 6): what the diagnosis spent and, if it stopped early, where."""
    spent = sum(account.spent.values())
    limit = (f"spent {spent} of {account.limit_invocations} invocations" if account.limit_invocations is not None
             else f"spent {spent} invocations, no limit")
    stopped = f"; stopped in {account.exhausted_phase}" if account.exhausted else ""
    return (f"  budget:     {limit} (reserve {account.reserve_invocations}); search tried "
            f"{account.candidates_tried} of {account.candidates_total} candidates{stopped}")


def _depth_note(edge: dict) -> str:
    """The depth of an edge that is only named, measured like M1's report_fields does for the shown one."""
    depth = max(edge["polluter_write_locations"][0]["depth"], edge["victim_read_locations"][0]["depth"])
    return f" (evidence at depth {depth}, above the default {DEFAULT_DEPTH})" if depth > DEFAULT_DEPTH else ""


def summary(report: dict, report_path: Path, minimised: Optional[Tuple[int, int]] = None,
            crashes: int = 0, deletion_checks: Sequence = (), budget=None, search=None) -> str:
    """`minimised` = (earlier tests, ddmin runs) when ddmin found the polluters (ADR-007); the report's
    schema has no field for it, so only the summary says how far the order was shrunk.
    `deletion_checks` (W20) may drop tests after ddmin, so ddmin's own count is its round-1 checks."""
    reason = f" ({report['unresolved_reason']})" if report["unresolved_reason"] else ""
    # ADR-010 Q3: VERIFIED is about the sequence, never about the resource being the cause.
    qualifier = " (sequence)" if report["outcome"] == "VERIFIED" else ""
    lines = [f"{report['outcome']}{qualifier}{reason}  {_test(report['victim'])}"]
    if report["polluters"]:
        lines.append("  polluter:   " + ", ".join(_test(p) for p in report["polluters"]))
    first_round = [c for c in deletion_checks if c.round == 1]
    removals = [c for c in deletion_checks if c.source == DELETION_RUN and c.status != NOT_RUN]
    not_run = sum(c.status == NOT_RUN for c in deletion_checks)
    if minimised:
        earlier, runs = minimised
        count = len(first_round) if first_round else len(report["polluters"])
        checked = "" if deletion_checks else "; not deletion-verified"
        lines.append(f"  minimised:  {earlier} earlier tests -> {count} polluter{'s' if count != 1 else ''} "
                     f"in {runs} runs (reduced by single-trial delta debugging{checked})")
    last_round = [c for c in deletion_checks if deletion_checks and c.round == deletion_checks[-1].round]
    if removals and all(c.status == NEEDED for c in last_round) and not any(c.status == NOT_NEEDED for c in removals):
        # M1's W20 verification (PR #137): say it plainly when every kept test was confirmed needed.
        lines.append(f"  deletion:   each kept test confirmed needed: removed one at a time, {removals[0].runs.n} runs "
                     f"each ({sum(c.runs.n for c in removals)} runs), the victim passed every run")
    elif removals:
        dropped = sum(c.status == NOT_NEEDED for c in removals)
        unsure = sum(c.status == INCONCLUSIVE for c in deletion_checks if c.round == deletion_checks[-1].round)
        lines.append(f"  deletion:   kept tests removed one at a time, {removals[0].runs.n} runs each "
                     f"({sum(c.runs.n for c in removals)} runs): {dropped} dropped as not needed, {unsure} inconclusive"
                     + (f", {not_run} not run (budget)" if not_run else ""))
    explored = report.get("order_exploration")
    if explored and explored["reproducing_seed"] is not None:
        lines.append(f"  orders:     reproduced in shuffled order (seed {explored['reproducing_seed']}) "
                     f"after {explored['shuffled_orders_tried']} shuffled orders")
    if report["unresolved_reason"] == "NOT_REPRODUCED" and explored:
        exhausted = " (no further distinct order found)" if explored["orders_exhausted"] else ""
        # A crash or timeout is not a pass: never say "never failed" when runs only crashed.
        result = f"no real failure ({crashes} runs crashed or timed out)" if crashes else "never failed"
        # "given" only for an order from --order; otherwise FlakeTrace discovered it.
        source = "given" if explored["order_given"] else "discovered"
        lines.append(f"  orders:     {source} order {report['reproduction']['n']}x, "
                     f"{explored['shuffled_orders_tried']} distinct shuffled orders{exhausted}, "
                     f"alone {report['victim_alone']['n']}x: {result}")
        lines.append(f"  bound:      failure rate in the {source} order < {report['reproduction']['upper']:.3f} "
                     "(95% Wilson), not proof of reliability")
    if report["shared_resource"]:
        resource = " ".join(str(value) for value in report["shared_resource"].values())
        write, read = report["polluter_write_location"], report["victim_read_location"]
        if write and read:
            resource += (f" (write {_test(write)}@{write['bytecode_offset']}"
                         f" -> read {_test(read)}@{read['bytecode_offset']})")
        lines.append(f"  resource:   {resource}")
        lines.append("              static overlap: a possible mechanism, not confirmed as the cause")
    reproduced, alone = report["reproduction"], report["victim_alone"]
    # The alone count holds only failures matching the reference signature (claims ledger G1, FT003);
    # "other failure" keeps a victim that fails alone differently (N4) apart from one that passes (F1).
    if report["unresolved_reason"] == "BUDGET_EXHAUSTED":
        # W24: these are only the starting order's runs before the budget ran out, not a verified sequence.
        sequence = (f"no sequence verified (the starting order failed {reproduced['matched']} of {reproduced['n']} "
                    "run(s) before the budget ran out)")
    else:
        sequence = f"{reproduced['matched']}/{reproduced['n']} (lower bound {reproduced['lower']:.3f})"
    lines.append(f"  reproduced: {sequence}   alone (same failure): {alone['matched']}/{alone['n']}, "
                 f"other failure: {alone['other']}/{alone['n']}")
    if search is not None:
        lines += search_line(search, budget.candidates_total if budget is not None else 0,
                             searched=budget is None or budget.spent["search"] > 0)
    if budget is not None:
        lines.append(budget_line(budget))
    lines.append(f"  report:     {report_path}")
    lines.append(f"  record:     {report['execution_record_reference']}")
    return "\n".join(lines)


class OrderFileError(Exception):
    """A problem with the --order file (exit 2)."""


def read_order(path: Path, victim: TestIdentifier) -> List[TestIdentifier]:
    """One Class#method per line; blank and # lines ignored; BOM and CRLF allowed (ADR-008)."""
    try:
        data = path.read_bytes()
    except OSError as error:
        raise OrderFileError(f"cannot read --order file {path}: {error.strerror}")
    try:
        # Windows PowerShell 5.1's `>` writes UTF-16 with a BOM; everything else is UTF-8 (BOM optional).
        text = data.decode("utf-16") if data[:2] in (b"\xff\xfe", b"\xfe\xff") else data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise OrderFileError(f"--order file {path} is not UTF-8 or UTF-16 text")
    order: List[TestIdentifier] = []
    seen = set()  # a set, not the list: a long order would make the duplicate check quadratic
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if not _VICTIM.fullmatch(line):
            raise OrderFileError(f"--order line {number} is not Class#method: {line!r}")
        class_name, _, method = line.partition("#")
        test = TestIdentifier(class_name, method)
        if test in seen:
            raise OrderFileError(f"--order lists {test} twice (line {number})")
        seen.add(test)
        order.append(test)
    if not order:
        raise OrderFileError(f"--order file {path} lists no tests")
    if victim not in order:
        raise OrderFileError(f"--order does not contain the victim {victim}")
    return order


def _test(location: dict) -> str:
    return f"{location['class']}#{location['method']}"


def _error(message: str, code: int) -> int:
    print(f"error: {message}", file=sys.stderr)
    return code
