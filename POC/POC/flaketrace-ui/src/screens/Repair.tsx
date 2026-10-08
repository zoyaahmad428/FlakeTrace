import { useState } from "react";
import { motion } from "motion/react";
import { CircleCheck, CircleX, Lock, RotateCcw, Wrench } from "lucide-react";
import { useStore } from "../state";
import { DECISION } from "../lib/certificate";
import { evidencePath } from "../lib/evidence";
import { sentence } from "../lib/format";
import { Badge, Button, FlowNav, Panel, ScreenHeader, Status, Switch, type StatusState } from "../components/ui";

type DiffRow = { kind: "hunk" | "add" | "del" | "ctx"; text: string; old?: number; new?: number };

function parseDiff(diff: string): DiffRow[] {
  const rows: DiffRow[] = [];
  let o = 0;
  let n = 0;
  for (const line of diff.split("\n")) {
    if (line.startsWith("---") || line.startsWith("+++")) continue;
    if (line.startsWith("@@")) {
      const m = line.match(/-(\d+)(?:,\d+)? \+(\d+)/);
      o = Number(m?.[1] ?? 0);
      n = Number(m?.[2] ?? 0);
      rows.push({ kind: "hunk", text: line });
    } else if (line.startsWith("+")) rows.push({ kind: "add", text: line.slice(1), new: n++ });
    else if (line.startsWith("-")) rows.push({ kind: "del", text: line.slice(1), old: o++ });
    else if (line.length) rows.push({ kind: "ctx", text: line.slice(1), old: o++, new: n++ });
    else if (rows.length && o) rows.push({ kind: "ctx", text: "", old: o++, new: n++ });
  }
  while (rows.length && rows[rows.length - 1].kind === "ctx" && !rows[rows.length - 1].text) rows.pop();
  return rows;
}

const ROW_STYLE = {
  hunk: "bg-action-soft/60 text-ink-3",
  add: "bg-verified-soft text-ink",
  del: "bg-victim-soft text-ink",
  ctx: "text-ink-2",
};

