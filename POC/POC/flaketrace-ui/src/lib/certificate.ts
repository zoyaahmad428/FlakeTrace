export type Decision = "verified" | "candidate" | "unresolved";
export type Abstention = "unsupported_resource" | "budget_exhausted" | "unstable_build" | "inconsistent_outcomes";

export const ABSTENTION: Record<Abstention, { title: string; next: string }> = {
  unsupported_resource: {
    title: "Unsupported resource",
    next: "The state lives outside static fields, system properties and file paths. Inspect it by hand.",
  },
  budget_exhausted: {
    title: "Budget exhausted",
    next: "The search stopped before any order met the acceptance rule. Raise the budget and run again.",
  },
  unstable_build: {
    title: "Unstable build",
    next: "The target did not pass consistently on its own, so no measurement here can be trusted. Stabilise the build first.",
  },
  inconsistent_outcomes: {
    title: "Inconsistent outcomes",
    next: "The same order gave conflicting results. The test is likely nondeterministic rather than order-dependent.",
  },
};

export const DECISION: Record<Decision, { label: string; tone: "verified" | "candidate" | "unresolved" }> = {
  verified: { label: "Verified", tone: "verified" },
  candidate: { label: "Candidate", tone: "candidate" },
  unresolved: { label: "Unresolved", tone: "unresolved" },
};

export const MATCH_FRACTION = 0.9;

export const totalCost = (lines: CostLine[]) => lines.reduce((n, l) => n + l.invocations, 0);

export function wilson(k: number, n: number, z = 1.96): [number, number] {
  if (n === 0) return [0, 1];
  const p = k / n;
  const z2 = z * z;
  const d = 1 + z2 / n;
  const centre = (p + z2 / (2 * n)) / d;
  const half = (z * Math.sqrt((p * (1 - p)) / n + z2 / (4 * n * n))) / d;
  return [Math.max(0, centre - half), Math.min(1, centre + half)];
}

export type CostLine = { label: string; invocations: number };

export function costModel(o: { candidates: number; controls: number; replays: number; orderLength: number }): CostLine[] {
  return [
    { label: "Candidate scan", invocations: o.candidates * 2 },
    { label: "Isolation controls", invocations: o.controls },
    { label: "Verification replays", invocations: o.replays * o.orderLength },
    { label: "Deletion checks", invocations: Math.max(1, o.orderLength - 1) },
  ];
}

export type CertInput = {
  budget: number;
  cost: number;
  polluterFound: boolean;
  controls: number;
  controlsPassed: number;
  replays: number;
  reproduced: number;
  threshold: number;
  deletionMinimal: boolean;
  resourceSupported: boolean;
};

export type Check = { label: string; ok: boolean; detail: string };

export type CertOutcome = {
  decision: Decision;
  reason?: Abstention;
  rationale: string;
  interval: [number, number];
  checks: Check[];
};

export function decide(i: CertInput): CertOutcome {
  const interval = wilson(i.reproduced, i.replays);
  const needed = Math.ceil(MATCH_FRACTION * i.replays);
  const checks: Check[] = [
    { label: "Within budget", ok: i.cost <= i.budget, detail: `${i.cost} of ${i.budget} invocations` },
    { label: "Target passes alone", ok: i.controlsPassed === i.controls, detail: `${i.controlsPassed} of ${i.controls} control runs` },
    { label: "Replay threshold met", ok: i.reproduced >= needed, detail: `${i.reproduced} of ${i.replays} reproduced, ${needed} needed` },
    {
      label: "Wilson lower bound",
      ok: interval[0] >= i.threshold,
      detail: `${interval[0].toFixed(2)} against a floor of ${i.threshold.toFixed(2)}`,
    },
    { label: "Deletion-minimal order", ok: i.deletionMinimal, detail: i.deletionMinimal ? "removing the polluter makes the target pass" : "a shorter order still fails" },
    { label: "Resource in a supported family", ok: i.resourceSupported, detail: i.resourceSupported ? "static field" : "outside the committed families" },
  ];

  if (i.cost > i.budget || !i.polluterFound) {
    return {
      decision: "unresolved",
      reason: "budget_exhausted",
      interval,
      checks,
      rationale: i.polluterFound
        ? `The plan needs ${i.cost} invocations but the budget allows ${i.budget}, so verification could not be reserved.`
        : "Every candidate ran without reproducing the failure. A deeper search needs more budget.",
    };
  }
  if (i.controlsPassed < i.controls) {
    return {
      decision: "unresolved",
      reason: "unstable_build",
      interval,
      checks,
      rationale: `The target failed ${i.controls - i.controlsPassed} of ${i.controls} times with nothing run before it.`,
    };
  }
  if (i.reproduced < needed || interval[0] < i.threshold) {
    return {
      decision: "unresolved",
      reason: "inconsistent_outcomes",
      interval,
      checks,
      rationale: `The order reproduced the failure ${i.reproduced} of ${i.replays} times, short of the acceptance rule.`,
    };
  }
  if (!i.deletionMinimal || !i.resourceSupported) {
    return {
      decision: "candidate",
      interval,
      checks,
      rationale: "The order replays reliably, but the evidence path does not reach a supported resource. FlakeTrace can tell you what to run, not why it fails.",
    };
  }
  return {
    decision: "verified",
    interval,
    checks,
    rationale: "The order replays above threshold, is deletion-minimal, and the write-to-read path runs through a static field.",
  };
}
