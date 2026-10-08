import { useState } from "react";
import { CircleCheck, CircleMinus, CircleX } from "lucide-react";
import { useStore } from "../state";
import { evoCommand } from "../lib/api";
import { evidencePath } from "../lib/evidence";
import { simpleClass } from "../lib/format";
import type { EvoParams } from "../lib/types";
import { Badge, Button, CopyButton, Field, FlowNav, Missing, Panel, ScreenHeader, Status, Switch, Terminal, inputClass, type StatusState } from "../components/ui";

const CRITERIA = [
  ["branch:line:exception", "Branch, line, exception"],
  ["branch:line", "Branch, line"],
  ["branch:line:exception:method:output", "Plus method and output"],
  ["mutation:branch:line", "Mutation, branch, line"],
];

const ASSERTIONS = [
  ["mutation", "Mutation-filtered"],
  ["all", "All observed"],
  ["structured", "Structured"],
];

const FIT = [
  { Icon: CircleCheck, tone: "text-verified", title: "Pins behaviour after a repair", text: "Locks in what the fixed class does." },
  { Icon: CircleMinus, tone: "text-ink-3", title: "Targets a class, not an interaction", text: "Order dependence lives between tests, so a per-class generator cannot see it." },
  { Icon: CircleMinus, tone: "text-ink-3", title: "Freezes current behaviour", text: "Including behaviour that is wrong, so the suite is proposed for review." },
  { Icon: CircleX, tone: "text-victim", title: "Never evidence for the diagnosis", text: "A generated test passing says nothing about the cause." },
];

