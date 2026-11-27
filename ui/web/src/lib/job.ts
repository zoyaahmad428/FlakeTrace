import type { Job } from "./api";
import type { VerifyResult } from "./bundles";
import type { Report } from "./report";

// `verify`: eval.bundle's own check, run when a committed bundle is opened or a run wrote one (UI demo design).
export type Loaded = { report: Report; from: string; validated: boolean; verify?: VerifyResult };

export function finishedRunLoad(job: Job): Loaded {
  const bundle = job.bundle ? ` · bundle: ${job.bundle.path}` : "";
  return { report: job.report!, from: `Live run: ${job.report_path}${bundle}`, validated: true, verify: job.bundle?.verify };
}

// A run that finishes while the presenter shows something they opened after starting it must not replace that view
// (review, 2026-11-27); the Target step offers the run's report instead.
export const keepsWhatIsOpen = (s: { jobStartedAt: number | null; loadedAt: number | null }) =>
  s.jobStartedAt !== null && s.loadedAt !== null && s.loadedAt > s.jobStartedAt;
