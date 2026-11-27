import { invocations, reproducedKind, testName, type Report, type ReproducedKind } from "./report";

// GET /api/bundles: one committed bundle in eval/bundles/ (ui/server.py list_bundles), not verified yet.
export type BundleEntry = {
  name: string; run_date: string | null; search: string | null; scope: string | null; policy: string | null;
  seed: number | null; report: Report | null; error?: string | null;
};
export type VerifyResult = { ok: boolean; problem: string | null };

export type BundleRow = {
  name: string; victim: string; outcome: string; reproduced: ReproducedKind | "unreadable"; scope: string | null;
  policy: string | null; seed: number | null; polluter: string; invocations: number | "—"; date: string | null;
};

// Design goal 4: committed evidence is never shown as a run made now.
// "Pre-run" first, so a narrow header that cuts the line still keeps it (review, 2026-11-27).
export const committedLabel = (name: string, date: string | null) =>
  `Pre-run on ${date ?? "an unrecorded date"}, not run now — committed bundle ${name}`;

export function bundleRow(e: BundleEntry): BundleRow {
  const r = e.report;
  if (!r) {
    // A bundle the server could not read stays in the table, with the reason (review, 2026-11-27).
    return { name: e.name, victim: e.error ?? "unreadable", outcome: "—", reproduced: "unreadable", scope: e.scope,
             policy: e.policy, seed: e.seed, polluter: "—", invocations: "—", date: e.run_date };
  }
  return {
    name: e.name, victim: testName(r.victim), outcome: r.outcome, reproduced: reproducedKind(r), scope: e.scope,
    policy: e.policy, seed: e.seed, polluter: r.polluters.length ? testName(r.polluters[0]) : "—",
    invocations: invocations(r) ?? "—", date: e.run_date,
  };
}
