import { useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { Check, Crosshair, LoaderCircle, Play, SearchX } from "lucide-react";
import { useStore, type ScanRow } from "../state";
import { rankCandidates } from "../lib/evidence";
import { reproduces, sleep } from "../lib/format";
import type { Access, Finding } from "../lib/types";
import { Badge, Button, FlowNav, Missing, Panel, ScreenHeader, Status, TestName } from "../components/ui";

const PHASES = [
  "Index test sources",
  "Find shared mutable state",
  "Resolve writers and readers through calls",
  "Check teardown restoration",
  "Rank candidates by static evidence",
  "Run each candidate before the target",
];

function AccessList({ title, items, target }: { title: string; items: Access[]; target: string }) {
  return (
    <div className="min-w-0">
      <p className="mb-2 text-sm font-medium text-ink-3">{title}</p>
      <ul className="space-y-1.5">
        {items.map((x) => {
          const key = `${x.test}#${x.method}`;
          const write = title === "Writes";
          const border = write ? (x.restores ? "border-l-line-strong" : "border-l-polluter") : key === target ? "border-l-victim" : "border-l-resource/50";
          return (
            <li key={`${key}:${x.line}`} className={`rounded-md border border-l-4 border-line bg-surface px-3 py-2 ${border}`}>
              <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                <TestName fq={key} role={write && !x.restores ? "polluter" : key === target ? "victim" : undefined} />
                {x.restores && <Badge tone="verified">restored in teardown</Badge>}
              </div>
              <p className="mt-0.5 text-sm text-ink-2">
                {x.how} <span className="font-mono text-[0.8rem] text-ink-3">{x.file}:{x.line}</span>
              </p>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

function FindingBlock({ f, target }: { f: Finding; target: string }) {
  const tone = f.severity === "bad" ? "victim" : f.severity === "warn" ? "candidate" : "verified";
  return (
    <div className="border-b border-line px-5 py-5 last:border-0">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
        <code className="font-mono text-[1.05rem] font-semibold text-resource">{f.resource.id}</code>
        <Badge tone={tone}>{f.verdict}</Badge>
        <span className="text-sm text-ink-3">
          {f.resource.type}, declared at {f.resource.declared_at}
        </span>
      </div>
      <p className="mt-1 text-ink-2">{f.summary}.</p>
      <div className="mt-4 grid gap-5 md:grid-cols-2">
        <AccessList title="Writes" items={f.writers} target={target} />
        <AccessList title="Reads" items={f.readers} target={target} />
      </div>
    </div>
  );
}

export default function DiagnosisScreen() {
  const { s, set, api, go } = useStore();
  const [phase, setPhase] = useState(-1);
  const a = s.analysis;
  if (!a || !s.source || !s.target) return <Missing title="No target chosen" action="Pick the failing test" onAction={() => go("target")}>Choose a target test first.</Missing>;

  const plan = rankCandidates(a, s.target, s.order);
  const rows = s.scan ?? [];
  const running = !!s.scan && !s.scanDone && !s.scanError;
  const current = s.scanDone ? PHASES.length : running ? Math.max(phase, 0) : phase;
  const first = rows.find((r) => r.reproduced);
  const byDeclared = [...rows].sort((x, y) => x.declared - y.declared).findIndex((r) => r.reproduced) + 1;
  const source = s.source;
  const target = s.target;

  async function run() {
    set({ scan: [], scanDone: false, scanError: null, cert: null, verify: null });
    for (let i = 0; i < PHASES.length - 1; i++) {
      setPhase(i);
      await sleep(300);
    }
    setPhase(PHASES.length - 1);
    const done: ScanRow[] = [];
    for (const p of plan) {
      const result = await api.run(source.path, [p.candidate, target], false);
      if (result.status !== "ok") {
        set({ scanError: result.error ?? `The runner returned ${result.status}.` });
        return;
      }
      done.push({ ...p, result, reproduced: reproduces(result.output, target) });
      set({ scan: [...done] });
    }
    set({ scanDone: true });
  }

  const start = () => run().catch((e: Error) => set({ scanError: e.message }));

  return (
    <>
      <ScreenHeader index={3} title="Diagnosis">
        FlakeTrace reads every test source and follows calls into production code. Then it runs each candidate before the target to see which one breaks it.
      </ScreenHeader>

      <Panel title="Run" aside={<TestName fq={s.target} role="victim" />}>
        <div className="grid gap-6 md:grid-cols-[minmax(0,1fr)_auto] md:items-start">
          <ol className="space-y-2">
            {PHASES.map((label, i) => {
              const state = i < current ? "done" : i === current && running ? "on" : "wait";
              return (
                <li key={label} className={`flex items-center gap-3 ${state === "wait" ? "text-ink-3" : "text-ink"}`}>
                  <span
                    className={`grid size-6 shrink-0 place-items-center rounded-full border-2 transition-colors ${
                      state === "done" ? "border-verified bg-verified text-white" : state === "on" ? "border-action text-action" : "border-line-strong"
                    }`}
                  >
                    {state === "done" ? <Check className="size-3.5" strokeWidth={3} aria-hidden /> : state === "on" ? <LoaderCircle className="size-3.5 animate-spin" aria-hidden /> : null}
                  </span>
                  <span className={state === "on" ? "font-medium" : ""}>{label}</span>
                  {i === PHASES.length - 1 && (running || s.scanDone) && (
                    <span className="ml-auto text-sm text-ink-3 tabular">
                      {rows.length} of {plan.length}
                    </span>
                  )}
                </li>
              );
            })}
          </ol>
          <Button variant="primary" onClick={start} busy={running} icon={<Play className="size-4" aria-hidden />}>
            {running ? "Running" : s.scanDone || s.scanError ? "Run again" : "Start diagnosis"}
          </Button>
        </div>
        <div className="mt-5 h-1.5 overflow-hidden rounded-full bg-sunken">
          <motion.div
            className="h-full origin-left rounded-full bg-linear-to-r from-polluter via-resource to-victim"
            initial={false}
            animate={{ scaleX: s.scanDone ? 1 : running ? (Math.max(phase, 0) + (plan.length ? rows.length / plan.length : 0)) / PHASES.length : 0 }}
            transition={{ type: "spring", stiffness: 120, damping: 24 }}
          />
        </div>
        {s.scanError && <Status state="error">{s.scanError}</Status>}
      </Panel>

      {s.scanDone && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="mt-5 rounded-xl border border-line bg-surface p-5">
          <div className="flex items-start gap-4">
            <div className={`grid size-11 shrink-0 place-items-center rounded-full ${first ? "bg-victim-soft text-victim" : "bg-unresolved-soft text-unresolved"}`}>
              {first ? <Crosshair className="size-5" aria-hidden /> : <SearchX className="size-5" aria-hidden />}
            </div>
            <div className="min-w-0">
              <p className="text-xl font-semibold leading-snug">
                {first ? (
                  <>
                    <TestName fq={first.candidate} role="polluter" /> breaks the target
                  </>
                ) : (
                  "No candidate broke the target"
                )}
              </p>
              <p className="mt-1 text-ink-2">
                {first
                  ? first.rank === byDeclared
                    ? `It was candidate ${first.rank} both by static ranking and in declared order.`
                    : `Ranked by static evidence it was candidate ${first.rank}. In declared order it would have been candidate ${byDeclared}.`
                  : "Every candidate ran before the target and the target still passed. The certificate will abstain."}
              </p>
            </div>
          </div>
          <dl className="mt-4 flex flex-wrap gap-x-8 gap-y-3 border-t border-line pt-4">
            {[
              ["Test classes", a.counts.test_classes],
              ["Test methods", a.counts.test_methods],
              ["Shared static fields", a.counts.shared_statics],
              ["Candidate orders run", rows.length],
              ["Invocations spent", rows.length * 2],
            ].map(([k, v]) => (
              <div key={k}>
                <dt className="text-sm text-ink-3">{k}</dt>
                <dd className="text-lg font-semibold tabular">{v}</dd>
              </div>
            ))}
          </dl>
        </motion.div>
      )}

      {s.scan && (
        <Panel title="Candidate scan" aside={`${rows.length} of ${plan.length} orders run`} pad={false} className="mt-5">
          <div className="scrollbar-thin overflow-x-auto">
            <table className="w-full min-w-[680px] text-left text-[0.93rem]">
              <thead className="border-b border-line bg-sunken/70 text-sm text-ink-3">
                <tr>
                  <th scope="col" className="px-5 py-2.5 font-medium">Rank</th>
                  <th scope="col" className="py-2.5 pr-4 font-medium">Order run</th>
                  <th scope="col" className="py-2.5 pr-4 font-medium">Static evidence</th>
                  <th scope="col" className="py-2.5 pr-5 text-right font-medium">Target</th>
                </tr>
              </thead>
              <tbody>
                <AnimatePresence initial={false}>
                  {plan.map((p) => {
                    const r = rows.find((x) => x.candidate === p.candidate);
                    return (
                      <motion.tr
                        key={p.candidate}
                        initial={false}
                        animate={{ backgroundColor: r?.reproduced ? "#fdebef" : "#ffffff", opacity: r ? 1 : 0.5 }}
                        transition={{ duration: 0.25 }}
                        className="border-b border-line last:border-0"
                      >
                        <td className="px-5 py-3 text-ink-3 tabular">{p.rank}</td>
                        <td className="py-3 pr-4">
                          <TestName fq={p.candidate} role={r?.reproduced ? "polluter" : undefined} /> <span className="text-ink-3">then</span>{" "}
                          <TestName fq={s.target} role="victim" />
                        </td>
                        <td className="py-3 pr-4 text-ink-2">
                          {p.evidence}
                          {p.known && (
                            <Badge tone="action" className="ml-2">
                              in your order
                            </Badge>
                          )}
                        </td>
                        <td className="py-3 pr-5 text-right">
                          {!r ? (
                            <span className="text-sm text-ink-3">{running ? "Queued" : "Not run"}</span>
                          ) : r.reproduced ? (
                            <Badge tone="victim">Fails</Badge>
                          ) : (
                            <Badge tone="neutral">Passes</Badge>
                          )}
                        </td>
                      </motion.tr>
                    );
                  })}
                </AnimatePresence>
              </tbody>
            </table>
          </div>
        </Panel>
      )}

      {s.scanDone && (
        <Panel title="Shared state" aside="Read from source, not executed" pad={false} className="mt-5">
          {a.findings.length ? (
            a.findings.map((f) => <FindingBlock key={f.resource.id} f={f} target={s.target} />)
          ) : (
            <p className="px-5 py-6 text-ink-3">No mutable static fields were found, so there is nothing for an order dependence to travel through.</p>
          )}
        </Panel>
      )}

      <FlowNav back={() => go("target")} next={() => go("result")} nextLabel="Open the certificate" nextDisabled={!s.scanDone} hint="Run the diagnosis to continue." />
    </>
  );
}
