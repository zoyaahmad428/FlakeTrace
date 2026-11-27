export type Unbuilt = { feature: string; label: string; source: string };

export const NOT_IN_PLAN = "NOT BUILT — NOT IN CURRENT PLAN";
const planned = (when: string) => `NOT BUILT YET — PLANNED FOR ${when}`;
const NO_SOURCE = "Not in the roadmap or any decision record";

export const UNBUILT = {
  container: { feature: "Running the project in a container", label: "IN THE COMMAND LINE ONLY (docker run flaketrace:w27, W27) — NOT FROM THE UI; a hardened container for untrusted projects is FYP-2", source: "Dockerfile (W27, M3); ADR-012 section 1; docs/10-Final1/action-register.md A3" },
  remoteSource: { feature: "Loading a project from a GitHub URL or a zip archive", label: NOT_IN_PLAN, source: NO_SOURCE },
  replay: { feature: "Replaying a bundle's evidence on another checkout", label: "IN THE COMMAND LINE ONLY (py -m runner replay, W23) — NOT IN THE UI", source: "ADR-013; docs/contracts/interfaces.md Interface 8" },
  filesystem: { feature: "Filesystem evidence", label: planned("FYP-II early"), source: "docs/00-Meta/roadmap.md, FYP-II early" },
  runtime: { feature: "Runtime (dynamic) evidence", label: "NOT BUILT — ADR-001's fallback replaced by ADR-015's spike (W34, stretch); awaits the supervisor", source: "ADR-001; ADR-015; docs/04-Implementation/evidence-collector.md section 3a; docs/10-Final1/supervisor-agenda.md" },
  teardown: { feature: '"Restored in teardown" detection', label: NOT_IN_PLAN, source: NO_SOURCE },
  repair: { feature: "Certificate-Driven Remediation: a suggested patch, checked on a copy, applied by a developer", label: planned("FYP-II early, gated"), source: "docs/07-Defense/decisions/cdr-gated-module.md" },
  verify: { feature: "Repair verification", label: planned("Iteration 3, gated"), source: "docs/00-Meta/roadmap.md, Iteration 3: repair verification (gated)" },
  evosuite: { feature: "EvoSuite test generation", label: NOT_IN_PLAN, source: NO_SOURCE },
} satisfies Record<string, Unbuilt>;
