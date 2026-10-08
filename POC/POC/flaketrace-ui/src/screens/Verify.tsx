import type { ReactNode } from "react";
import { Circle, CircleCheck, CircleX, LoaderCircle, Play } from "lucide-react";
import { useStore, verifyPassed } from "../state";
import type { RunResult } from "../lib/types";
import { plural } from "../lib/format";
import { Badge, Button, FlowNav, Missing, Panel, ScreenHeader, Status, Terminal } from "../components/ui";

type CheckState = "pending" | "running" | "pass" | "fail";

const ICON: Record<CheckState, ReactNode> = {
  pending: <Circle className="mt-0.5 size-5 shrink-0 text-line-strong" aria-label="Not run" />,
  running: <LoaderCircle className="mt-0.5 size-5 shrink-0 animate-spin text-action" aria-label="Running" />,
  pass: <CircleCheck className="mt-0.5 size-5 shrink-0 text-verified" aria-label="Passed" />,
  fail: <CircleX className="mt-0.5 size-5 shrink-0 text-victim" aria-label="Failed" />,
};

function runState(run: RunResult | undefined, running: boolean, isNext: boolean): CheckState {
  if (run) return run.status === "ok" && run.passed ? "pass" : "fail";
  return running && isNext ? "running" : "pending";
}

function runDetail(run: RunResult | undefined, fallback: string) {
  if (!run) return fallback;
  if (run.status !== "ok") return run.error ?? run.status;
  return `exit ${run.exit_code} across ${plural(run.order?.length ?? 0, "test")}`;
}

export default function VerifyScreen() {
  const { s, set, api, go } = useStore();
  if (!s.patch || s.patch.status !== "ok" || !s.source || !s.analysis || !s.cert) {
    return <Missing title="No patch to verify" action="Go to repair" onAction={() => go("repair")}>Generate a patch on the Repair step first.</Missing>;
  }

  const source = s.source;
  const order = s.cert.order;
  const all = s.analysis.test_methods;
  const v = s.verify;
  const running = v?.status === "running";
  const policyOk = !!s.patch.policy?.every((p) => p[1]);
  const canRun = s.mode === "demo" || !!s.health?.toolchain.can_run_tests;

  async function verify() {
    set({ verify: { status: "running" } });
    const steps: [keyof Omit<NonNullable<typeof v>, "status">, string[]][] = [
      ["order", order],
      ["alone", [s.target]],
      ["full", all],
    ];
    for (const [key, tests] of steps) {
      const r = await api.run(source.path, tests, s.applied);
      set((prev) => ({ verify: { ...(prev.verify ?? { status: "running" }), [key]: r } }));
    }
    set((prev) => ({ verify: prev.verify && { ...prev.verify, status: "done" } }));
  }

  const start = () => verify().catch(() => set((prev) => ({ verify: prev.verify && { ...prev.verify, status: "done" } })));

  const checks: { label: string; state: CheckState; detail: string }[] = [
    { label: "Patch applied", state: s.applied ? "pass" : "fail", detail: s.applied ? "The working tree carries the fix." : "Apply it on the Repair step." },
    { label: "Target passes in the failing order", state: runState(v?.order, running, true), detail: runDetail(v?.order, "Re-runs the certified order.") },
    { label: "Target still passes alone", state: runState(v?.alone, running, !!v?.order), detail: runDetail(v?.alone, "Guards against a fix that breaks isolation.") },
    { label: "Whole module still passes", state: runState(v?.full, running, !!v?.alone), detail: runDetail(v?.full, `All ${all.length} test methods in declared order.`) },
    { label: "No assertion weakened", state: policyOk ? "pass" : "fail", detail: policyOk ? "Every policy check passed." : "A policy check failed on the Repair step." },
  ];

  const done = v?.status === "done";
  const passed = verifyPassed(v) && s.applied && policyOk;

  const outputs: [string, RunResult | undefined][] = [
    ["Certified order", v?.order],
    ["Target alone", v?.alone],
    ["Whole module", v?.full],
  ];

  return (
    <>
      <ScreenHeader index={7} title="Verify">
        A patch that makes the failure disappear is not the same as a patch that fixes it. Every check must pass.
      </ScreenHeader>

      <Panel title="Checks" aside="All must pass" pad={false}>
        <ul>
          {checks.map((c) => (
            <li key={c.label} className="flex items-start gap-3 border-b border-line px-5 py-3 last:border-0">
              {ICON[c.state]}
              <div className="min-w-0">
                <p className={`font-medium ${c.state === "pending" ? "text-ink-2" : "text-ink"}`}>{c.label}</p>
                <p className="text-sm text-ink-3">{c.detail}</p>
              </div>
            </li>
          ))}
        </ul>
        <div className="border-t border-line px-5 py-4">
          <div className="flex flex-wrap items-center gap-3">
            <Button variant="primary" busy={running} disabled={!canRun} onClick={start} icon={<Play className="size-4" aria-hidden />}>
              {running ? "Running" : done ? "Verify again" : "Run verification"}
            </Button>
            {!canRun && <span className="text-sm text-candidate">No JDK on the backend's PATH, so the checks cannot execute.</span>}
          </div>
          {done && (
            <Status state={passed ? "ok" : s.applied ? "error" : "warn"}>
              {passed
                ? "The certified order now passes, the target still passes alone, and nothing else broke."
                : !s.applied
                  ? "The patch is not applied, so the certified order still fails. Apply it on the Repair step and verify again."
                  : "At least one check failed. The patch did not remove the dependence."}
            </Status>
          )}
        </div>
      </Panel>

      {outputs.some(([, r]) => r) && (
        <Panel title="Runner output" className="mt-5">
          <div className="space-y-3">
            {outputs.map(([label, r]) =>
              r ? (
                <details key={label} open={r.status !== "ok" || !r.passed} className="group rounded-lg border border-line">
                  <summary className="flex cursor-pointer list-none items-center gap-3 px-4 py-2.5 font-medium">
                    {label}
                    <Badge tone={r.status === "ok" && r.passed ? "verified" : "victim"} className="ml-auto">
                      {r.status === "ok" ? (r.passed ? "passed" : "failed") : r.status.replace("_", " ")}
                    </Badge>
                  </summary>
                  <div className="border-t border-line p-3">
                    <Terminal text={r.status === "ok" ? r.output ?? "" : r.error ?? r.status} />
                  </div>
                </details>
              ) : null,
            )}
          </div>
        </Panel>
      )}

      <FlowNav back={() => go("repair")} next={() => go("evosuite")} nextLabel="Go to EvoSuite" />
    </>
  );
}
