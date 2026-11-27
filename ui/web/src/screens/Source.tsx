import { useEffect, useState, type ChangeEvent } from "react";
import { useStore } from "../state";
import { api, isBackendDown, type ReportEntry } from "../lib/api";
import { bundleRow, committedLabel, type BundleEntry, type VerifyResult } from "../lib/bundles";
import { looksLikeReport, outcomeLabel, outcomeTone, type Outcome, type Report } from "../lib/report";
import { UNBUILT } from "../lib/labels";
import { NotBuilt } from "../components/NotBuilt";
import { Badge, Button, Field, FlowNav, Panel, ScreenHeader, Status, TestName, inputClass } from "../components/ui";

const TOOLS = ["java", "javac", "javap", "mvn"];

export default function SourceScreen() {
  const { s, go, setForm, load, refreshHealth } = useStore();
  const [reports, setReports] = useState<ReportEntry[]>([]);
  const [openError, setOpenError] = useState<string | null>(null);

  const [bundles, setBundles] = useState<BundleEntry[]>([]);
  const [opening, setOpening] = useState<string | null>(null);
  const [checkPath, setCheckPath] = useState("");
  const [checked, setChecked] = useState<VerifyResult | null>(null);

  useEffect(() => {
    api.reports().then(setReports).catch(() => setReports([]));
    api.bundles().then(setBundles).catch(() => setBundles([]));
  }, [s.health]);

  // verify runs on the server when the bundle is opened (about 3 s), never from a cache.
  const openBundle = (name: string) => {
    setOpening(name);
    setOpenError(null);
    api
      .bundle(name)
      .then((b) => load({ report: b.report, from: committedLabel(b.name, b.run_date), validated: true, verify: b.verify }))
      .catch((e: Error) => setOpenError(e.message))
      .finally(() => setOpening(null));
  };

  const checkFolder = () => {
    setChecked(null);
    api.checkBundle(checkPath.trim()).then(setChecked).catch((e: Error) => setChecked({ ok: false, problem: e.message }));
  };

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
                  <Badge tone={outcomeTone(r.outcome as Outcome)}>{outcomeLabel(r.outcome)}</Badge>
                </li>
              ))}
            </ul>
          )}
          <Field label="Or a report file from this computer" htmlFor="file">
            <input id="file" type="file" accept=".json,application/json" onChange={openFile} className="text-sm" />
          </Field>
          {openError && <Status state="error">{openError}</Status>}
        </Panel>

        <Panel title="Committed evidence" aside="eval/bundles/ — pre-run bundles, verified when opened">
          {bundles.length === 0 ? (
            <p className="text-ink-2">No committed bundles found (or the backend is not running).</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-ink-3">
                  <tr>
                    {["Open", "Victim", "Outcome", "Reproduced by", "Scope", "Policy", "Seed", "Polluter", "Invocations", "Date"].map((h) => (
                      <th key={h} className="pb-2 pr-3 font-medium">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {bundles.map((b) => {
                    const row = bundleRow(b);
                    return (
                      <tr key={row.name} className="border-t border-line align-top">
                        <td className="py-1.5 pr-3">
                          <Button size="sm" busy={opening === row.name} onClick={() => openBundle(row.name)}>{row.name.slice(0, 16)}</Button>
                        </td>
                        <td className="py-1.5 pr-3"><TestName fq={row.victim} role="victim" /></td>
                        <td className="py-1.5 pr-3"><Badge tone={outcomeTone(row.outcome as Outcome)}>{outcomeLabel(row.outcome)}</Badge></td>
                        <td className="py-1.5 pr-3">{row.reproduced}</td>
                        <td className="py-1.5 pr-3">{row.scope}</td>
                        <td className="py-1.5 pr-3">{row.policy}</td>
                        <td className="py-1.5 pr-3 tabular">{row.seed}</td>
                        <td className="py-1.5 pr-3">{row.polluter === "—" ? "—" : <TestName fq={row.polluter} role="polluter" />}</td>
                        <td className="py-1.5 pr-3 tabular">{row.invocations}</td>
                        <td className="py-1.5 pr-3 tabular">{row.date}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
          <div className="mt-5">
            <Field label="Check a bundle folder (eval.bundle verify, read-only)" htmlFor="checkPath" hint="Any folder on this computer, for example a copy you changed by hand. Nothing is written.">
              <div className="flex flex-wrap gap-2">
                <input id="checkPath" className={`${inputClass} min-w-[20rem] flex-1`} value={checkPath} onChange={(e) => setCheckPath(e.target.value)} />
                <Button size="sm" disabled={!checkPath.trim()} onClick={checkFolder}>Check</Button>
              </div>
            </Field>
            {checked && (
              <Status state={checked.ok ? "idle" : "error"}>
                {checked.ok ? "OK — the checksums match and the record recounts to the report." : checked.problem}
              </Status>
            )}
          </div>
          <div className="mt-4">
            <NotBuilt item={UNBUILT.replay} />
          </div>
        </Panel>
      </div>
      <FlowNav next={() => go("target")} nextLabel="Choose the failing test" />
    </>
  );
}
