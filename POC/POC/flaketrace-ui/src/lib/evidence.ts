import type { Access, Analysis, Resource } from "./types";

export const accessKey = (x: Access) => `${x.test}#${x.method}`;

export type EvidencePath = { resource: Resource; write: Access; read: Access };

export function evidencePath(a: Analysis, polluter: string, target: string): EvidencePath | null {
  for (const f of a.findings) {
    const write = f.writers.find((w) => accessKey(w) === polluter && !w.restores);
    const read = f.readers.find((r) => accessKey(r) === target);
    if (write && read) return { resource: f.resource, write, read };
  }
  return null;
}

export type PlannedCandidate = {
  candidate: string;
  rank: number;
  declared: number;
  tier: number;
  evidence: string;
  known: boolean;
};

const TIERS = [
  "Direct unrestored write",
  "Unrestored write through a call",
  "Write restored in teardown",
  "Reads shared state only",
  "No shared-state access",
];

export function rankCandidates(a: Analysis, target: string, knownOrder: string[]): PlannedCandidate[] {
  const rows = a.test_methods
    .filter((m) => m !== target)
    .map((candidate, i) => {
      const writes = a.findings.flatMap((f) => f.writers.filter((w) => accessKey(w) === candidate));
      const reads = a.findings.some((f) => f.readers.some((r) => accessKey(r) === candidate));
      const unrestored = writes.filter((w) => !w.restores);
      const tier = unrestored.some((w) => w.attribution === "direct") ? 0 : unrestored.length ? 1 : writes.length ? 2 : reads ? 3 : 4;
      return { candidate, declared: i + 1, tier, evidence: TIERS[tier], known: knownOrder.includes(candidate), rank: 0 };
    });
  rows.sort((x, y) => Number(y.known) - Number(x.known) || x.tier - y.tier || x.declared - y.declared);
  return rows.map((r, i) => ({ ...r, rank: i + 1 }));
}
