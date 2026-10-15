import { useEffect, useState, type ChangeEvent } from "react";
import { useStore } from "../state";
import { api, isBackendDown, type ReportEntry } from "../lib/api";
import { looksLikeReport, outcomeTone, type Outcome, type Report } from "../lib/report";
import { UNBUILT } from "../lib/labels";
import { NotBuilt } from "../components/NotBuilt";
import { Badge, Button, Field, FlowNav, Panel, ScreenHeader, Status, TestName, inputClass } from "../components/ui";

const TOOLS = ["java", "javac", "javap", "mvn"];

export default function SourceScreen() {
  const { s, go, setForm, load, refreshHealth } = useStore();
  const [reports, setReports] = useState<ReportEntry[]>([]);
  const [openError, setOpenError] = useState<string | null>(null);

  useEffect(() => {
    api.reports().then(setReports).catch(() => setReports([]));
  }, [s.health]);

  const openNamed = (name: string) =>
    api
      .report(name)
      .then((report) => load({ report, from: `eval/reports/${name}.json`, validated: true }))
      .catch((e: Error) => setOpenError(e.message));

  const openFile = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setOpenError(null);
    let data: unknown;
    try {
      data = JSON.parse(await file.text());
    } catch {
      setOpenError(`${file.name} is not a JSON file.`);
      return;
    }
    try {
      const check = await api.validate(data);
      if (check.valid) load({ report: data as Report, from: `Local file: ${file.name}`, validated: true });
      else setOpenError(check.message ?? "Not a valid FlakeTrace report.");
    } catch (error) {
      if (!isBackendDown(error)) setOpenError((error as Error).message);
      else if (looksLikeReport(data)) load({ report: data as Report, from: `Local file: ${file.name}`, validated: false });
      else setOpenError(`${file.name} is not a FlakeTrace report (required fields are missing).`);
    }
  };

  return (
    <>
      <ScreenHeader index={1} title="Source">
        Pick the Maven project to diagnose live, or open a report FlakeTrace already wrote.
      </ScreenHeader>
      <div className="grid gap-5">
        <Panel title="Tools on this machine">
          {s.healthError ? (
            <>
              <Status state="error" className="">{s.healthError}</Status>
              <Button size="sm" className="mt-3" onClick={refreshHealth}>Check again</Button>
            </>
          ) : !s.health ? (
            <Status state="busy" className="">Checking the backend</Status>
          ) : (
            <ul className="grid gap-1.5 font-mono text-[0.88rem]">
              {TOOLS.map((tool) => (
                <li key={tool} className="flex gap-3">
                  <span className="w-14 shrink-0">{tool}</span>
                  {s.health!.tools[tool] ? <span className="text-ink-2 [overflow-wrap:anywhere]">{s.health!.tools[tool]}</span> : <Badge tone="unresolved">not found</Badge>}
                </li>
              ))}
              <li className="flex gap-3">
                <span className="w-14 shrink-0">python</span>
                <span className="text-ink-2">{s.health.python}</span>
              </li>
            </ul>
          )}
        </Panel>

        <Panel title="Project for a live run">
          <Field label="Maven project folder (contains pom.xml)" htmlFor="project" hint="If pom.xml is missing, the runner says so on the Target step.">
            <input id="project" className={inputClass} value={s.form.project} onChange={(e) => setForm({ project: e.target.value })} />
          </Field>
          {s.health && (
            <Button size="sm" className="mt-3" onClick={() => setForm({ project: s.health!.fixture })}>
              Use the seeded fixture
            </Button>
          )}
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <NotBuilt item={UNBUILT.container} />
            <NotBuilt item={UNBUILT.remoteSource} />
          </div>
        </Panel>

        <Panel title="Open a report">
          {reports.length > 0 && (
            <ul className="mb-4 grid gap-2">
              {reports.map((r) => (
                <li key={r.name} className="flex flex-wrap items-center gap-3">
                  <Button size="sm" onClick={() => openNamed(r.name)}>{r.name}</Button>
                  <TestName fq={r.victim} role="victim" />
                  <Badge tone={outcomeTone(r.outcome as Outcome)}>{r.outcome}</Badge>
                </li>
              ))}
            </ul>
          )}
          <Field label="Or a report file from this computer" htmlFor="file">
            <input id="file" type="file" accept=".json,application/json" onChange={openFile} className="text-sm" />
          </Field>
          {openError && <Status state="error">{openError}</Status>}
        </Panel>
      </div>
      <FlowNav next={() => go("target")} nextLabel="Choose the failing test" />
    </>
  );
}
