import { FolderGit2 } from "lucide-react";
import { useStore } from "../state";
import { jdkVersion } from "../lib/format";
import { Segmented } from "./ui";
import lockup from "../assets/flaketrace-lockup.png";

function Connection() {
  const { s } = useStore();
  if (s.mode === "demo") return <span className="text-sm text-ink-3">Recorded runs of the demo project</span>;
  if (s.healthError)
    return (
      <span className="flex items-center gap-2 text-sm text-victim" title={s.healthError}>
        <span className="size-2 rounded-full bg-victim" />
        Backend not reachable
      </span>
    );
  if (!s.health) return <span className="text-sm text-ink-3">Checking backend</span>;
  const t = s.health.toolchain;
  return (
    <span className="flex items-center gap-2 text-sm text-ink-2">
      <span className="size-2 rounded-full bg-verified" />
      Backend connected, JDK {t.can_run_tests ? jdkVersion(t.java) : "missing"}
    </span>
  );
}

export function Header() {
  const { s, switchMode } = useStore();
  return (
    <header className="sticky top-0 z-40 border-b border-line bg-surface/92 backdrop-blur">
      <div className="mx-auto flex max-w-[1320px] flex-wrap items-center gap-x-5 gap-y-2 px-4 py-2.5 md:px-6">
        <img src={lockup} alt="FlakeTrace" className="h-8 w-auto" />

        {s.source && (
          <div className="hidden min-w-0 items-center gap-2.5 rounded-full border border-line bg-sunken px-3 py-1 text-sm sm:flex">
            <FolderGit2 className="size-4 shrink-0 text-ink-3" aria-hidden />
            <span className="font-medium">{s.source.name}</span>
            <span className="truncate text-ink-3">{s.source.module}</span>
            {s.git && <code className="font-mono text-[0.8rem] text-ink-2">{s.git.sha}</code>}
          </div>
        )}

        <div className="ml-auto flex items-center gap-4">
          <span className="hidden md:inline-flex">
            <Connection />
          </span>
          <Segmented
            name="mode"
            label="Data source"
            value={s.mode}
            onChange={switchMode}
            options={[
              { value: "demo", label: "Offline demo" },
              { value: "live", label: "Live backend" },
            ]}
          />
        </div>
      </div>
    </header>
  );
}
