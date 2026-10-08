import { useMemo, useState } from "react";
import { motion } from "motion/react";
import { useStore } from "../state";
import { accessKey } from "../lib/evidence";
import { simpleClass } from "../lib/format";
import type { Analysis } from "../lib/types";
import { Badge, Button, FlowNav, Missing, Panel, ScreenHeader, type Tone } from "../components/ui";

type Col = "w" | "res" | "r";
type Cat = "dir" | "ind" | "res";

type GNode = {
  id: string;
  col: Col;
  title: string;
  sub: string;
  loc: string;
  kind: string;
  badge: [string, Tone];
  rows: [string, string][];
  code: string;
  note: string;
  stroke: string;
  fill: string;
  strong: boolean;
};

type GEdge = { id: string; from: string; to: string; cat: Cat; onPath: boolean };

const C = {
  ink: "#0c1a30", ink2: "#34445c", ink3: "#56657b", strong: "#a9b4c4", surface: "#ffffff",
  polluter: "#c2410c", polluterSoft: "#fff0e6", resource: "#0f766e", resourceSoft: "#e2f4f1",
  victim: "#be123c", victimSoft: "#fdebef", candidate: "#a15c07", action: "#1f4fd8",
};

const COLS: Record<Col, { x: number; w: number }> = { w: { x: 4, w: 256 }, res: { x: 352, w: 196 }, r: { x: 640, w: 256 } };
const ROW = 78;
const NH = 62;
const TOP = 40;
const W = 900;

const EDGE_STYLE: Record<Cat, { stroke: string; dash?: string; label: string }> = {
  dir: { stroke: C.ink2, label: "Direct access" },
  ind: { stroke: C.candidate, dash: "7 5", label: "Through a call" },
  res: { stroke: C.strong, dash: "1.5 5", label: "Restored in teardown" },
};

function build(a: Analysis, target: string, polluter: string) {
  const nodes: GNode[] = [];
  const byKey = new Map<string, GNode>();
  const edges: GEdge[] = [];

  const node = (col: Col, key: string, make: () => Omit<GNode, "id" | "col">) => {
    const k = `${col}|${key}`;
    let n = byKey.get(k);
    if (!n) {
      n = { id: `n${nodes.length}`, col, ...make() };
      byKey.set(k, n);
      nodes.push(n);
    }
    return n;
  };
  const edge = (from: GNode, to: GNode, cat: Cat, onPath: boolean) => {
    const id = `${from.id}-${to.id}-${cat}`;
    const existing = edges.find((e) => e.id === id);
    if (existing) existing.onPath ||= onPath;
    else edges.push({ id, from: from.id, to: to.id, cat, onPath });
  };

  for (const f of a.findings) {
    const onPathFinding = f.writers.some((w) => accessKey(w) === polluter && !w.restores) && f.readers.some((r) => accessKey(r) === target);
    const rn = node("res", f.resource.id, () => ({
      title: f.resource.id,
      sub: f.resource.type,
      loc: f.resource.declared_at,
      kind: "Mutable static field",
      badge: [f.verdict, f.severity === "bad" ? "victim" : f.severity === "warn" ? "candidate" : "verified"],
      rows: [
        ["Owner", f.resource.owner_fqcn], ["Type", f.resource.type], ["Declared at", f.resource.declared_at],
        ["Writers", String(f.writers.length)], ["Unrestored writers", String(f.polluters.length)], ["Readers", String(f.readers.length)],
      ],
      code: "",
      note: `${f.summary}.`,
      stroke: C.resource,
      fill: C.resourceSoft,
      strong: true,
    }));

    for (const w of f.writers) {
      const key = accessKey(w);
      const isPolluter = key === polluter && !w.restores;
      const wn = node("w", key, () => ({
        title: simpleClass(key),
        sub: `#${w.method}`,
        loc: `${w.file}:${w.line}`,
        kind: "Test method that writes",
        badge: w.restores ? ["restored in teardown", "verified"] : isPolluter ? ["polluter", "polluter"] : ["unrestored write", "candidate"],
        rows: [["Test", w.test], ["Method", w.method], ["Access", w.how], ["Attribution", w.attribution === "direct" ? "direct" : "through a call"], ["Source", `${w.file}:${w.line}`]],
        code: w.code.trim(),
        note: w.restores ? "This write is undone before the next test runs, so it cannot leak." : "The field keeps this value after the test returns.",
        stroke: w.restores ? C.strong : C.polluter,
        fill: isPolluter ? C.polluterSoft : C.surface,
        strong: isPolluter,
      }));
      edge(wn, rn, w.restores ? "res" : w.attribution === "direct" ? "dir" : "ind", isPolluter && onPathFinding);
    }

    for (const r of f.readers) {
      const key = accessKey(r);
      const isTarget = key === target;
      const rd = node("r", key, () => ({
        title: simpleClass(key),
        sub: `#${r.method}`,
        loc: `${r.file}:${r.line}`,
        kind: "Test method that reads",
        badge: isTarget ? ["target", "victim"] : ["reader", "neutral"],
        rows: [["Test", r.test], ["Method", r.method], ["Access", r.how], ["Attribution", r.attribution === "direct" ? "direct" : "through a call"], ["Source", `${r.file}:${r.line}`]],
        code: r.code.trim(),
        note: "Whatever the field holds when this line runs is what the test sees.",
        stroke: isTarget ? C.victim : C.strong,
        fill: isTarget ? C.victimSoft : C.surface,
        strong: isTarget,
      }));
      edge(rn, rd, r.attribution === "direct" ? "dir" : "ind", isTarget && onPathFinding);
    }
  }
  return { nodes, edges };
}

