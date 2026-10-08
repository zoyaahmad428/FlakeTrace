import { motion } from "motion/react";
import { CircleCheck, CircleX, FileClock, RotateCcw, ShieldAlert, ShieldCheck, ShieldX } from "lucide-react";
import { SCENARIOS, activeScenario, planCost, useStore, type CertRun } from "../state";
import { ABSTENTION, DECISION, MATCH_FRACTION, decide, totalCost, type Decision } from "../lib/certificate";
import { evidencePath } from "../lib/evidence";
import { failureSignature, jdkVersion, methodName, plural, reproduces, shortName, simpleClass, sleep } from "../lib/format";
import type { RunResult } from "../lib/types";
import { Trace } from "../components/Trace";
import { Badge, Button, CopyButton, FlowNav, Missing, Panel, ScreenHeader, Status, TONE, TestName, Terminal } from "../components/ui";

const SEAL: Record<Decision, { Icon: typeof ShieldCheck; hex: string }> = {
  verified: { Icon: ShieldCheck, hex: "#15803d" },
  candidate: { Icon: ShieldAlert, hex: "#a15c07" },
  unresolved: { Icon: ShieldX, hex: "#475569" },
};

function Seal({ decision }: { decision: Decision }) {
  const { Icon, hex } = SEAL[decision];
  const tone = TONE[DECISION[decision].tone];
  return (
    <div className={`relative grid size-24 shrink-0 place-items-center rounded-full ${tone.soft}`}>
      <svg viewBox="0 0 96 96" className="absolute inset-0 -rotate-90" aria-hidden>
        <motion.circle cx="48" cy="48" r="45" fill="none" stroke={hex} strokeWidth="3.5" strokeLinecap="round" initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }} />
        <circle cx="48" cy="48" r="37" fill="none" stroke={hex} strokeOpacity="0.3" strokeWidth="1.5" strokeDasharray="2 5" />
      </svg>
      <motion.span initial={{ scale: 0.5, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ delay: 0.35, type: "spring", stiffness: 320, damping: 18 }}>
        <Icon className={`size-10 ${tone.text}`} strokeWidth={1.75} aria-hidden />
      </motion.span>
    </div>
  );
}

function Cells({ label, values, total, good, goodClass, badClass, goodWord, badWord }: { label: string; values: boolean[]; total: number; good: boolean; goodClass: string; badClass: string; goodWord: string; badWord: string }) {
  const count = values.filter((v) => v === good).length;
  return (
    <div>
      <div className="mb-2 flex flex-wrap items-baseline justify-between gap-2">
        <span className="font-medium">{label}</span>
        <span className="text-sm text-ink-2 tabular">
          {count} of {total} {goodWord}
          {values.length > count ? `, ${values.length - count} ${badWord}` : ""}
        </span>
      </div>
      <div
        role="img"
        aria-label={`${label}: ${count} of ${total} ${goodWord}`}
        className="grid gap-1.5"
        style={{ gridTemplateColumns: `repeat(${Math.min(total, 10)}, minmax(0, 30px))` }}
      >
        {Array.from({ length: total }, (_, i) => {
          const v = values[i];
          return (
            <motion.span
              key={i}
              className={`aspect-square rounded-[5px] border ${v === undefined ? "border-dashed border-line-strong bg-surface" : v === good ? goodClass : badClass}`}
              initial={false}
              animate={v === undefined ? { scale: 1 } : { scale: [0.55, 1] }}
              transition={{ duration: 0.22 }}
            />
          );
        })}
      </div>
    </div>
  );
}