function DiffView({ diff }: { diff: string }) {
  return (
    <div className="scrollbar-thin overflow-x-auto">
      <table className="w-full min-w-[620px] border-collapse font-mono text-[0.82rem] leading-6">
        <tbody>
          {parseDiff(diff).map((r, i) => (
            <tr key={i} className={ROW_STYLE[r.kind]}>
              {r.kind === "hunk" ? (
                <td colSpan={4} className="px-4 py-0.5">
                  {r.text}
                </td>
              ) : (
                <>
                  <td className="w-12 select-none border-r border-line/70 px-2 text-right text-ink-3 tabular">{r.old ?? ""}</td>
                  <td className="w-12 select-none border-r border-line/70 px-2 text-right text-ink-3 tabular">{r.new ?? ""}</td>
                  <td className={`w-6 select-none text-center font-semibold ${r.kind === "add" ? "text-verified" : r.kind === "del" ? "text-victim" : ""}`}>
                    {r.kind === "add" ? "+" : r.kind === "del" ? "−" : ""}
                  </td>
                  <td className="whitespace-pre pr-4">{r.text}</td>
                </>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function RepairScreen() {
  const { s, set, api, go } = useStore();
  const [busy, setBusy] = useState<"" | "generate" | "apply" | "revert">("");
  const [status, setStatus] = useState<{ state: StatusState; msg: string }>(() =>
    s.applied ? { state: "ok", msg: "The patch is applied. Revert restores the original file." } : { state: "idle", msg: "No patch yet." },
  );

  const decision = s.cert?.outcome?.decision;
  const polluter = s.cert?.polluter ?? "";
  const path = s.analysis && polluter ? evidencePath(s.analysis, polluter, s.target) : null;

  const header = (
    <ScreenHeader index={6} title="Repair">
      A mechanical fix derived from the certificate: capture the field before each test and restore it after. Only test code is touched.
    </ScreenHeader>
  );

  if (!s.repairOn) {
    return (
      <>
        {header}
        <Panel title="Repair is switched off">
          <p className="mb-4 text-ink-2">You turned repair off on the Target step. Turn it on to propose a patch for this case.</p>
          <Switch checked={s.repairOn} onChange={(v) => set({ repairOn: v })} label="Propose a repair" description="Runs only when the certificate is Verified." />
        </Panel>
        <FlowNav back={() => go("graph")} next={() => go("evosuite")} nextLabel="Skip to EvoSuite" />
      </>
    );
  }

  if (decision !== "verified") {
    return (
      <>
        {header}
        <div className="flex flex-col items-start gap-5 rounded-xl border border-line bg-surface p-6 sm:flex-row">
          <div className="grid size-12 shrink-0 place-items-center rounded-full bg-unresolved-soft text-unresolved">
            <Lock className="size-6" aria-hidden />
          </div>
          <div>
            <h2 className="text-lg font-semibold">Repair is gated on a Verified certificate</h2>
            <p className="mt-1 max-w-[66ch] text-ink-2">
              This case is {decision ? DECISION[decision].label : "not certified yet"}. A patch built on weaker evidence can send a developer to change the wrong
              test, with an official-looking artefact behind it. That is worse than no answer.
            </p>
            <Button className="mt-4" onClick={() => go("result")}>
              Back to the certificate
            </Button>
          </div>
        </div>
        <FlowNav back={() => go("graph")} next={() => go("evosuite")} nextLabel="Skip to EvoSuite" />
      </>
    );
  }

  const source = s.source!;

  async function generate() {
    setBusy("generate");
    setStatus({ state: "busy", msg: "Building a patch from the certificate…" });
    try {
      const p = await api.patch(source.path, source.module, false);
      set({ patch: p, verify: null });
      if (p.status === "ok") setStatus({ state: "ok", msg: `${p.added_lines} lines proposed for ${p.file?.split("/").pop()}. Only the polluter's test class changes.` });
      else setStatus({ state: "warn", msg: p.error ?? p.status });
    } catch (e) {
      setStatus({ state: "error", msg: (e as Error).message });
    } finally {
      setBusy("");
    }
  }

  async function apply() {
    setBusy("apply");
    setStatus({ state: "busy", msg: "Writing the patch…" });
    try {
      const p = await api.patch(source.path, source.module, true);
      if (p.status !== "ok") throw new Error(p.error ?? "The patch could not be applied.");
      set({ patch: p, applied: true, verify: null });
      setStatus({ state: "ok", msg: s.mode === "demo" ? "Applied for this session. The offline demo writes nothing to disk." : `Applied to ${p.file}. Revert restores it.` });
    } catch (e) {
      setStatus({ state: "error", msg: (e as Error).message });
    } finally {
      setBusy("");
    }
  }

  async function revert() {
    setBusy("revert");
    setStatus({ state: "busy", msg: "Restoring the working tree…" });
    try {
      const r = await api.revert(source.path);
      if (r.status !== "ok") throw new Error(r.error ?? "Revert failed.");
      set({ applied: false, verify: null });
      setStatus({ state: "ok", msg: "Working tree restored." });
    } catch (e) {
      setStatus({ state: "error", msg: (e as Error).message });
    } finally {
      setBusy("");
    }
  }

  const patch = s.patch?.status === "ok" ? s.patch : null;
  const policy = patch?.policy ?? [];
  const passed = policy.filter((p) => p[1]).length;

  return (
    <>
      {header}
      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.55fr)_minmax(0,1fr)]">
        <Panel
          title="Patch"
          aside={<Badge tone={s.applied ? "verified" : patch ? "action" : "neutral"}>{s.applied ? "Applied" : patch ? "Proposed" : "Not generated"}</Badge>}
          pad={false}
        >
          {patch?.diff ? (
            <>
              <p className="border-b border-line px-5 py-2.5 font-mono text-[0.85rem] text-ink-2 [overflow-wrap:anywhere]">{patch.file}</p>
              <DiffView diff={patch.diff} />
            </>
          ) : (
            <p className="px-5 py-12 text-center text-ink-3">{s.patch?.error ?? "Generate a patch to see the diff."}</p>
          )}
          <div className="border-t border-line px-5 py-4">
            <div className="flex flex-wrap items-center gap-3">
              <Button variant="primary" busy={busy === "generate"} disabled={!!busy && busy !== "generate"} onClick={generate} icon={<Wrench className="size-4" aria-hidden />}>
                {patch ? "Regenerate patch" : "Generate patch"}
              </Button>
              <Button busy={busy === "apply"} disabled={!patch || s.applied || (!!busy && busy !== "apply")} onClick={apply}>
                Apply to working tree
              </Button>
              <Button variant="ghost" busy={busy === "revert"} disabled={!s.applied || (!!busy && busy !== "revert")} onClick={revert} icon={<RotateCcw className="size-4" aria-hidden />}>
                Revert
              </Button>
            </div>
            <Status state={status.state}>{status.msg}</Status>
          </div>
        </Panel>

        <div className="min-w-0 space-y-5">
          <Panel title="Policy checks" aside={policy.length ? `${passed} of ${policy.length} passed` : undefined} pad={false}>
            {policy.length ? (
              <ul>
                {policy.map(([label, ok, detail], i) => (
                  <motion.li key={label} initial={{ opacity: 0, x: -6 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.04 }} className="flex items-start gap-3 border-b border-line px-5 py-2.5 last:border-0">
                    {ok ? <CircleCheck className="mt-0.5 size-5 shrink-0 text-verified" aria-label="Passed" /> : <CircleX className="mt-0.5 size-5 shrink-0 text-victim" aria-label="Failed" />}
                    <div className="min-w-0">
                      <p className="font-medium">{sentence(label)}</p>
                      <p className="text-sm text-ink-3 [overflow-wrap:anywhere]">{detail}</p>
                    </div>
                  </motion.li>
                ))}
              </ul>
            ) : (
              <p className="px-5 py-6 text-ink-3">Checked when the patch is generated: test code only, no assertion changed, no retries, no new dependencies.</p>
            )}
          </Panel>

          <Panel title="Why not fix the field itself">
            <p className="text-[0.95rem] text-ink-2">
              Making <code className="font-mono text-resource">{path?.resource.id ?? "the field"}</code> non-static is the durable fix, but it changes production
              code and every caller. FlakeTrace limits patches to test sources and leaves the deeper change to a person.
            </p>
          </Panel>
        </div>
      </div>

      <FlowNav back={() => go("graph")} next={() => go("verify")} nextLabel="Verify the patch" nextDisabled={!patch} hint="Generate a patch first." />
    </>
  );
}
