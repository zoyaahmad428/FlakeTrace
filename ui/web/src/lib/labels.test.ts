import { describe, expect, it } from "vitest";
import { NOT_IN_PLAN, UNBUILT } from "./labels";

describe("labels for unbuilt parts (spec section 5)", () => {
  it("match the approved wording exactly", () => {
    expect(Object.fromEntries(Object.entries(UNBUILT).map(([id, item]) => [id, item.label]))).toEqual({
      container: "IN THE COMMAND LINE ONLY (docker run flaketrace:w27, W27) — NOT FROM THE UI; a hardened container for untrusted projects is FYP-2",
      remoteSource: "NOT BUILT — NOT IN CURRENT PLAN",
      replay: "IN THE COMMAND LINE ONLY (py -m runner replay, W23) — NOT IN THE UI",
      filesystem: "NOT BUILT YET — PLANNED FOR FYP-II early",
      runtime: "NOT BUILT — ADR-001's fallback replaced by ADR-015's spike (W34, stretch); awaits the supervisor",
      teardown: "NOT BUILT — NOT IN CURRENT PLAN",
      repair: "NOT BUILT YET — PLANNED FOR FYP-II early, gated",
      verify: "NOT BUILT YET — PLANNED FOR Iteration 3, gated",
      evosuite: "NOT BUILT — NOT IN CURRENT PLAN",
    });
  });

  it("no longer labels what the UI now runs (budget, ranked search: the Advanced run options)", () => {
    expect("budget" in UNBUILT || "ranking" in UNBUILT).toBe(false);
  });

  it("gives a source for every label", () => {
    for (const item of Object.values(UNBUILT)) expect(item.source.length).toBeGreaterThan(0);
  });

  it("marks exactly the three parts no document plans", () => {
    expect(Object.values(UNBUILT).filter((item) => item.label === NOT_IN_PLAN).map((item) => item.feature)).toEqual([
      "Loading a project from a GitHub URL or a zip archive",
      '"Restored in teardown" detection',
      "EvoSuite test generation",
    ]);
  });
});
