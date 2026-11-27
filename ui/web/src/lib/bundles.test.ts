import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { bundleRow, committedLabel, type BundleEntry } from "./bundles";
import type { Report } from "./report";

const BUNDLES = fileURLToPath(new URL("../../../../eval/bundles/", import.meta.url));
const FJ03 = "com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf";

// Built from the committed files the way ui/server.py list_bundles() builds an entry.
function entry(name: string, search: string): BundleEntry {
  const manifest = JSON.parse(readFileSync(`${BUNDLES}${name}/manifest.json`, "utf-8"));
  const report = JSON.parse(readFileSync(`${BUNDLES}${name}/report.json`, "utf-8")) as Report;
  const p = manifest.parameters;
  return { name, run_date: manifest.run_date, search, scope: p.scope, policy: p.policy, seed: p.seed, report };
}

describe("committed evidence (UI demo design, goal 4)", () => {
  it("labels a committed bundle as pre-run, never as run now", () => {
    expect(committedLabel(`20261122T120044Z-${FJ03}`, "2026-11-22")).toBe(
      `Pre-run on 2026-11-22, not run now — committed bundle 20261122T120044Z-${FJ03}`,
    );
  });

  it("gives the step-5 FJ-03 row its comparison columns", () => {
    expect(bundleRow(entry(`20261122T120044Z-${FJ03}`, "pairs"))).toEqual({
      name: `20261122T120044Z-${FJ03}`, victim: FJ03, outcome: "CANDIDATE", reproduced: "pair", scope: "package",
      policy: "original", seed: 0, polluter: "com.alibaba.json.bvt.serializer.SerializeWriterTest_14#test_writer_1",
      invocations: 798, date: "2026-11-22",
    });
  });

  it("shows a random seed reaching a different certified polluter", () => {
    const row = bundleRow(entry(`20261122T170257Z-${FJ03}`, "pairs"));
    expect([row.policy, row.seed, row.invocations, row.reproduced]).toEqual(["random", 1, 76, "pair"]);
  });

  it("marks the 21-Nov runs as a given order, and the package order run as never", () => {
    expect(bundleRow(entry(`20261121T162830Z-${FJ03}`, "order")).reproduced).toBe("given order");
    const never = bundleRow(entry(`20261124T151413Z-${FJ03}`, "order"));
    expect([never.reproduced, never.polluter, never.invocations]).toEqual(["never", "—", 12817]);
  });
});

describe("review fixes (2026-11-27)", () => {
  it("lists an unreadable bundle as its own row instead of hiding the table", () => {
    const row = bundleRow({ name: "20991231T000000Z-x.Y#z", run_date: null, search: null, scope: null, policy: null,
                            seed: null, report: null, error: "cannot read this bundle" });
    expect([row.reproduced, row.outcome, row.victim]).toEqual(["unreadable", "—", "cannot read this bundle"]);
  });
});
