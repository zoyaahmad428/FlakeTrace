import { Reorder, motion } from "motion/react";
import { ChevronDown, ChevronUp, GripVertical, Lightbulb, X } from "lucide-react";
import { SCENARIOS, planCost, useStore } from "../state";
import { totalCost, type CostLine } from "../lib/certificate";
import { methodName, shortName } from "../lib/format";
import { Badge, Field, FlowNav, Missing, Panel, ScreenHeader, Segmented, Switch, TestName, inputClass } from "../components/ui";

const SHADES = ["bg-ink-2", "bg-ink-3", "bg-action", "bg-line-strong"];

function BudgetMeter({ lines, budget }: { lines: CostLine[]; budget: number }) {
  const total = totalCost(lines);
  const scale = Math.max(total, budget);
  const over = total > budget;
  return (
    <div className="mt-4">
      <div className="relative">
        <div className="flex h-3 overflow-hidden rounded-full bg-sunken ring-1 ring-line">
          {lines.map((l, i) => (
            <motion.div
              key={l.label}
              className={SHADES[i]}
              initial={false}
              animate={{ width: `${(l.invocations / scale) * 100}%` }}
              transition={{ type: "spring", stiffness: 220, damping: 30 }}
            />
          ))}
        </div>
        <motion.span
          aria-hidden
          className={`absolute -top-1.5 h-6 w-[3px] -translate-x-1/2 rounded-full ${over ? "bg-candidate" : "bg-ink"}`}
          initial={false}
          animate={{ left: `${(budget / scale) * 100}%` }}
          transition={{ type: "spring", stiffness: 220, damping: 30 }}
        />
      </div>
      <ul className="mt-3 grid gap-x-5 gap-y-1 text-sm sm:grid-cols-2">
        {lines.map((l, i) => (
          <li key={l.label} className="flex items-center gap-2">
            <span className={`size-2.5 rounded-sm ${SHADES[i]}`} aria-hidden />
            <span className="text-ink-2">{l.label}</span>
            <span className="ml-auto font-mono tabular">{l.invocations}</span>
          </li>
        ))}
      </ul>
      <p className={`mt-3 text-[0.93rem] ${over ? "font-medium text-candidate" : "text-ink-2"}`}>
        {over
          ? `Too small. The plan needs ${total} invocations, so the certificate will abstain with Budget exhausted.`
          : `The plan needs ${total} of ${budget} invocations. Verification is reserved before the search spends anything.`}
      </p>
    </div>
  );
}

