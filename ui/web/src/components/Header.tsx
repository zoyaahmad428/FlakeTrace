import { FolderGit2 } from "lucide-react";
import { useStore } from "../state";
import { shortName } from "../lib/format";
import { testName } from "../lib/report";
import lockup from "../assets/flaketrace-lockup.png";

function Connection() {
  const { s } = useStore();
  if (s.healthError)
    return (
      <span className="flex items-center gap-2 text-sm text-victim" title={s.healthError}>
        <span className="size-2 rounded-full bg-victim" />
        Backend not running
      </span>
    );
  if (!s.health) return <span className="text-sm text-ink-3">Checking backend</span>;
  const ok = s.health.missing.length === 0;
  return (
    <span className="flex items-center gap-2 text-sm text-ink-2">
      <span className={`size-2 rounded-full ${ok ? "bg-verified" : "bg-candidate"}`} />
      {ok ? "Backend connected, live runs available" : `Live runs need: ${s.health.missing.join(", ")}`}
    </span>
  );
}

export function Header() {
  const { s } = useStore();
  const loaded = s.loaded;
  return (
    <header className="sticky top-0 z-40 border-b border-line bg-surface/92 backdrop-blur">
      <div className="mx-auto flex max-w-[1320px] flex-wrap items-center gap-x-5 gap-y-2 px-4 py-2.5 md:px-6">
        <img src={lockup} alt="FlakeTrace" className="h-8 w-auto" />
        {loaded && (
          <div className="hidden min-w-0 items-center gap-2.5 rounded-full border border-line bg-sunken px-3 py-1 text-sm sm:flex">
            <FolderGit2 className="size-4 shrink-0 text-ink-3" aria-hidden />
            <span className="font-medium">{shortName(testName(loaded.report.victim))}</span>
            <span className="truncate text-ink-3">{loaded.from}</span>
          </div>
        )}
        <div className="ml-auto">
          <Connection />
        </div>
      </div>
    </header>
  );
}
