import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { invocations, looksLikeReport, reproducedKind, toView, type Report } from "./report";

const REPORTS = fileURLToPath(new URL("../../../../eval/reports/", import.meta.url));
const read = (name: string) => JSON.parse(readFileSync(`${REPORTS}${name}.json`, "utf-8")) as Report;

// Spec section 5: expected values copied from eval/reports/*.json (schema v2, regenerated 2026-11-19).
const EXPECTED: Record<string, { outcome: string; polluters: number; order: number; reduced: number; reproduction: string; alone: string }> = {
  f1: { outcome: "VERIFIED (sequence)", polluters: 1, order: 3, reduced: 2, reproduction: "20/20", alone: "0/20" },
  f2: { outcome: "VERIFIED (sequence)", polluters: 1, order: 8, reduced: 2, reproduction: "20/20", alone: "0/20" },
  f3: { outcome: "VERIFIED (sequence)", polluters: 2, order: 17, reduced: 3, reproduction: "20/20", alone: "0/20" },
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
  it("says why a result is only a candidate (F3-shaped, before W20's deletion check)", () => {
    // F3 itself is VERIFIED now (W20 landed, 2026-11-20): both polluters' real deletion
    // checks come back NEEDED. No real committed report is CANDIDATE any more, so this
    // reuses F3's real shape with outcome/candidate_reasons overridden to the state F3
    // itself was in before W20 -- still a faithful DELETION_EVIDENCE_INCOMPLETE case.
    const stillIncomplete: Report = { ...read("f3"), outcome: "CANDIDATE", candidate_reasons: ["DELETION_EVIDENCE_INCOMPLETE"] };
    expect(toView(stillIncomplete).candidateReasons).toEqual([
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

const BUNDLES = fileURLToPath(new URL("../../../../eval/bundles/", import.meta.url));
const bundle = (name: string) => JSON.parse(readFileSync(`${BUNDLES}${name}/report.json`, "utf-8")) as Report;
const FJ03 = "com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf";

describe("how the failure was reproduced (UI demo design, goal 3), on committed bundles", () => {
  it("names a constructed pair, with the pairs tried, for FJ-03 in pair mode (demo step 5)", () => {
    const r = bundle(`20261122T120044Z-${FJ03}`);
    expect(reproducedKind(r)).toBe("pair");
    expect(toView(r).reproduced).toBe(
      "Found in a constructed pair: the polluter ran directly before the victim, after 368 of 524 pairs. " +
        "Pair mode does not run the project's own orders.",
    );
    expect(invocations(r)).toBe(798);
  });

  it("says a given order was given, for a report from before reproduced_by existed", () => {
    const r = bundle(`20261121T162830Z-${FJ03}`);
    expect("reproduced_by" in r).toBe(false);
    expect(reproducedKind(r)).toBe("given order");
    expect(toView(r).reproduced).toBe(
      "The failing order (2 tests) was given with --order. The given order reproduced the failure; no shuffled orders were needed.",
    );
  });

  it("says never, with what was tried, when nothing reproduced", () => {
    const r = bundle(`20261124T151413Z-${FJ03}`);
    expect(reproducedKind(r)).toBe("never");
    expect(toView(r).reproduced).toBe("31 shuffled orders tried (seeds from 0); none reproduced the failure.");
    expect(invocations(r)).toBe(12817);
  });

  it("keeps today's text for an order-mode fixture report", () => {
    expect(reproducedKind(read("f1"))).toBe("order");
    expect(toView(read("f1")).reproduced).toBe("The original order reproduced the failure; no shuffled orders were needed.");
  });

  it("has no invocation count without a budget account", () => {
    const { budget, ...r } = bundle(`20261122T120044Z-${FJ03}`);
    expect(budget).toBeDefined();
    expect(invocations(r as Report)).toBeNull();
  });
});

describe("review fixes (2026-11-27)", () => {
  const step5 = () => bundle(`20261122T120044Z-${FJ03}`);

  it("says the victim failed alone, never 'never reproduced', for a pair-mode victim that fails alone", () => {
    const r = { ...step5(), outcome: "UNRESOLVED", unresolved_reason: "VICTIM_FAILS_ALONE", reproduced_by: "order",
                polluters: [], budget: { ...step5().budget!, candidates: { tried: 0, total: 524 } } } as Report;
    expect(reproducedKind(r)).toBe("order");
    expect(toView(r).reproduced).toBe("The victim failed when run alone; no pairs were run.");
  });

  it("says when the budget stopped a pair search that found nothing", () => {
    const r = { ...step5(), outcome: "UNRESOLVED", unresolved_reason: "BUDGET_EXHAUSTED", reproduced_by: null,
                failure_signature: null, polluters: [],
                budget: { ...step5().budget!, exhausted: true, candidates: { tried: 40, total: 524 } } } as Report;
    expect(toView(r).reproduced).toBe(
      "Never reproduced: no pair failed twice in a row (40 of 524 pairs tried); the budget stopped the search.",
    );
  });
});

describe("deletion checks on the Diagnosis step (A4, 2026-11-27)", () => {
  it("shows each kept test removed for F3, with its runs and status", () => {
    const r = bundle("20261121T184910Z-odfixture.ToggleVictimTest#expectsNotBothFlagsSet");
    expect(toView(r).deletions).toEqual([
      "Removed odfixture.ToggleAPolluterTest#setFlagA: the victim passed 20 of 20 runs without it → NEEDED",
      "Removed odfixture.ToggleBPolluterTest#setFlagB: the victim passed 20 of 20 runs without it → NEEDED",
    ]);
  });

  it("says when the only polluter's check reuses the alone runs", () => {
    expect(toView(bundle(`20261122T120044Z-${FJ03}`)).deletions).toEqual([
      "Removed com.alibaba.json.bvt.serializer.SerializeWriterTest_14#test_writer_1 (the only polluter): the victim alone passed 20 of 20 runs → NEEDED",
    ]);
  });

  it("names a check the budget stopped, and a later round", () => {
    const r = bundle("20261121T184910Z-odfixture.ToggleVictimTest#expectsNotBothFlagsSet");
    const cut = { ...r, deletion_checks: [
      { ...r.deletion_checks![0], status: "NOT_RUN", runs: null },
      { ...r.deletion_checks![1], round: 2 },
    ] } as Report;
    expect(toView(cut).deletions).toEqual([
      "Removed odfixture.ToggleAPolluterTest#setFlagA: not run, the budget ran out → NOT_RUN",
      "Round 2 — removed odfixture.ToggleBPolluterTest#setFlagB: the victim passed 20 of 20 runs without it → NEEDED",
    ]);
  });

  it("has none when no polluter was blamed", () => {
    expect(toView(bundle(`20261124T151413Z-${FJ03}`)).deletions).toEqual([]);
  });
});
