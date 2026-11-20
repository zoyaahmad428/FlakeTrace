import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { looksLikeReport, toView, type Report } from "./report";

const REPORTS = fileURLToPath(new URL("../../../../eval/reports/", import.meta.url));
const read = (name: string) => JSON.parse(readFileSync(`${REPORTS}${name}.json`, "utf-8")) as Report;

// Spec section 5: expected values copied from eval/reports/*.json (schema v2, regenerated 2026-11-19).
const EXPECTED: Record<string, { outcome: string; polluters: number; order: number; reduced: number; reproduction: string; alone: string }> = {
  f1: { outcome: "VERIFIED (sequence)", polluters: 1, order: 3, reduced: 2, reproduction: "20/20", alone: "0/20" },
  f2: { outcome: "VERIFIED (sequence)", polluters: 1, order: 8, reduced: 2, reproduction: "20/20", alone: "0/20" },
  f3: { outcome: "CANDIDATE", polluters: 2, order: 17, reduced: 3, reproduction: "20/20", alone: "0/20" },
  f4: { outcome: "VERIFIED (sequence)", polluters: 1, order: 14, reduced: 2, reproduction: "20/20", alone: "0/20" },
  n1: { outcome: "UNRESOLVED(VICTIM_FAILS_ALONE)", polluters: 0, order: 11, reduced: 1, reproduction: "20/20", alone: "20/20" },
  // N2 fails at random by design (NegativeFlakyTest), so its rate changes on every regeneration:
  // "from report" means the expected rate is read from n2.json itself (M3's request, PR #109).
  n2: { outcome: "UNRESOLVED(VICTIM_FAILS_ALONE)", polluters: 0, order: 12, reduced: 1, reproduction: "from report", alone: "from report" },
  n3: { outcome: "UNRESOLVED(NOT_REPRODUCED)", polluters: 0, order: 6, reduced: 6, reproduction: "0/20", alone: "0/20" },
  n4: { outcome: "UNRESOLVED(VICTIM_FAILS_ALONE_DIFFERENTLY)", polluters: 0, order: 5, reduced: 1, reproduction: "20/20", alone: "0/20" },
};

describe("toView on the eight committed reports", () => {
  for (const [name, e] of Object.entries(EXPECTED)) {
    it(name, () => {
      const v = toView(read(name));
      expect(v.outcome).toBe(e.outcome);
      expect(v.polluters).toHaveLength(e.polluters);
      expect(v.originalOrder).toHaveLength(e.order);
      expect(v.reducedSequence).toHaveLength(e.reduced);
      const r = read(name);
      const rate = (c: { matched: number; n: number }) => `${c.matched}/${c.n}`;
      expect(v.reproduction).toBe(e.reproduction === "from report" ? rate(r.reproduction) : e.reproduction);
      expect(v.alone).toBe(e.alone === "from report" ? rate(r.victim_alone) : e.alone);
    });
  }
});

describe("every null field becomes a stated reason", () => {
  for (const name of Object.keys(EXPECTED)) {
    it(name, () => {
      const v = toView(read(name));
      for (const [key, value] of Object.entries(v)) expect(value, key).not.toBeUndefined();
      if (v.resource === null) expect(v.resourceNote).not.toBe("");
      if (v.polluters.length === 0) expect(v.pollutersNote).not.toBe("");
      if (v.outcome.startsWith("UNRESOLVED")) expect(v.reason).toBeTruthy();
      expect(v.signature).not.toBe("");
      expect(v.exploration).not.toBe("");
    });
  }
});

describe("details", () => {
  it("names a system property by its key (F2)", () => {
    expect(toView(read("f2")).resource).toEqual({ name: 'System property "odfixture.turbo"', kind: "system property" });
  });
  it("names a static field (F3)", () => {
    expect(toView(read("f3")).resource?.name).toBe("odfixture.Toggles.flagA");
  });
  it("says when the read is in a method the victim calls (F2)", () => {
    expect(toView(read("f2")).read).toEqual({
      at: "odfixture.FeatureFlags#isTurboEnabled", cls: "odfixture.FeatureFlags", offset: 2, note: "read in a method the victim calls",
    });
  });
  it("explains a missing failure signature (N3)", () => {
    expect(toView(read("n3")).signature).toMatch(/^No failure signature: the failure never reproduced/);
  });
  it("describes how orders were explored", () => {
    expect(toView(read("f1")).exploration).toBe("The original order reproduced the failure; no shuffled orders were needed.");
    expect(toView(read("f4")).exploration).toBe("Reproduced with a shuffled order (seed 6) after 7 shuffled orders.");
    expect(toView(read("n3")).exploration).toBe("31 shuffled orders tried (seeds from 0); none reproduced the failure.");
  });
  it("shows every alone outcome, so failing alone differently is visible (FT003, N4)", () => {
    expect(toView(read("n4")).aloneDetail).toBe("passed 0 · failed differently 20 · crashed or not run 0");
    expect(toView(read("n4")).reason).toMatch(/fails when run alone with a different failure/);
  });
  it("says why a result is only a candidate (F3)", () => {
    expect(toView(read("f3")).candidateReasons).toEqual([
      "not every kept test is shown to be needed: at least one deletion check (W20) did not run, ran fewer than 10 times, or is not yet read into the report",
    ]);
    expect(toView(read("f1")).candidateReasons).toEqual([]);
  });
  it("gives the Wilson interval", () => {
    expect(toView(read("f1")).reproductionBounds).toBe("95% Wilson interval [0.839, 1.000]");
  });
  it("recognises a report by its required fields", () => {
    expect(looksLikeReport(read("f1"))).toBe(true);
    for (const bad of [null, [], {}, { outcome: "VERIFIED" }, "text"]) expect(looksLikeReport(bad)).toBe(false);
  });
});