function WilsonBar({ lo, hi, k, n, threshold, fill }: { lo: number; hi: number; k: number; n: number; threshold: number; fill: string }) {
  const p = n ? k / n : 0;
  return (
    <div>
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <span className="font-medium">Wilson 95% interval</span>
        <span className="font-mono text-ink-2 tabular">
          {lo.toFixed(2)} to {hi.toFixed(2)}
        </span>
      </div>
      <div className="relative mx-2 mt-3 h-14">
        <div className="absolute inset-x-0 top-4 h-3 rounded-full bg-sunken ring-1 ring-line" />
        <motion.div
          className={`absolute top-4 h-3 origin-left rounded-full ${fill}`}
          style={{ left: `${lo * 100}%`, width: `${Math.max(hi - lo, 0.005) * 100}%` }}
          initial={{ scaleX: 0 }}
          animate={{ scaleX: 1 }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        />
        <span className="absolute top-1.5 h-8 w-0.5 -translate-x-1/2 bg-ink" style={{ left: `${threshold * 100}%` }} aria-hidden />
        <span className="absolute top-10 -translate-x-1/2 whitespace-nowrap text-xs font-medium text-ink-2" style={{ left: `${threshold * 100}%` }}>
          floor {threshold.toFixed(2)}
        </span>
        <span className="absolute top-[11px] size-[22px] -translate-x-1/2 rounded-full border-[3px] border-white bg-ink shadow" style={{ left: `${p * 100}%` }} aria-hidden />
        <span className="absolute left-0 top-10 text-xs text-ink-3">0</span>
        <span className="absolute right-0 top-10 text-xs text-ink-3">1</span>
      </div>
      <p className="mt-1 text-sm text-ink-3">
        The interval describes how reliably this order replays under the harness. It is not the probability that the diagnosis is correct.
      </p>
    </div>
  );
}

const flakyReproduces = (i: number) => (i * 7 + 3) % 20 < 13;

export default function CertificateScreen() {
  const { s, set, api, go } = useStore();
  const a = s.analysis;
  if (!a || !s.source || !s.scanDone) return <Missing title="No diagnosis yet" action="Go to diagnosis" onAction={() => go("diagnosis")}>Run the diagnosis before issuing a certificate.</Missing>;

  const source = s.source;
  const target = s.target;
  const scenario = activeScenario(s);
  const polluterRow = s.scan?.find((r) => r.reproduced);
  const path = polluterRow ? evidencePath(a, polluterRow.candidate, target) : null;
  const resourceSupported = !!path && scenario !== "hidden";
  const cost = planCost(s);
  const total = totalCost(cost);
  const cert = s.cert;
  const outcome = cert?.outcome;
  const N = s.replays;

  async function issue() {
    const t0 = performance.now();
    const polluter = polluterRow?.candidate ?? "";
    const order = polluter ? [polluter, target] : [target];
    const base: CertRun = {
      status: "running", scenario, polluter, order, controls: [], replays: [], signature: null, outcome: null, cost,
      deletionMinimal: false, resourceSupported, issuedAt: "", wallMs: 0,
    };
    set({ cert: base, verify: null });
    const finish = (patch: Partial<CertRun>) =>
      set((prev) => ({ cert: prev.cert && { ...prev.cert, ...patch, status: "done", issuedAt: new Date().toISOString(), wallMs: Math.round(performance.now() - t0) } }));
    const stop = (r: RunResult) => finish({ error: r.error ?? `The runner returned ${r.status}.` });

    if (!polluter || total > s.budget) {
      await sleep(400);
      finish({
        outcome: decide({ budget: s.budget, cost: total, polluterFound: !!polluter, controls: 0, controlsPassed: 0, replays: 0, reproduced: 0, threshold: s.threshold, deletionMinimal: false, resourceSupported }),
      });
      return;
    }

    const controls: boolean[] = [];
    let alone: RunResult | undefined;
    for (let i = 0; i < N; i++) {
      if (s.mode === "live" || i === 0) {
        alone = await api.run(source.path, [target], false);
        if (alone.status !== "ok") return stop(alone);
      } else {
        await sleep(45);
      }
      controls.push(!!alone?.passed && !(scenario === "unstable" && i % 4 === 2));
      set((prev) => ({ cert: prev.cert && { ...prev.cert, controls: [...controls], alone } }));
    }

    const replays: boolean[] = [];
    let polluting: RunResult | undefined;
    for (let i = 0; i < N; i++) {
      if (s.mode === "live" || i === 0) {
        polluting = await api.run(source.path, order, false);
        if (polluting.status !== "ok") return stop(polluting);
      } else {
        await sleep(55);
      }
      const hit = reproduces(polluting?.output, target);
      replays.push(scenario === "flaky" ? hit && flakyReproduces(i) : hit);
      set((prev) => ({ cert: prev.cert && { ...prev.cert, replays: [...replays], polluting } }));
    }

    const deletionMinimal = !!alone?.passed;
    finish({
      signature: failureSignature(polluting?.output, target),
      deletionMinimal,
      outcome: decide({
        budget: s.budget, cost: total, polluterFound: true, controls: N, controlsPassed: controls.filter(Boolean).length,
        replays: N, reproduced: replays.filter(Boolean).length, threshold: s.threshold, deletionMinimal, resourceSupported,
      }),
    });
  }

  const start = () => issue().catch((e: Error) => set((prev) => ({ cert: prev.cert && { ...prev.cert, status: "done", error: e.message } })));

  const running = cert?.status === "running";
  const tone = outcome ? TONE[DECISION[outcome.decision].tone] : TONE.neutral;
  const k = cert?.replays.filter(Boolean).length ?? 0;
  const certId = `FT-${s.git?.sha ?? "local"}-${simpleClass(target).slice(0, 4).toUpperCase()}${(target.length * 37) % 1000}`;
  const command = cert?.polluting?.command ?? `java -cp build/classes FlakeDemo ${(cert?.order ?? []).join(" ")}`;
  const scenarioTitle = SCENARIOS.find((x) => x.value === scenario)?.title ?? "";
  const innocent = s.scan?.find((r) => !r.reproduced);
  const reason = outcome?.reason ? ABSTENTION[outcome.reason] : null;
  const checks = outcome && cert?.replays.length ? outcome.checks : outcome?.checks.slice(0, 1) ?? [];

  const provenance =
    s.mode === "live" ? (
      <Badge tone="action">Live runs</Badge>
    ) : scenario === "planted" ? (
      <Badge tone="action">Recorded runs</Badge>
    ) : (
      <Badge tone="candidate">Simulated: {scenarioTitle}</Badge>
    );

  return (
    <>
      <ScreenHeader index={4} title="Certificate">
        What was found, how it was established, and what it does not claim.
      </ScreenHeader>

      <section className={`relative overflow-hidden rounded-2xl border bg-surface p-6 md:p-7 ${outcome ? "border-line-strong" : "border-line"}`}>
        {outcome && <div aria-hidden className={`absolute inset-x-0 top-0 h-1.5 ${tone.fill}`} />}
        <div className="flex flex-col gap-6 md:flex-row md:items-center">
          {outcome ? (
            <Seal key={`${outcome.decision}${cert?.issuedAt}`} decision={outcome.decision} />
          ) : (
            <div className="grid size-24 shrink-0 place-items-center rounded-full border-2 border-dashed border-line-strong bg-sunken">
              <FileClock className="size-9 text-ink-3" strokeWidth={1.75} aria-hidden />
            </div>
          )}
          <div className="min-w-0 flex-1">
            {outcome ? (
              <>
                <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
                  <h2 className={`text-[2.4rem] font-semibold leading-none tracking-[-0.02em] ${tone.text}`}>{DECISION[outcome.decision].label}</h2>
                  {reason && <span className="text-xl font-medium text-ink-2">{reason.title}</span>}
                </div>
                <p className="mt-3 max-w-[70ch] text-[1.05rem] text-ink-2">{outcome.rationale}</p>
                {reason && <p className="mt-2 max-w-[70ch] font-medium text-ink">{reason.next}</p>}
                <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-ink-3">
                  <code className="font-mono text-ink-2">{certId}</code>
                  <span>Issued {new Date(cert!.issuedAt).toLocaleString()}</span>
                  {provenance}
                </div>
              </>
            ) : (
              <>
                <h2 className="text-[2rem] font-semibold leading-tight tracking-[-0.015em]">{running ? "Replaying" : "Not issued yet"}</h2>
                <p className="mt-2 max-w-[70ch] text-[1.02rem] text-ink-2">
                  {polluterRow
                    ? `FlakeTrace runs the target alone ${plural(N, "time")}, then replays ${shortName(polluterRow.candidate)} followed by the target ${plural(N, "time")}. The plan costs ${total} of your ${s.budget} invocations.`
                    : "No candidate reproduced the failure, so there is no order to replay. Issuing records the abstention."}
                </p>
                {running && (
                  <p className="mt-2 text-sm text-ink-3 tabular">
                    {cert.controls.length} of {N} controls, {cert.replays.length} of {N} replays
                  </p>
                )}
              </>
            )}
          </div>
          <Button variant={outcome ? "secondary" : "primary"} busy={running} onClick={start} icon={outcome ? <RotateCcw className="size-4" aria-hidden /> : undefined}>
            {running ? "Replaying" : outcome ? "Issue again" : polluterRow ? `Run ${N + N} replays and issue` : "Issue certificate"}
          </Button>
        </div>
        {cert?.error && <Status state="error">{cert.error}</Status>}
      </section>

      <Panel title="Evidence path" aside={path ? "From source analysis and execution" : undefined} className="mt-5">
        {polluterRow ? (
          <Trace
            polluter={{ title: simpleClass(polluterRow.candidate), sub: `#${methodName(polluterRow.candidate)}`, line: path ? `${path.write.file}:${path.write.line}` : undefined, detail: path?.write.how }}
            resource={{ title: path?.resource.id ?? "", sub: path?.resource.type, line: path?.resource.declared_at, detail: resourceSupported ? "mutable static field" : "Source analysis could not see the write that connects these tests. The order still fails." }}
            victim={{ title: simpleClass(target), sub: `#${methodName(target)}`, line: path ? `${path.read.file}:${path.read.line}` : undefined, detail: path?.read.how }}
            hiddenResource={!resourceSupported}
          />
        ) : (
          <p className="text-ink-2">No candidate reproduced the failure, so there is no path to draw.</p>
        )}
      </Panel>

      <div className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1.35fr)_minmax(0,1fr)]">
        <div className="min-w-0 space-y-5">
          <Panel title="Reliability" aside={cert?.replays.length ? `${k} of ${N} reproduced` : undefined}>
            {cert && (cert.controls.length || running) ? (
              <div className="space-y-6">
                <Cells label="Target alone" values={cert.controls} total={N} good goodClass="border-verified bg-verified" badClass="border-candidate bg-candidate" goodWord="passed" badWord="failed" />
                <Cells label="Polluter, then target" values={cert.replays} total={N} good goodClass="border-victim bg-victim" badClass="border-line-strong bg-sunken" goodWord="reproduced" badWord="did not" />
                {outcome && cert.replays.length > 0 && (
                  <WilsonBar lo={outcome.interval[0]} hi={outcome.interval[1]} k={k} n={N} threshold={s.threshold} fill={tone.fill} />
                )}
                {s.mode === "demo" && (
                  <p className="border-t border-line pt-3 text-sm text-ink-3">
                    Offline demo: the first run of each order is a recorded real run and the repetitions reuse its outcome.
                    {scenario !== "planted" && ` The "${scenarioTitle}" scenario then alters them.`}
                  </p>
                )}
              </div>
            ) : (
              <p className="text-ink-3">
                {outcome ? "No replays ran, because verification could not start." : `Replays appear here. Acceptance needs ${Math.ceil(MATCH_FRACTION * N)} of ${N} to reproduce and a Wilson lower bound of at least ${s.threshold.toFixed(2)}.`}
              </p>
            )}
          </Panel>

          {outcome && (
            <Panel title="Acceptance checks" pad={false}>
              <ul>
                {checks.map((c, i) => (
                  <motion.li key={c.label} initial={{ opacity: 0, x: -6 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }} className="flex items-start gap-3 border-b border-line px-5 py-3 last:border-0">
                    {c.ok ? <CircleCheck className="mt-0.5 size-5 shrink-0 text-verified" aria-label="Passed" /> : <CircleX className="mt-0.5 size-5 shrink-0 text-victim" aria-label="Failed" />}
                    <div className="min-w-0">
                      <p className="font-medium">{c.label}</p>
                      <p className="text-sm text-ink-3">{c.detail}</p>
                    </div>
                  </motion.li>
                ))}
              </ul>
            </Panel>
          )}

          {outcome && cert?.replays.length ? (
            <Panel title="Counterfactual checks" pad={false}>
              <ul className="text-[0.93rem]">
                {[
                  { order: [target], result: `passed ${cert.controls.filter(Boolean).length} of ${N}`, ok: true },
                  { order: cert.order, result: `failed ${k} of ${N}`, ok: false },
                  ...(innocent ? [{ order: [innocent.candidate, target], result: "passed", ok: true }] : []),
                ].map((row) => (
                  <li key={row.order.join()} className="flex flex-wrap items-center gap-x-3 gap-y-1 border-b border-line px-5 py-3 last:border-0">
                    <span className="flex min-w-0 flex-wrap items-center gap-x-2">
                      {row.order.map((t, i) => (
                        <span key={t} className="flex items-center gap-2">
                          {i > 0 && <span className="text-ink-3">then</span>}
                          <TestName fq={t} role={t === target ? "victim" : t === cert.polluter ? "polluter" : undefined} />
                        </span>
                      ))}
                    </span>
                    <Badge tone={row.ok ? "verified" : "victim"} className="ml-auto">
                      {row.result}
                    </Badge>
                  </li>
                ))}
              </ul>
              <p className="border-t border-line px-5 py-3 text-sm text-ink-3">
                Removing the polluter makes the target pass, so the order is deletion-minimal (1-minimal). That is not the same as the minimum.
              </p>
            </Panel>
          ) : null}
        </div>

        <div className="min-w-0 space-y-5">
          <Panel title="Case identity">
            <dl className="grid grid-cols-[auto_minmax(0,1fr)] gap-x-5 gap-y-2.5 text-[0.93rem]">
              {(
                [
                  ["Repository", source.name],
                  ["Commit", s.git ? `${s.git.sha} on ${s.git.branch}` : "no git history"],
                  ["Module", source.module],
                  ["JDK", jdkVersion(s.health?.toolchain.java)],
                  ["Runner", s.health?.toolchain.mvn ? "Maven" : "FlakeTrace JDK harness"],
                  ["Target", <TestName key="t" fq={target} role="victim" />],
                  ["Classification", outcome && outcome.decision !== "unresolved" ? "Victim: passes alone, fails after a polluter" : "Not classified"],
                  ["Failure signature", cert?.signature ? <code key="sig" className="font-mono text-[0.85rem] [overflow-wrap:anywhere]">{cert.signature}</code> : "Not captured"],
                ] as [string, React.ReactNode][]
              ).map(([key, value]) => (
                <div key={key} className="contents">
                  <dt className="text-ink-3">{key}</dt>
                  <dd className="min-w-0 [overflow-wrap:anywhere]">{value}</dd>
                </div>
              ))}
            </dl>
          </Panel>

          <Panel title="Budget account" aside={`${total} of ${s.budget}`}>
            <ul className="space-y-2 text-[0.93rem]">
              {cost.map((l) => (
                <li key={l.label} className="flex items-center gap-3">
                  <span className="text-ink-2">{l.label}</span>
                  <span className="mx-1 flex-1 border-b border-dotted border-line-strong" aria-hidden />
                  <span className="font-mono tabular">{l.invocations}</span>
                </li>
              ))}
              <li className="flex items-center gap-3 border-t border-line pt-2 font-semibold">
                <span>Total invocations</span>
                <span className="ml-auto font-mono tabular">{total}</span>
              </li>
            </ul>
            <p className="mt-3 text-sm text-ink-3">
              0 Maven launches. {cert?.wallMs ? `Wall time ${(cert.wallMs / 1000).toFixed(1)} s in this session.` : ""}
            </p>
          </Panel>

          {cert?.order.length === 2 && outcome && outcome.decision !== "unresolved" && (
            <Panel title="Replay command" aside={<CopyButton text={command} />}>
              <p className="mb-2 text-sm text-ink-3">Deletion-minimal order. Anyone can re-run it to check this certificate.</p>
              <Terminal text={command} wrap />
            </Panel>
          )}

          <Panel title="Limitations">
            <ul className="list-disc space-y-1.5 pl-5 text-[0.93rem] text-ink-2 marker:text-ink-3">
              <li>Reflective and native writes are invisible to source analysis. Their absence here is not evidence they don't happen.</li>
              <li>One resource at a time. Other shared state may also be involved.</li>
              <li>Replays ran in one JVM through the harness, not in a clean container.</li>
              <li>Committed families are static fields, system properties and file paths. Anything else is recorded as unsupported.</li>
            </ul>
          </Panel>
        </div>
      </div>

      <FlowNav back={() => go("diagnosis")} next={() => go("graph")} nextLabel="Open the evidence graph" />
    </>
  );
}