export default function TargetScreen() {
  const { s, set, go } = useStore();
  const a = s.analysis;
  if (!a) return <Missing title="No project loaded" action="Choose a project" onAction={() => go("source")}>Load a project first.</Missing>;

  const readers = new Set(a.findings.flatMap((f) => f.victims.map((v) => `${v.test}#${v.method}`)));
  const classes = new Map<string, string[]>();
  for (const m of a.test_methods) {
    const cls = m.split("#")[0];
    classes.set(cls, [...(classes.get(cls) ?? []), m]);
  }

  const invalidate = { cert: null, verify: null };
  const chooseTarget = (t: string) =>
    set({
      target: t,
      order: a.suggested?.victim === t ? a.suggested.order : [t],
      scan: null,
      scanDone: false,
      scanError: null,
      ...invalidate,
    });
  const setOrder = (order: string[]) => set({ order, scan: null, scanDone: false, ...invalidate });
  const move = (i: number, d: number) => {
    const next = [...s.order];
    [next[i], next[i + d]] = [next[i + d], next[i]];
    setOrder(next);
  };

  return (
    <>
      <ScreenHeader index={2} title="Pick the failing test">
        FlakeTrace diagnoses one test you already know fails. It does not search for flaky tests.
      </ScreenHeader>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)]">
        <div className="min-w-0 space-y-5">
          <Panel title="Failing test" aside={`${a.test_methods.length} discovered`}>
            {a.suggested && (
              <p className="mb-4 flex gap-2.5 rounded-lg bg-action-soft px-3.5 py-2.5 text-[0.93rem] text-ink-2">
                <Lightbulb className="mt-0.5 size-4 shrink-0 text-action" aria-hidden />
                <span>
                  Static analysis points at <TestName fq={a.suggested.victim} role="victim" />, which reads{" "}
                  <code className="font-mono text-resource">{a.suggested.resource}</code>.
                </span>
              </p>
            )}
            <div role="radiogroup" aria-label="Target test" className="space-y-4">
              {[...classes.entries()].map(([cls, methods]) => (
                <div key={cls}>
                  <p className="mb-1.5 font-mono text-[0.85rem] text-ink-3">{cls}</p>
                  <div className="space-y-1.5">
                    {methods.map((m) => {
                      const on = m === s.target;
                      return (
                        <button
                          key={m}
                          type="button"
                          role="radio"
                          aria-checked={on}
                          onClick={() => chooseTarget(m)}
                          className={`flex w-full items-center gap-3 rounded-lg border px-3.5 py-2.5 text-left transition-colors ${
                            on ? "border-victim bg-victim-soft" : "border-line hover:border-line-strong hover:bg-sunken/60"
                          }`}
                        >
                          <span className={`grid size-4 shrink-0 place-items-center rounded-full border-2 ${on ? "border-victim" : "border-line-strong"}`}>
                            {on && <motion.span layoutId="target-dot" className="size-2 rounded-full bg-victim" />}
                          </span>
                          <code className="min-w-0 flex-1 truncate font-mono text-[0.9rem]">#{methodName(m)}</code>
                          {readers.has(m) && <Badge tone="resource">reads shared state</Badge>}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </Panel>

          <Panel title="Known failing order" aside="Optional">
            <p className="mb-3 text-[0.93rem] text-ink-2">
              Tests in run order, first to last. Candidates in this order are tried first, and the certificate minimises it.
            </p>
            <Reorder.Group axis="y" values={s.order} onReorder={setOrder} className="space-y-1.5">
              {s.order.map((t, i) => (
                <Reorder.Item
                  key={t}
                  value={t}
                  className="flex items-center gap-2 rounded-lg border border-line bg-surface py-1.5 pl-2 pr-1.5"
                  whileDrag={{ scale: 1.015, boxShadow: "0 10px 28px rgba(12,26,48,0.14)" }}
                >
                  <GripVertical className="size-4 shrink-0 cursor-grab text-ink-3 active:cursor-grabbing" aria-hidden />
                  <span className="w-5 text-center text-sm text-ink-3 tabular">{i + 1}</span>
                  <span className="min-w-0 flex-1 truncate">
                    <TestName fq={t} role={t === s.target ? "victim" : undefined} />
                  </span>
                  <button type="button" aria-label={`Move ${shortName(t)} earlier`} disabled={i === 0} onClick={() => move(i, -1)} className="grid size-8 place-items-center rounded-md text-ink-3 hover:bg-sunken hover:text-ink disabled:opacity-30">
                    <ChevronUp className="size-4" />
                  </button>
                  <button type="button" aria-label={`Move ${shortName(t)} later`} disabled={i === s.order.length - 1} onClick={() => move(i, 1)} className="grid size-8 place-items-center rounded-md text-ink-3 hover:bg-sunken hover:text-ink disabled:opacity-30">
                    <ChevronDown className="size-4" />
                  </button>
                  <button type="button" aria-label={`Remove ${shortName(t)}`} onClick={() => setOrder(s.order.filter((x) => x !== t))} className="grid size-8 place-items-center rounded-md text-ink-3 hover:bg-victim-soft hover:text-victim">
                    <X className="size-4" />
                  </button>
                </Reorder.Item>
              ))}
            </Reorder.Group>
            <select
              aria-label="Add a test to the order"
              className={`${inputClass} mt-3 font-sans`}
              value=""
              onChange={(e) => e.target.value && setOrder([...s.order, e.target.value])}
            >
              <option value="">Add a test to the order…</option>
              {a.test_methods
                .filter((m) => !s.order.includes(m))
                .map((m) => (
                  <option key={m} value={m}>
                    {shortName(m)}
                  </option>
                ))}
            </select>
          </Panel>
        </div>

        <div className="min-w-0 space-y-5">
          <Panel title="Budget and acceptance">
            <Field label="Execution budget" htmlFor="budget" hint="Test-method invocations FlakeTrace may spend before it stops.">
              <div className="flex items-center gap-4">
                <input
                  id="budget"
                  type="range"
                  min={10}
                  max={400}
                  step={5}
                  value={s.budget}
                  onChange={(e) => set({ budget: Number(e.target.value), ...invalidate })}
                  className="h-2 min-w-0 flex-1 accent-action"
                />
                <output htmlFor="budget" className="w-14 text-right font-mono text-lg font-semibold tabular">
                  {s.budget}
                </output>
              </div>
            </Field>
            <BudgetMeter lines={planCost(s)} budget={s.budget} />

            <div className="mt-5 grid gap-5 border-t border-line pt-5 sm:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2">
              <Field
                label="Verification replays"
                hint={s.mode === "live" ? "Each live replay recompiles and runs, about two seconds." : "At least 90% must reproduce the failure."}
              >
                <Segmented
                  name="replays"
                  label="Verification replays"
                  value={s.replays}
                  onChange={(v) => set({ replays: v, ...invalidate })}
                  options={[5, 10, 20].map((v) => ({ value: v, label: String(v) }))}
                />
              </Field>
              <Field label="Wilson 95% lower bound floor" hint="Project policy, not a published finding.">
                <Segmented
                  name="threshold"
                  label="Wilson lower bound floor"
                  value={s.threshold}
                  onChange={(v) => set({ threshold: v, ...invalidate })}
                  options={[0.6, 0.7, 0.8].map((v) => ({ value: v, label: v.toFixed(2) }))}
                />
              </Field>
            </div>
          </Panel>

          <Panel title="Optional stages">
            <div className="space-y-2.5">
              <Switch checked={s.repairOn} onChange={(v) => set({ repairOn: v })} label="Propose a repair" description="Runs only when the certificate is Verified." />
              <Switch checked={s.evoOn} onChange={(v) => set({ evoOn: v })} label="EvoSuite generation" description="Search-based JUnit suite for the affected class." />
            </div>
          </Panel>

          {s.mode === "demo" && (
            <Panel title="Scenario" aside={<Badge tone="action">Offline demo</Badge>}>
              <p className="mb-3 text-[0.93rem] text-ink-2">
                Recorded runs are real. The other scenarios simulate weaker evidence so you can show how the certificate responds.
              </p>
              <div role="radiogroup" aria-label="Scenario" className="space-y-1.5">
                {SCENARIOS.map((sc) => {
                  const on = sc.value === s.scenario;
                  return (
                    <button
                      key={sc.value}
                      type="button"
                      role="radio"
                      aria-checked={on}
                      onClick={() => set({ scenario: sc.value, ...invalidate })}
                      className={`flex w-full items-start gap-3 rounded-lg border px-3.5 py-2.5 text-left transition-colors ${
                        on ? "border-action bg-action-soft" : "border-line hover:border-line-strong hover:bg-sunken/60"
                      }`}
                    >
                      <span className={`mt-1 grid size-4 shrink-0 place-items-center rounded-full border-2 ${on ? "border-action" : "border-line-strong"}`}>
                        {on && <motion.span layoutId="scenario-dot" className="size-2 rounded-full bg-action" />}
                      </span>
                      <span>
                        <span className="block font-medium">{sc.title}</span>
                        <span className="block text-sm text-ink-3">{sc.desc}</span>
                      </span>
                    </button>
                  );
                })}
              </div>
            </Panel>
          )}
        </div>
      </div>

      <FlowNav back={() => go("source")} next={() => go("diagnosis")} nextLabel="Go to diagnosis" nextDisabled={!s.target} hint="Pick a target test." />
    </>
  );
}
