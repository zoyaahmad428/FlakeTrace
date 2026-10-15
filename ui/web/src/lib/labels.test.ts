import { describe, expect, it } from "vitest";
import { NOT_IN_PLAN, UNBUILT } from "./labels";

describe("labels for unbuilt parts (spec section 5)", () => {
  it("match the approved wording exactly", () => {
    expect(Object.fromEntries(Object.entries(UNBUILT).map(([id, item]) => [id, item.label]))).toEqual({
      container: "NOT BUILT YET — PLANNED FOR Iteration 2",
      remoteSource: "NOT BUILT — NOT IN CURRENT PLAN",
      budget: "NOT BUILT YET — PLANNED FOR a later iteration",
      ranking: "NOT BUILT YET — PLANNED FOR Iteration 2",
      filesystem: "NOT BUILT YET — PLANNED FOR FYP-II early",
      runtime: "NOT BUILT YET — PLANNED FOR Iteration 2",
      teardown: "NOT BUILT — NOT IN CURRENT PLAN",
      repair: "NOT BUILT YET — PLANNED FOR FYP-II early, gated",
      verify: "NOT BUILT YET — PLANNED FOR Iteration 3, gated",
      evosuite: "NOT BUILT — NOT IN CURRENT PLAN",
    });
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
