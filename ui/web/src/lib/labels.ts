export type Unbuilt = { feature: string; label: string; source: string };

export const NOT_IN_PLAN = "NOT BUILT — NOT IN CURRENT PLAN";
const planned = (when: string) => `NOT BUILT YET — PLANNED FOR ${when}`;
const NO_SOURCE = "Not in the roadmap or any decision record";

export const UNBUILT = {
  container: { feature: "Running the project in a container", label: planned("Iteration 2"), source: 'Mid report, Conclusion: "a first container deployment"' },
  remoteSource: { feature: "Loading a project from a GitHub URL or a zip archive", label: NOT_IN_PLAN, source: NO_SOURCE },
  budget: { feature: "Execution budget", label: planned("a later iteration"), source: 'Mid report, Conclusion: "Later iterations add the execution budget"' },
  ranking: { feature: "Ranking candidate polluters using the evidence module", label: planned("Iteration 2"), source: 'Mid report, Conclusion: "ranks candidates using the evidence module"' },
  filesystem: { feature: "Filesystem evidence", label: planned("FYP-II early"), source: "docs/00-Meta/roadmap.md, FYP-II early" },
  runtime: { feature: "Runtime (dynamic) evidence", label: planned("Iteration 2"), source: "docs/00-Meta/roadmap.md, Iteration 2: dynamic collection" },
  teardown: { feature: '"Restored in teardown" detection', label: NOT_IN_PLAN, source: NO_SOURCE },
  repair: { feature: "Certificate-Driven Remediation: a suggested patch, checked on a copy, applied by a developer", label: planned("FYP-II early, gated"), source: "docs/07-Defense/decisions/cdr-gated-module.md" },
  verify: { feature: "Repair verification", label: planned("Iteration 3, gated"), source: "docs/00-Meta/roadmap.md, Iteration 3: repair verification (gated)" },
  evosuite: { feature: "EvoSuite test generation", label: NOT_IN_PLAN, source: NO_SOURCE },
} satisfies Record<string, Unbuilt>;
