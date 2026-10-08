import { useState } from "react";
import { motion } from "motion/react";
import { FileArchive, FolderOpen, GitBranch, Package } from "lucide-react";
import { useStore } from "../state";
import type { SourceKind } from "../lib/api";
import { Button, Field, FlowNav, Panel, ScreenHeader, Status, inputClass, type StatusState } from "../components/ui";

const KINDS: { kind: SourceKind; title: string; desc: string; Icon: typeof Package }[] = [
  { kind: "demo", title: "Demo project", desc: "Bundled Maven module with a planted order dependence", Icon: Package },
  { kind: "local", title: "Folder on this machine", desc: "A Maven or Gradle project, git history optional", Icon: FolderOpen },
  { kind: "github", title: "GitHub repository", desc: "Shallow clone of a public repository", Icon: GitBranch },
  { kind: "zip", title: "Dataset archive", desc: "A .zip of a Java project", Icon: FileArchive },
];

const loadedMessage = (name: string, module: string, classes: number, methods: number) =>
  `Loaded ${name}. Found ${classes} test classes and ${methods} test methods in ${module}.`;

export default function SourceScreen() {
  const { s, set, api, go } = useStore();
  const [kind, setKind] = useState<SourceKind>((s.source?.kind as SourceKind | undefined) ?? "demo");
  const [value, setValue] = useState("");
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<{ state: StatusState; msg: string }>(() =>
    s.source && s.analysis
      ? { state: "ok", msg: loadedMessage(s.source.name, s.source.module, s.analysis.counts.test_classes, s.analysis.counts.test_methods) }
      : { state: "idle", msg: "Nothing loaded yet." },
  );

  const blocked = s.mode === "demo" && kind !== "demo";
  const needsValue = kind !== "demo" && !value.trim();

  async function load() {
    setBusy(true);
    setStatus({ state: "busy", msg: kind === "github" ? "Cloning the repository…" : "Reading the project…" });
    try {
      const src = await api.source(kind, value.trim());
      if (src.status !== "ok") throw new Error(src.error ?? "The project could not be loaded.");
      const git = await api.git(src.path);
      const analysis = await api.analyze(src.path, src.module);
      if (analysis.status !== "ok") throw new Error(analysis.error ?? "Static analysis failed on this project.");
      const sug = analysis.suggested;
      set({
        source: src,
        git: git.status === "ok" ? git : null,
        analysis,
        target: sug?.victim ?? analysis.test_methods[0] ?? "",
        order: sug?.order ?? [],
        scan: null,
        scanDone: false,
        scanError: null,
        cert: null,
        patch: null,
        applied: false,
        verify: null,
        evo: null,
      });
      setStatus({ state: "ok", msg: loadedMessage(src.name, src.module, analysis.counts.test_classes, analysis.counts.test_methods) });
    } catch (e) {
      setStatus({ state: "error", msg: (e as Error).message });
    } finally {
      setBusy(false);
    }
  }

  const facts: [string, number][] = s.analysis && s.source
    ? [
        ["Java files", s.source.java_files],
        ["Test files", s.source.test_files],
        ["Test methods", s.analysis.counts.test_methods],
        ["Shared static fields", s.analysis.counts.shared_statics],
      ]
    : [];

  return (
    <>
      <ScreenHeader index={1} title="Choose a project">
        FlakeTrace reads the git history and the test sources of a Java project. The bundled demo has a planted order dependence to diagnose.
      </ScreenHeader>

      <Panel title="Where the project comes from">
        <div role="radiogroup" aria-label="Project source" className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {KINDS.map((k) => {
            const on = k.kind === kind;
            return (
              <button
                key={k.kind}
                type="button"
                role="radio"
                aria-checked={on}
                onClick={() => setKind(k.kind)}
                className={`relative rounded-xl border p-4 text-left transition-colors ${on ? "border-transparent" : "border-line hover:border-line-strong hover:bg-sunken/60"}`}
              >
                {on && (
                  <motion.span
                    layoutId="source-kind"
                    className="absolute inset-0 rounded-xl border-2 border-action bg-action-soft"
                    transition={{ type: "spring", stiffness: 500, damping: 40 }}
                  />
                )}
                <span className="relative block">
                  <k.Icon className={`size-5 ${on ? "text-action" : "text-ink-3"}`} aria-hidden />
                  <span className="mt-3 block font-semibold text-ink">{k.title}</span>
                  <span className="mt-0.5 block text-sm text-ink-3">{k.desc}</span>
                </span>
              </button>
            );
          })}
        </div>

        <div className="mt-5">
          {kind === "demo" && (
            <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1 rounded-lg border border-line bg-sunken px-4 py-3">
              <code className="font-mono font-semibold">demo-project</code>
              <span className="text-sm text-ink-2">The services/user module: 5 test classes and one planted order dependence.</span>
            </div>
          )}
          {kind === "local" && (
            <Field label="Project folder" htmlFor="src-local" hint="Maven or Gradle. Git history is optional.">
              <input id="src-local" className={inputClass} placeholder="C:\projects\my-service" value={value} onChange={(e) => setValue(e.target.value)} spellCheck={false} />
            </Field>
          )}
          {kind === "github" && (
            <Field label="Repository URL" htmlFor="src-github" hint="Shallow clone of the last 50 commits.">
              <input id="src-github" className={inputClass} placeholder="https://github.com/owner/repo.git" value={value} onChange={(e) => setValue(e.target.value)} spellCheck={false} />
            </Field>
          )}
          {kind === "zip" && (
            <Field label="Archive path" htmlFor="src-zip" hint="Entries with absolute paths or .. are refused.">
              <input id="src-zip" className={inputClass} placeholder="C:\datasets\project.zip" value={value} onChange={(e) => setValue(e.target.value)} spellCheck={false} />
            </Field>
          )}
          {blocked && (
            <p className="mt-3 text-[0.93rem] text-candidate">
              The offline demo only includes the bundled project. Switch to Live backend in the header to load your own.
            </p>
          )}
        </div>

        <div className="mt-5 flex flex-wrap gap-3">
          <Button variant="primary" busy={busy} disabled={blocked || needsValue} onClick={load}>
            {busy ? "Loading" : s.source ? "Load again" : "Load project"}
          </Button>
        </div>
        <Status state={status.state}>{status.msg}</Status>
      </Panel>

      {s.source && s.analysis && (
        <div className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)]">
          <Panel
            title="Recent commits"
            aside={
              s.git ? (
                <span className="inline-flex items-center gap-1.5">
                  <GitBranch className="size-3.5" aria-hidden />
                  {s.git.branch}
                </span>
              ) : (
                "No git history"
              )
            }
          >
            {s.git?.commits.length ? (
              <ol className="-mx-2 space-y-0.5">
                {s.git.commits.map(([sha, subject, when], i) => (
                  <li key={sha} className="grid grid-cols-[auto_minmax(0,1fr)_auto] items-baseline gap-3 rounded-md px-2 py-1.5 hover:bg-sunken">
                    <code className={`font-mono text-[0.85rem] ${i === 0 ? "font-semibold text-action" : "text-ink-3"}`}>{sha}</code>
                    <span className="truncate">{subject}</span>
                    <span className="text-sm text-ink-3">{when}</span>
                  </li>
                ))}
              </ol>
            ) : (
              <p className="text-ink-3">This project has no commit history to show.</p>
            )}
          </Panel>

          <Panel title="What FlakeTrace found">
            <dl className="grid grid-cols-2 gap-x-6 gap-y-4">
              {facts.map(([k, v]) => (
                <div key={k}>
                  <dt className="text-sm text-ink-3">{k}</dt>
                  <dd className="mt-0.5 text-2xl font-semibold tabular">{v}</dd>
                </div>
              ))}
            </dl>
            <p className="mt-4 border-t border-line pt-3 text-sm text-ink-2 [overflow-wrap:anywhere]">
              Module <code className="font-mono">{s.source.module}</code> in <code className="font-mono">{s.source.path}</code>
            </p>
          </Panel>
        </div>
      )}

      <FlowNav next={() => go("target")} nextLabel="Choose the failing test" nextDisabled={!s.analysis} hint="Load a project to continue." />
    </>
  );
}