const trim = (text: string, max: number) => (text.length > max ? `${text.slice(0, max - 1)}…` : text);

export default function GraphScreen() {
  const { s, go } = useStore();
  const [sel, setSel] = useState<string | null>(null);
  const [off, setOff] = useState<Record<Cat, boolean>>({ dir: false, ind: false, res: false });
  const polluter = s.scan?.find((r) => r.reproduced)?.candidate ?? "";
  const model = useMemo(() => (s.analysis ? build(s.analysis, s.target, polluter) : null), [s.analysis, s.target, polluter]);

  if (!s.analysis || !model) return <Missing title="No analysis yet" action="Choose a project" onAction={() => go("source")}>Load and diagnose a project first.</Missing>;

  const { nodes, edges } = model;
  const cols: Record<Col, GNode[]> = { w: [], res: [], r: [] };
  nodes.forEach((n) => cols[n.col].push(n));
  const maxN = Math.max(cols.w.length, cols.res.length, cols.r.length, 1);
  const H = TOP + maxN * ROW;
  const pos = new Map<string, { x: number; y: number; w: number }>();
  (Object.keys(cols) as Col[]).forEach((c) => {
    const top = TOP + ((maxN - cols[c].length) * ROW) / 2;
    cols[c].forEach((n, i) => pos.set(n.id, { x: COLS[c].x, y: top + i * ROW, w: COLS[c].w }));
  });

  const edgeOn = (e: GEdge) => !off[e.cat] && (!sel || e.from === sel || e.to === sel);
  const live = new Set<string>();
  edges.forEach((e) => {
    if (edgeOn(e)) {
      live.add(e.from);
      live.add(e.to);
    }
  });
  const selected = nodes.find((n) => n.id === sel) ?? null;
  const toggle = (id: string) => setSel((cur) => (cur === id ? null : id));

  return (
    <>
      <ScreenHeader index={5} title="Evidence graph">
        Every write and read the analysis resolved, and how each was attributed. The certificate is one path through this graph. The rest is what was considered and not chosen.
      </ScreenHeader>

      <Panel
        title="Reads and writes"
        aside={`${cols.res.length} shared ${cols.res.length === 1 ? "field" : "fields"}, ${cols.w.length} writers, ${cols.r.length} readers`}
        pad={false}
      >
        <div className="flex flex-wrap items-center gap-2 border-b border-line px-5 py-3">
          <span className="mr-1 text-sm text-ink-3">Show</span>
          {(Object.keys(EDGE_STYLE) as Cat[]).map((cat) => (
            <button
              key={cat}
              type="button"
              aria-pressed={!off[cat]}
              onClick={() => setOff((o) => ({ ...o, [cat]: !o[cat] }))}
              className={`inline-flex h-8 items-center gap-2 rounded-full border px-3 text-sm font-medium transition-colors ${off[cat] ? "border-line bg-surface text-ink-3 line-through" : "border-line-strong bg-sunken text-ink"}`}
            >
              <svg width="22" height="6" aria-hidden>
                <line x1="1" y1="3" x2="21" y2="3" stroke={EDGE_STYLE[cat].stroke} strokeWidth="2.5" strokeDasharray={EDGE_STYLE[cat].dash} strokeLinecap="round" />
              </svg>
              {EDGE_STYLE[cat].label}
            </button>
          ))}
          <Button size="sm" variant="ghost" className="ml-auto" disabled={!sel} onClick={() => setSel(null)}>
            Clear selection
          </Button>
        </div>

        <div className="grid xl:grid-cols-[minmax(0,1fr)_300px]">
          <div className="scrollbar-thin min-w-0 overflow-x-auto p-4">
            {nodes.length === 0 ? (
              <p className="p-6 text-ink-3">No shared mutable statics were found, so there is nothing to graph.</p>
            ) : (
              <svg viewBox={`0 0 ${W} ${H}`} className="block h-auto w-full min-w-[760px]" role="group" aria-label="Writes and reads between test methods and shared static fields" style={{ fontFamily: "var(--font-sans)" }}>
                <defs>
                  {[["dir", C.ink2], ["ind", C.candidate], ["res", C.strong], ["pol", C.polluter], ["vic", C.victim]].map(([id, color]) => (
                    <marker key={id} id={`arrow-${id}`} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                      <path d="M0,0 L10,5 L0,10 z" fill={color} />
                    </marker>
                  ))}
                </defs>
                {[["Tests that write", COLS.w.x], ["Shared static state", COLS.res.x], ["Tests that read", COLS.r.x]].map(([label, x]) => (
                  <text key={label} x={x} y={16} fontSize="13" fontWeight="600" fill={C.ink3}>
                    {label}
                  </text>
                ))}

                {edges.map((e) => {
                  const a = pos.get(e.from)!;
                  const b = pos.get(e.to)!;
                  const x1 = a.x + a.w;
                  const y1 = a.y + NH / 2;
                  const x2 = b.x - 4;
                  const y2 = b.y + NH / 2;
                  const intoResource = nodes.find((n) => n.id === e.to)?.col === "res";
                  const style = EDGE_STYLE[e.cat];
                  const stroke = e.onPath ? (intoResource ? C.polluter : C.victim) : style.stroke;
                  const marker = e.onPath ? (intoResource ? "pol" : "vic") : e.cat;
                  return (
                    <motion.path
                      key={e.id}
                      d={`M${x1},${y1} C${x1 + 56},${y1} ${x2 - 56},${y2} ${x2},${y2}`}
                      fill="none"
                      stroke={stroke}
                      strokeWidth={e.onPath ? 3.5 : 1.75}
                      strokeDasharray={e.onPath ? undefined : style.dash}
                      strokeLinecap="round"
                      markerEnd={`url(#arrow-${marker})`}
                      initial={false}
                      animate={{ opacity: edgeOn(e) ? 1 : 0.06 }}
                      transition={{ duration: 0.2 }}
                    />
                  );
                })}

                {nodes.map((n) => {
                  const p = pos.get(n.id)!;
                  const faint = !live.has(n.id) && n.id !== sel;
                  const isSel = n.id === sel;
                  const chars = Math.floor((p.w - 24) / 7.2);
                  return (
                    <motion.g
                      key={n.id}
                      className="gnode cursor-pointer"
                      role="button"
                      tabIndex={0}
                      aria-pressed={isSel}
                      aria-label={`${n.title}${n.col === "res" ? "" : n.sub}, ${n.badge[0]}`}
                      onClick={() => toggle(n.id)}
                      onKeyDown={(ev) => {
                        if (ev.key === "Enter" || ev.key === " ") {
                          ev.preventDefault();
                          toggle(n.id);
                        }
                      }}
                      initial={false}
                      animate={{ opacity: faint ? 0.18 : 1 }}
                      transition={{ duration: 0.2 }}
                    >
                      <rect x={p.x} y={p.y} width={p.w} height={NH} rx="9" fill={n.fill} stroke={isSel ? C.action : n.stroke} strokeWidth={isSel ? 3 : n.strong ? 2.25 : 1.25} />
                      <text x={p.x + 12} y={p.y + 21} fontSize="14" fontWeight="600" fill={C.ink}>
                        {trim(n.title, chars)}
                      </text>
                      <text x={p.x + 12} y={p.y + 38} fontSize="12" fill={C.ink2} style={{ fontFamily: "var(--font-mono)" }}>
                        {trim(n.sub, chars)}
                      </text>
                      <text x={p.x + 12} y={p.y + 53} fontSize="11" fill={C.ink3} style={{ fontFamily: "var(--font-mono)" }}>
                        {trim(n.loc, chars)}
                      </text>
                    </motion.g>
                  );
                })}
              </svg>
            )}
          </div>

          <aside className="min-w-0 border-t border-line bg-sunken/50 p-5 xl:border-l xl:border-t-0" aria-live="polite">
            {selected ? (
              <motion.div key={selected.id} initial={{ opacity: 0, x: 8 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.18 }}>
                <p className="text-sm text-ink-3">{selected.kind}</p>
                <p className="mt-1 font-mono text-[1rem] font-semibold [overflow-wrap:anywhere]">
                  {selected.title}
                  {selected.col !== "res" && selected.sub}
                </p>
                <Badge tone={selected.badge[1]} className="mt-2">
                  {selected.badge[0]}
                </Badge>
                <dl className="mt-4 space-y-2 text-sm">
                  {selected.rows.map(([k, v]) => (
                    <div key={k}>
                      <dt className="text-ink-3">{k}</dt>
                      <dd className="font-mono text-[0.82rem] text-ink [overflow-wrap:anywhere]">{v}</dd>
                    </div>
                  ))}
                </dl>
                {selected.code && (
                  <pre className="scrollbar-thin mt-4 overflow-x-auto rounded-md border border-line bg-surface px-3 py-2 font-mono text-[0.8rem] text-ink-2">{selected.code}</pre>
                )}
                <p className="mt-3 text-sm text-ink-2">{selected.note}</p>
              </motion.div>
            ) : (
              <p className="text-[0.93rem] text-ink-3">Select a node to see its source line and how the access was attributed. The thick orange and crimson line is the path the certificate names.</p>
            )}
          </aside>
        </div>

        <div className="space-y-2 border-t border-line px-5 py-4 text-[0.93rem] text-ink-2">
          <p>
            <span className="font-medium text-ink">Direct access</span> means the test names the field on the line shown.{" "}
            <span className="font-medium text-candidate">Through a call</span> means the analysis followed a call into production code, so the attribution is to the call chain.{" "}
            <span className="font-medium text-ink-3">Restored in teardown</span> means the writing class resets the field, so the write cannot leak.
          </p>
          <p className="text-ink-3">Reflective and native access never appears here. Its absence is not evidence that it does not happen.</p>
        </div>
      </Panel>

      <FlowNav back={() => go("result")} next={() => go("repair")} nextLabel="Go to repair" nextDisabled={s.cert?.status !== "done"} hint="Issue the certificate first." />
    </>
  );
}
