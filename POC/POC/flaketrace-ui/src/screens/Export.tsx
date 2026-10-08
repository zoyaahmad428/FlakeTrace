import { useMemo } from "react";
import { Download } from "lucide-react";
import { SCENARIOS, activeScenario, useStore, verifyPassed, type State } from "../state";
import { totalCost } from "../lib/certificate";
import { evidencePath } from "../lib/evidence";
import { jdkVersion } from "../lib/format";
import { Button, CopyButton, FlowNav, Missing, Panel, ScreenHeader } from "../components/ui";

const round = (n: number) => Math.round(n * 1000) / 1000;

function buildRecord(s: State) {
  const cert = s.cert;
  const outcome = cert?.outcome;
  const scenario = activeScenario(s);
  const path = s.analysis && cert?.polluter ? evidencePath(s.analysis, cert.polluter, s.target) : null;
  const k = cert?.replays.filter(Boolean).length ?? 0;
  const n = cert?.replays.length ?? 0;

  return {
    tool: "FlakeTrace",
    format: "certificate, prototype",
    generated: new Date().toISOString(),
    provenance:
      s.mode === "live"
        ? "live backend"
        : scenario === "planted"
          ? "offline demo: recorded runs of the bundled project; repetitions reuse the recorded outcome"
          : `offline demo: simulated scenario "${SCENARIOS.find((x) => x.value === scenario)?.title}"`,
    case: {
      repository: s.source?.name ?? null,
      path: s.source?.path ?? null,
      commit: s.git?.sha_full ?? null,
      branch: s.git?.branch ?? null,
      module: s.source?.module ?? null,
      jdk: jdkVersion(s.health?.toolchain.java),
      target: s.target,
      failure_signature: cert?.signature ?? null,
    },
    classification: outcome && outcome.decision !== "unresolved" ? "victim" : null,
    decision: outcome ? { class: outcome.decision, reason: outcome.reason ?? null, rationale: outcome.rationale } : null,
    replay_order: cert?.polluter
      ? { tests: cert.order, minimality: "deletion-minimal (1-minimal)", command: cert.polluting?.command ?? null }
      : null,
    counterfactual_checks:
      cert && n
        ? [
            { order: [s.target], expected: "pass", observed: `${cert.controls.filter(Boolean).length}/${cert.controls.length} passed` },
            { order: cert.order, expected: "fail", observed: `${k}/${n} reproduced` },
          ]
        : [],
    resource_evidence: path
      ? {
          family: cert?.resourceSupported ? "static field" : "not observed",
          resource: path.resource.id,
          write: { test: `${path.write.test}#${path.write.method}`, at: `${path.write.file}:${path.write.line}`, how: path.write.how, attribution: path.write.attribution },
          read: { test: `${path.read.test}#${path.read.method}`, at: `${path.read.file}:${path.read.line}`, how: path.read.how, attribution: path.read.attribution },
        }
      : null,
    reliability:
      outcome && n
        ? {
            replays: n,
            reproduced: k,
            rate: round(k / n),
            wilson_95: [round(outcome.interval[0]), round(outcome.interval[1])],
            lower_bound_floor: s.threshold,
            controls: { runs: cert!.controls.length, passed: cert!.controls.filter(Boolean).length },
          }
        : null,
    budget: cert
      ? { declared: s.budget, planned_invocations: totalCost(cert.cost), lines: cert.cost, maven_launches: 0, wall_time_ms: cert.wallMs }
      : { declared: s.budget },
    repair:
      s.patch?.status === "ok"
        ? {
            file: s.patch.file,
            strategy: s.patch.strategy,
            added_lines: s.patch.added_lines,
            applied: s.applied,
            policy_passed: `${s.patch.policy?.filter((p) => p[1]).length}/${s.patch.policy?.length}`,
          }
        : null,
    verification:
      s.verify?.status === "done"
        ? { certified_order_passes: !!s.verify.order?.passed, target_alone_passes: !!s.verify.alone?.passed, module_passes: !!s.verify.full?.passed, all_passed: verifyPassed(s.verify) }
        : null,
    evosuite: s.evo ? { status: s.evo.status, target: s.evo.target_class, command: s.evo.command } : null,
    limitations: [
      "Reflective and native writes are invisible to source analysis",
      "One resource at a time",
      "Replays ran in one JVM through the harness, not a clean container",
      "The Wilson interval describes replay reliability, not the probability the diagnosis is correct",
    ],
  };
}

function JsonView({ text }: { text: string }) {
  const parts = text.split(/("(?:\\.|[^"\\])*"(?:\s*:)?|\b(?:true|false|null)\b|-?\d+(?:\.\d+)?)/g);
  return (
    <pre className="scrollbar-thin max-h-[560px] overflow-auto bg-sunken/60 px-5 py-4 font-mono text-[0.82rem] leading-6 text-ink-2">
      {parts.map((p, i) => {
        if (!p) return null;
        if (p.startsWith('"')) return <span key={i} className={p.endsWith(":") ? "text-action" : "text-resource"}>{p}</span>;
        if (/^(true|false|null)$/.test(p)) return <span key={i} className="font-medium text-polluter">{p}</span>;
        if (/^-?\d/.test(p)) return <span key={i} className="text-candidate">{p}</span>;
        return p;
      })}
    </pre>
  );
}

export default function ExportScreen() {
  const { s, go } = useStore();
  const text = useMemo(() => JSON.stringify(buildRecord(s), null, 2), [s]);
  if (!s.cert) return <Missing title="Nothing to export" action="Open the certificate" onAction={() => go("result")}>Issue a certificate first.</Missing>;

  const download = () => {
    const url = URL.createObjectURL(new Blob([text], { type: "application/json" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = `flaketrace-${s.git?.sha ?? "case"}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <>
      <ScreenHeader index={9} title="Export">
        The certificate as machine-readable JSON. Every field comes from what this session ran and read.
      </ScreenHeader>

      <Panel
        title="Case record"
        aside={
          <span className="flex items-center gap-1">
            <CopyButton text={text} label="Copy JSON" />
            <Button size="sm" variant="ghost" onClick={download} icon={<Download className="size-4" aria-hidden />}>
              Download
            </Button>
          </span>
        }
        pad={false}
      >
        <JsonView text={text} />
      </Panel>

      <FlowNav back={() => go("evosuite")} next={() => go("source")} nextLabel="Start another case" />
    </>
  );
}
