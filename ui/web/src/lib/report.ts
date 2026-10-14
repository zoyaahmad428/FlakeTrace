import { plural } from "./format";

// Mirrors eval/schema/report.schema.json (read-only consumer, ADR-009).
export type TestId = { class: string; method: string };
export type WilsonCount = { successes: number; n: number; confidence: number; lower: number; upper: number };
export type SharedResource = { kind: "static-field"; class: string; field: string } | { kind: "system-property"; key: string };
export type CodeLocation = { class: string; method: string; bytecode_offset: number };
export type FailureSignature = { exception_type: string; message?: string | null; stack_trace: string };
export type OrderExploration = {
  order_given: boolean;
  shuffled_orders_tried: number;
  orders_exhausted: boolean;
  seed_base: number;
  reproducing_seed: number | null;
  infrastructure_failures: number;
};
export type Outcome = "VERIFIED" | "CANDIDATE" | "UNRESOLVED";
export type Report = {
  victim: TestId;
  polluters: TestId[];
  original_failing_order: TestId[];
  reduced_sequence: TestId[];
  reproduction: WilsonCount;
  sequence_any_signature_failures: number;
  victim_alone: WilsonCount;
  shared_resource: SharedResource | null;
  polluter_write_location: CodeLocation | null;
  victim_read_location: CodeLocation | null;
  failure_signature: FailureSignature | null;
  order_exploration?: OrderExploration;
  instrumentation_level: string;
  execution_record_reference: string;
  source_integrity: { passed: boolean; details: string };
  outcome: Outcome;
  unresolved_reason: string | null;
  limitations: string[];
};

const REQUIRED: (keyof Report)[] = [
  "victim", "polluters", "original_failing_order", "reduced_sequence", "reproduction", "sequence_any_signature_failures",
  "victim_alone", "shared_resource", "polluter_write_location", "victim_read_location", "failure_signature",
  "instrumentation_level", "execution_record_reference", "source_integrity", "outcome", "unresolved_reason", "limitations",
];

export const WILSON_FLOOR = 0.7;

const REASON: Record<string, string> = {
  VICTIM_FAILS_ALONE: "the victim also fails when run alone, so no earlier test can be blamed",
  NOT_REPRODUCED: "the failure never reproduced, in the original order or in any shuffled order tried",
  SIGNATURE_MISMATCH: "the sequence failed, but with a different failure than the original",
  INFRASTRUCTURE_FAILURE: "the runs only crashed or timed out; no real failure was observed",
  NO_SUPPORTED_RESOURCE_EVIDENCE: "no shared state of a supported kind (static field or system property) links the polluter to the victim",
  BELOW_CONFIDENCE_THRESHOLD: "the failure does not reproduce reliably enough",
  SOURCE_INTEGRITY_FAILED: "the analysed project's source changed during the run",
};

export type Loc = { at: string; cls: string; offset: number; note: string };

export type ReportView = {
  victim: string;
  outcome: string;
  outcomeTone: "verified" | "candidate" | "unresolved";
  reason: string | null;
  polluters: string[];
  pollutersNote: string;
  originalOrder: string[];
  reducedSequence: string[];
  reproduction: string;
  reproductionBounds: string;
  alone: string;
  aloneBounds: string;
  resource: { name: string; kind: string } | null;
  resourceNote: string;
  write: Loc | null;
  read: Loc | null;
  signature: string;
  stackTrace: string;
  integrity: string;
  integrityPassed: boolean;
  exploration: string;
  instrumentation: string;
  limitations: string[];
};

export const testName = (t: TestId) => `${t.class}#${t.method}`;

export const outcomeText = (r: Report) => (r.outcome === "UNRESOLVED" ? `UNRESOLVED(${r.unresolved_reason})` : r.outcome);

export const outcomeTone = (o: Outcome) => (o === "VERIFIED" ? "verified" : o === "CANDIDATE" ? "candidate" : "unresolved");

