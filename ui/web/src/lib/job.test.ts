import { describe, expect, it } from "vitest";
import { finishedRunLoad, keepsWhatIsOpen } from "./job";
import type { Job } from "./api";

const report = { outcome: "VERIFIED" } as never;
const job = (patch: Partial<Job> = {}): Job =>
  ({ id: "j", state: "done", started: "", command: "", report, report_path: "C:/r/run.report.json", ...patch }) as Job;

describe("a finished live run (review fixes 4 and 9, 2026-11-27)", () => {
  it("carries its bundle's verify result into the Certificate step", () => {
    const loaded = finishedRunLoad(job({ bundle: { path: "C:/r/bundles/run", verify: { ok: true, problem: null } } }));
    expect(loaded.verify).toEqual({ ok: true, problem: null });
    expect(loaded.from).toBe("Live run: C:/r/run.report.json · bundle: C:/r/bundles/run");
  });

  it("has no verify result without a bundle", () => {
    expect(finishedRunLoad(job()).verify).toBeUndefined();
  });

  it("does not replace a report the presenter opened while the run was going", () => {
    expect(keepsWhatIsOpen({ jobStartedAt: 1000, loadedAt: 2000 })).toBe(true);
    expect(keepsWhatIsOpen({ jobStartedAt: 2000, loadedAt: 1000 })).toBe(false);
    expect(keepsWhatIsOpen({ jobStartedAt: 2000, loadedAt: null })).toBe(false);
  });
});