export default function EvoSuiteScreen() {
  const { s, set, api, go } = useStore();
  const a = s.analysis;
  const path = a && s.cert?.polluter ? evidencePath(a, s.cert.polluter, s.target) : null;
  const [p, setP] = useState<EvoParams>(() => ({
    targetClass: s.evo?.target_class ?? path?.resource.owner_fqcn ?? a?.findings[0]?.resource.owner_fqcn ?? a?.test_classes[0] ?? "",
    searchBudget: "60",
    seed: "1",
    criteria: "branch:line:exception",
    assertionStrategy: "mutation",
    deterministic: true,
  }));
  const [busy, setBusy] = useState<"" | "check" | "run">("");
  const [status, setStatus] = useState<{ state: StatusState; msg: string }>({ state: "idle", msg: "Nothing run yet." });

  if (!s.source || !a) return <Missing title="No project loaded" action="Choose a project" onAction={() => go("source")}>Load a project first.</Missing>;

  const source = s.source;
  const tool = s.evo?.toolchain ?? s.health?.toolchain;
  const testDir = `${source.path}/${source.module}/src/test/java`;
  const command = evoCommand(p, tool, testDir);
  const update = (patch: Partial<EvoParams>) => setP((cur) => ({ ...cur, ...patch }));

  async function call(execute: boolean) {
    setBusy(execute ? "run" : "check");
    setStatus({ state: "busy", msg: execute ? "Running EvoSuite…" : "Checking the toolchain and classpath…" });
    try {
      const d = await api.evosuite(source.path, source.module, p, execute);
      set({ evo: d });
      if (d.status === "ok") setStatus({ state: "ok", msg: `Generated ${d.generated_files?.length ?? 0} file(s) into ${d.test_dir}.` });
      else if (d.status === "ready") setStatus({ state: "ok", msg: "The toolchain is ready. Generate runs the command below." });
      else if (d.status === "unavailable") setStatus({ state: "warn", msg: `${d.error}. The command below is what would run.` });
      else setStatus({ state: d.status === "not_compiled" ? "warn" : "error", msg: d.error ?? d.status });
    } catch (e) {
      setStatus({ state: "error", msg: (e as Error).message });
    } finally {
      setBusy("");
    }
  }

  const facts: [string, React.ReactNode, string][] = [
    ["Class under test", <code key="c" className="font-mono">{simpleClass(p.targetClass) || "none"}</code>, path ? "Owner of the certified resource" : "From the analysis"],
    ["Suite", <code key="s" className="font-mono">{simpleClass(p.targetClass)}_ESTest</code>, s.evo?.generated_files?.length ? `${s.evo.generated_files.length} file(s) written` : "Not generated"],
    [
      "Toolchain",
      tool?.can_run_evosuite ? <span key="t" className="text-verified">Ready</span> : <span key="t" className="text-candidate">EvoSuite jar missing</span>,
      tool?.can_run_evosuite ? tool.evosuite_jar : "Set EVOSUITE_JAR to enable",
    ],
  ];

  return (
    <>
      <ScreenHeader index={8} title="EvoSuite generation">
        Search-based generation of a JUnit suite for one class. It documents behaviour; it does not find polluters.
      </ScreenHeader>

      {!s.evoOn && (
        <Status state="idle" className="mb-5">
          This stage is off in your Target settings. You can still build the command here.
        </Status>
      )}

      <div className="mb-5 grid gap-px overflow-hidden rounded-xl border border-line bg-line sm:grid-cols-3">
        {facts.map(([label, value, sub]) => (
          <div key={label} className="min-w-0 bg-surface px-5 py-4">
            <p className="text-sm text-ink-3">{label}</p>
            <p className="mt-1 text-lg font-semibold [overflow-wrap:anywhere]">{value}</p>
            <p className="text-sm text-ink-3 [overflow-wrap:anywhere]">{sub}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
        <Panel title="Configure">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="sm:col-span-2">
              <Field label="Class" htmlFor="evo-class">
                <input id="evo-class" className={inputClass} value={p.targetClass} onChange={(e) => update({ targetClass: e.target.value })} spellCheck={false} />
              </Field>
            </div>
            <Field label="Search budget, seconds" htmlFor="evo-budget">
              <input id="evo-budget" className={inputClass} inputMode="numeric" value={p.searchBudget} onChange={(e) => update({ searchBudget: e.target.value.replace(/\D/g, "") })} />
            </Field>
            <Field label="Seed" htmlFor="evo-seed">
              <input id="evo-seed" className={inputClass} inputMode="numeric" value={p.seed} onChange={(e) => update({ seed: e.target.value.replace(/\D/g, "") })} />
            </Field>
            <Field label="Coverage criteria" htmlFor="evo-crit">
              <select id="evo-crit" className={`${inputClass} font-sans`} value={p.criteria} onChange={(e) => update({ criteria: e.target.value })}>
                {CRITERIA.map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Assertions" htmlFor="evo-assert">
              <select id="evo-assert" className={`${inputClass} font-sans`} value={p.assertionStrategy} onChange={(e) => update({ assertionStrategy: e.target.value })}>
                {ASSERTIONS.map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </Field>
            <div className="sm:col-span-2">
              <Switch checked={p.deterministic} onChange={(v) => update({ deterministic: v })} label="Reject non-deterministic tests" description="Drops cases that read the clock, network, filesystem or unseeded randomness." />
            </div>
          </div>

          <div className="mt-5 flex flex-wrap gap-3">
            <Button busy={busy === "check"} disabled={busy === "run"} onClick={() => call(false)}>
              Check toolchain
            </Button>
            <Button variant="primary" busy={busy === "run"} disabled={busy === "check" || !p.targetClass} onClick={() => call(true)}>
              Generate suite
            </Button>
          </div>
          <Status state={status.state}>{status.msg}</Status>

          <div className="mt-5">
            <div className="mb-2 flex items-center gap-2">
              <span className="text-sm font-medium text-ink-2">Command</span>
              {s.mode === "demo" && <Badge tone="action">Built in the browser</Badge>}
              <span className="ml-auto">
                <CopyButton text={s.evo?.command ?? command} />
              </span>
            </div>
            <Terminal text={s.evo?.command ?? command} wrap />
          </div>
        </Panel>

        <Panel title="Where it helps, where it does not" pad={false}>
          <ul>
            {FIT.map((f) => (
              <li key={f.title} className="flex items-start gap-3 border-b border-line px-5 py-3.5 last:border-0">
                <f.Icon className={`mt-0.5 size-5 shrink-0 ${f.tone}`} aria-hidden />
                <div>
                  <p className="font-medium">{f.title}</p>
                  <p className="text-sm text-ink-3">{f.text}</p>
                </div>
              </li>
            ))}
          </ul>
        </Panel>
      </div>

      <FlowNav back={() => go(s.patch?.status === "ok" ? "verify" : "repair")} next={() => go("export")} nextLabel="Export the case" />
    </>
  );
}
