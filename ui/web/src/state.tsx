import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { api, ApiError, retryWhileDown, type Health, type Job } from "./lib/api";
import { DEFAULT_FORM, toRequest, type Form } from "./lib/request";
import type { VerifyResult } from "./lib/bundles";
import { outcomeText, resourceName, testName, type Report } from "./lib/report";
import { plural, shortName } from "./lib/format";

export type StepId = "source" | "target" | "diagnosis" | "result" | "graph" | "repair" | "verify" | "evosuite" | "export";

export const STEPS: { id: StepId; label: string }[] = [
  { id: "source", label: "Source" },
  { id: "target", label: "Target" },
  { id: "diagnosis", label: "Diagnosis" },
  { id: "result", label: "Certificate" },
  { id: "graph", label: "Evidence graph" },
  { id: "repair", label: "Repair" },
  { id: "verify", label: "Verify" },
  { id: "evosuite", label: "EvoSuite" },
  { id: "export", label: "Export" },
];

// `verify`: eval.bundle's own check, run when a committed bundle is opened (UI demo design, goal 4).
export type Loaded = { report: Report; from: string; validated: boolean; verify?: VerifyResult };
export type { Form };

export type State = {
  step: StepId;
  health: Health | null;
  healthError: string | null;
  form: Form;
  loaded: Loaded | null;
  job: Job | null;
  jobStartedAt: number | null;
  jobError: string | null;
};

const NEEDS_REPORT: StepId[] = ["diagnosis", "result", "graph", "export"];
const POLL_MS = 2000;

export const canVisit = (step: StepId, s: State) => !NEEDS_REPORT.includes(step) || s.loaded !== null;

export function summary(step: StepId, s: State): string {
  const r = s.loaded?.report;
  switch (step) {
    case "source":
      return s.healthError ? "Backend not running" : !s.health ? "Checking tools" : s.health.missing.length ? `Missing: ${s.health.missing.join(", ")}` : "Tools found";
    case "target":
      return s.job?.state === "running" ? "Diagnosis running" : r ? shortName(testName(r.victim)) : "Choose the failing test";
    case "diagnosis":
      return r ? plural(r.polluters.length, "polluter") : "No report yet";
    case "result":
      return r ? outcomeText(r) : "No report yet";
    case "graph":
      return r ? (r.shared_resource ? resourceName(r.shared_resource) : "No shared resource") : "No report yet";
    case "export":
      return r ? "Report JSON" : "No report yet";
    default:
      return "Not built";
  }
}


type Store = {
  s: State;
  go: (step: StepId) => void;
  setForm: (patch: Partial<Form>) => void;
  load: (loaded: Loaded) => void;
  diagnose: () => void;
  refreshHealth: () => void;
};

const initial: State = {
  step: "source",
  health: null,
  healthError: null,
  form: DEFAULT_FORM,
  loaded: null,
  job: null,
  jobStartedAt: null,
  jobError: null,
};

const StoreContext = createContext<Store | null>(null);

export function StoreProvider({ children }: { children: ReactNode }) {
  const [s, setState] = useState<State>(initial);
  const current = useRef(s);
  current.current = s;
  const alive = useRef(true);
  // Set on every mount: StrictMode mounts twice in development, and a flag left false would drop poll results.
  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
    };
  }, []);

  const set = useCallback((patch: Partial<State>) => setState((prev) => ({ ...prev, ...patch })), []);
  const go = useCallback((step: StepId) => setState((prev) => (canVisit(step, prev) ? { ...prev, step } : prev)), []);
  const setForm = useCallback((patch: Partial<Form>) => setState((prev) => ({ ...prev, form: { ...prev.form, ...patch } })), []);
  const load = useCallback((loaded: Loaded) => setState((prev) => ({ ...prev, loaded, step: "diagnosis" })), []);

  const refreshHealth = useCallback(() => {
    set({ health: null, healthError: null });
    retryWhileDown(api.health)
      .then((health) => set({ health, healthError: null }))
      .catch((e: Error) => set({ health: null, healthError: e.message }));
  }, [set]);

  useEffect(refreshHealth, [refreshHealth]);

  const poll = useCallback(
    function poll(id: string) {
      api
        .job(id)
        .then((job) => {
          if (!alive.current) return;
          if (job.state === "running") {
            set({ job });
            setTimeout(() => poll(id), POLL_MS);
          } else if (job.state === "done" && job.report) {
            setState((prev) => ({ ...prev, job, loaded: { report: job.report!, from: `Live run: ${job.report_path}${job.bundle ? ` · bundle: ${job.bundle.path}` : ""}`, validated: true }, step: "diagnosis" }));
          } else {
            set({ job });
          }
        })
        .catch((e: Error) => {
          if (!alive.current) return;
          const restarted = e instanceof ApiError && e.status === 404;
          set({ job: null, jobError: restarted ? "The backend restarted, so this run's result is lost. Start the diagnosis again." : e.message });
        });
    },
    [set],
  );

  const diagnose = useCallback(() => {
    const { form } = current.current;
    const req = toRequest(form);
    set({ job: null, jobError: null });
    api
      .diagnose(req)
      .then(({ job_id }) => {
        set({ jobStartedAt: Date.now(), job: { id: job_id, state: "running", started: "", command: "" } });
        poll(job_id);
      })
      .catch((e: Error) => {
        const busy = e instanceof ApiError && e.status === 409;
        set({ jobError: busy ? `A diagnosis is already running (started ${String((e as ApiError).body.started)}).` : e.message });
      });
  }, [poll, set]);

  const value = useMemo(() => ({ s, go, setForm, load, diagnose, refreshHealth }), [s, go, setForm, load, diagnose, refreshHealth]);
  return <StoreContext.Provider value={value}>{children}</StoreContext.Provider>;
}

export function useStore() {
  const store = useContext(StoreContext);
  if (!store) throw new Error("useStore must be used inside StoreProvider");
  return store;
}