export const resourceName = (r: SharedResource) => (r.kind === "static-field" ? `${r.class}.${r.field}` : `System property "${r.key}"`);

const resourceKind = (r: SharedResource) => (r.kind === "static-field" ? "static field" : "system property");

const rate = (c: WilsonCount) => `${c.successes}/${c.n}`;

const bounds = (c: WilsonCount) => `${Math.round(c.confidence * 100)}% Wilson interval [${c.lower.toFixed(3)}, ${c.upper.toFixed(3)}]`;

export function looksLikeReport(x: unknown): boolean {
  return typeof x === "object" && x !== null && !Array.isArray(x) && REQUIRED.every((key) => key in x);
}

function loc(l: CodeLocation | null, owners: TestId[], inside: string, outside: string): Loc | null {
  if (!l) return null;
  const own = owners.some((t) => t.class === l.class && t.method === l.method);
  return { at: `${l.class}#${l.method}`, cls: l.class, offset: l.bytecode_offset, note: own ? inside : outside };
}

function exploration(r: Report): string {
  const e = r.order_exploration;
  if (!e) return "This report does not record how orders were explored.";
  const start = e.order_given ? "The failing order was given with --order. " : "";
  const crashes = e.infrastructure_failures ? ` ${plural(e.infrastructure_failures, "run")} crashed or timed out.` : "";
  if (e.reproducing_seed !== null) {
    return `${start}Reproduced with a shuffled order (seed ${e.reproducing_seed}) after ${plural(e.shuffled_orders_tried, "shuffled order")}.${crashes}`;
  }
  if (e.shuffled_orders_tried === 0) {
    const which = e.order_given ? "given" : "original";
    return r.reproduction.successes > 0
      ? `${start}The ${which} order reproduced the failure; no shuffled orders were needed.${crashes}`
      : `${start}The ${which} order never reproduced the failure; no shuffled orders were tried.${crashes}`;
  }
  const exhausted = e.orders_exhausted ? " Every distinct order was tried." : "";
  return `${start}${plural(e.shuffled_orders_tried, "shuffled order")} tried (seeds from ${e.seed_base}); none reproduced the failure.${exhausted}${crashes}`;
}

export function toView(r: Report): ReportView {
  const reason = r.outcome === "UNRESOLVED" && r.unresolved_reason ? (REASON[r.unresolved_reason] ?? r.unresolved_reason) : null;
  const signature = r.failure_signature;
  return {
    victim: testName(r.victim),
    outcome: outcomeText(r),
    outcomeTone: outcomeTone(r.outcome),
    reason,
    polluters: r.polluters.map(testName),
    pollutersNote: r.polluters.length ? "" : reason ? `No polluter is named: ${reason}.` : "No polluter is named in this report.",
    originalOrder: r.original_failing_order.map(testName),
    reducedSequence: r.reduced_sequence.map(testName),
    reproduction: rate(r.reproduction),
    reproductionBounds: bounds(r.reproduction),
    alone: rate(r.victim_alone),
    aloneBounds: bounds(r.victim_alone),
    resource: r.shared_resource ? { name: resourceName(r.shared_resource), kind: resourceKind(r.shared_resource) } : null,
    resourceNote: r.shared_resource
      ? ""
      : reason
        ? `No shared resource: ${reason}.`
        : "Static analysis found no shared resource of a supported kind (see Limitations on the Certificate step).",
    write: loc(r.polluter_write_location, r.polluters, "written in the polluter test", "written in a method the polluter calls"),
    read: loc(r.victim_read_location, [r.victim], "read in the victim test", "read in a method the victim calls"),
    signature: signature
      ? `${signature.exception_type}${signature.message ? `: ${signature.message}` : ""}`
      : `No failure signature: ${reason ?? "the report has none"}.`,
    stackTrace: signature?.stack_trace ?? "",
    integrity: r.source_integrity.details,
    integrityPassed: r.source_integrity.passed,
    exploration: exploration(r),
    instrumentation: r.instrumentation_level,
    limitations: r.limitations,
  };
}
