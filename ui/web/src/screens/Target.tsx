import { useEffect, useState } from "react";
import { useStore } from "../state";
import { api, type JobKind, type ReportEntry } from "../lib/api";
import { WILSON_FLOOR } from "../lib/report";
import type { Form } from "../lib/request";
import { Button, Field, FlowNav, Panel, ScreenHeader, Status, Terminal, inputClass } from "../components/ui";

const FAILED_TITLE: Record<JobKind, string> = {
  input: "The runner rejected the input",
  tool: "Diagnosis could not run",
  timeout: "Diagnosis could not run",
  no_report: "The runner finished without a report",
  invalid_report: "The runner's report could not be used",
};

function Elapsed({ since }: { since: number }) {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);
  return <>{Math.round((now - since) / 1000)} s</>;
}

export default function TargetScreen() {
  const { s, go, setForm, diagnose } = useStore();
  const [fixtures, setFixtures] = useState<ReportEntry[]>([]);
  useEffect(() => {
    api.reports().then(setFixtures).catch(() => setFixtures([]));
  }, []);

  const job = s.job;
  const running = job?.state === "running";
  const blocked = s.healthError
    ? "Live runs need the backend: start ui\\start.cmd."
    : !s.health
      ? "Checking the backend."
      : s.health.missing.length
        ? `Live runs need: ${s.health.missing.join(", ")} (not found on PATH).`
        : !s.form.project.trim()
          ? "Enter the project folder on the Source step."
          : !s.form.victim.trim()
            ? "Enter the failing test."
            : null;

  return (
    <>
      <ScreenHeader index={2} title="Target">
        The failing test to diagnose. A live run starts fresh JVMs; on the fixture it has taken about one minute (50–66 s measured).
      </ScreenHeader>
      <div className="grid gap-5">
        <Panel title="Failing test">
          <div className="grid gap-4">
            <Field label="Victim test (Class#method)" htmlFor="victim">
              <input id="victim" className={inputClass} placeholder="odfixture.ConfigVictimTest#expectsDefaultMode" value={s.form.victim} onChange={(e) => setForm({ victim: e.target.value })} />
            </Field>
            {fixtures.length > 0 && (
              <Field label="Or a fixture case" htmlFor="fixture">
                <select id="fixture" className={inputClass} value="" onChange={(e) => e.target.value && setForm({ victim: e.target.value })}>
                  <option value="">Choose…</option>
                  {fixtures.map((f) => (
                    <option key={f.name} value={f.victim}>
                      {f.name}: {f.victim}
                    </option>
                  ))}
                </select>
              </Field>
            )}
            <Field label="Known failing order (optional, one Class#method per line)" htmlFor="order" hint="Without it, the runner uses the project's own order, then shuffled orders (ADR-008).">
              <textarea id="order" rows={4} className={`${inputClass} h-auto py-2`} value={s.form.order} onChange={(e) => setForm({ order: e.target.value })} />
            </Field>
          </div>
        </Panel>

        <Panel title="Replays and acceptance">
          <div className="grid gap-4 md:grid-cols-2">
            <Field label="Replays (n)" htmlFor="n" hint="Default 20. VERIFIED needs at least 19 of 20.">
              <input id="n" type="number" min={1} max={1000} className={inputClass} value={s.form.n} onChange={(e) => setForm({ n: Number(e.target.value) })} />
            </Field>
            <Field label="Wilson 95% lower bound floor" htmlFor="floor" hint="Fixed by design; not a setting.">
              <input id="floor" className={inputClass} value={WILSON_FLOOR.toFixed(2)} readOnly disabled />
            </Field>
          </div>
        </Panel>

        <Panel title="Advanced run options" aside="the command line's options and defaults">
          <details>
            <summary className="cursor-pointer text-ink-2">Search, scope, policy, budget, evidence bundle</summary>
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <Field label="Search (--search)" htmlFor="search" hint="pairs: [candidate, victim] for every test in scope, for a victim no order makes fail (ADR-016). Not with a known order.">
                <select id="search" className={inputClass} value={s.form.search} onChange={(e) => setForm({ search: e.target.value as Form["search"] })}>
                  <option value="order">order (default)</option>
                  <option value="pairs">pairs</option>
                </select>
              </Field>
              <Field label="Scope (--scope)" htmlFor="scope" hint="package: only tests in the victim's package. Not with a known order.">
                <select id="scope" className={inputClass} value={s.form.scope} onChange={(e) => setForm({ scope: e.target.value as Form["scope"] })}>
                  <option value="module">module (default)</option>
                  <option value="package">package</option>
                </select>
              </Field>
              <Field label="Policy (--policy)" htmlFor="policy" hint="The order candidates are tried in. ranked uses static evidence; a rank orders the search, it never says what caused the failure.">
                <select id="policy" className={inputClass} value={s.form.policy} onChange={(e) => setForm({ policy: e.target.value as Form["policy"] })}>
                  <option value="original">original (default)</option>
                  <option value="ranked">ranked</option>
                  <option value="random">random</option>
                </select>
              </Field>
              <Field label="Seed (--seed)" htmlFor="seed" hint="Default 0. The first shuffle seed, and the random policy's seed.">
                <input id="seed" type="number" min={0} className={inputClass} value={s.form.seed} onChange={(e) => setForm({ seed: Number(e.target.value) })} />
              </Field>
              <Field label="Shuffled orders (--shuffles)" htmlFor="shuffles" hint="Default 31: tried when the starting order never fails.">
                <input id="shuffles" type="number" min={0} className={inputClass} value={s.form.shuffles} onChange={(e) => setForm({ shuffles: Number(e.target.value) })} />
              </Field>
              <Field label="Budget: invocations (--budget-invocations)" htmlFor="budgetInvocations" hint="Empty: no limit, still counted. 3 × n are kept for verification.">
                <input id="budgetInvocations" type="number" min={1} className={inputClass} value={s.form.budgetInvocations} onChange={(e) => setForm({ budgetInvocations: e.target.value })} />
              </Field>
              <Field label="Budget: seconds (--budget-seconds)" htmlFor="budgetSeconds" hint="Empty: no limit. Stops searching; verification still runs.">
                <input id="budgetSeconds" type="number" min={0} step="any" className={inputClass} value={s.form.budgetSeconds} onChange={(e) => setForm({ budgetSeconds: e.target.value })} />
              </Field>
              <Field label="Evidence bundle (--bundle)" htmlFor="bundle" hint="Written into this run's own folder, never into the repository.">
                <label className="flex items-center gap-2 text-ink-2">
                  <input id="bundle" type="checkbox" checked={s.form.bundle} onChange={(e) => setForm({ bundle: e.target.checked })} />
                  write an evidence bundle
                </label>
              </Field>
              <Field label="Lifecycle (--lifecycle)" htmlFor="lifecycle" hint="Fixed in the UI at the command line's default (ADR-012).">
                <input id="lifecycle" className={inputClass} value="class-grouped" readOnly disabled />
              </Field>
              <Field label="Workspace (--workspace)" htmlFor="workspace" hint="Fixed in the UI at the default: a disposable copy (ADR-012).">
                <input id="workspace" className={inputClass} value="copy" readOnly disabled />
              </Field>
            </div>
          </details>
        </Panel>

        <Panel title="Run">
          <Button variant="primary" onClick={diagnose} disabled={!!blocked} busy={running}>
            Diagnose
          </Button>
          {blocked && !running && <Status state="idle">{blocked}</Status>}
          {s.health && <p className="mt-2 text-sm text-ink-3">A run is stopped after {Math.round(s.health.job_timeout_s / 60)} min.</p>}
          {s.jobError && <Status state="warn">{s.jobError}</Status>}
          {running && s.jobStartedAt !== null && (
            <>
              <Status state="busy">
                Running real JVM tests… <Elapsed since={s.jobStartedAt} />
              </Status>
              {job.command && <Terminal className="mt-3" wrap text={job.command} />}
            </>
          )}
          {job?.state === "failed" && (
            <>
              <Status state="error">
                <span className="font-medium">{FAILED_TITLE[job.kind ?? "tool"]}:</span> {job.message}
              </Status>
              {job.output_tail && <Terminal className="mt-3" wrap text={job.output_tail} />}
            </>
          )}
        </Panel>
      </div>
      <FlowNav back={() => go("source")} next={() => go("diagnosis")} nextLabel="See the diagnosis" nextDisabled={!s.loaded} hint="Run a diagnosis or open a report first" />
    </>
  );
}
