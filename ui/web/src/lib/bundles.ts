import { invocations, reproducedKind, testName, type Report, type ReproducedKind } from "./report";

// GET /api/bundles: one committed bundle in eval/bundles/ (ui/server.py list_bundles), not verified yet.
export type BundleEntry = {
  name: string; run_date: string | null; search: string; scope: string | null; policy: string | null;
  seed: number | null; report: Report;
};
export type VerifyResult = { ok: boolean; problem: string | null };

export type BundleRow = {
  name: string; victim: string; outcome: string; reproduced: ReproducedKind; scope: string | null;
  policy: string | null; seed: number | null; polluter: string; invocations: number | "—"; date: string | null;
};

// Design goal 4: committed evidence is never shown as a run made now.
export const committedLabel = (name: string, date: string | null) =>
  `Committed bundle ${name} — pre-run on ${date ?? "an unrecorded date"}, not run now`;

export function bundleRow(e: BundleEntry): BundleRow {
  const r = e.report;
  return {
    name: e.name, victim: testName(r.victim), outcome: r.outcome, reproduced: reproducedKind(r), scope: e.scope,
    policy: e.policy, seed: e.seed, polluter: r.polluters.length ? testName(r.polluters[0]) : "—",
    invocations: invocations(r) ?? "—", date: e.run_date,
  };
}
