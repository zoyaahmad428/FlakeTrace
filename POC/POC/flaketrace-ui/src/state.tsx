import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { makeApi, type Api, type Mode } from "./lib/api";
import type { Analysis, EvoResult, GitInfo, Health, PatchResult, RunResult, Source } from "./lib/types";
import { DECISION, costModel, type CertOutcome, type CostLine } from "./lib/certificate";
import type { PlannedCandidate } from "./lib/evidence";
import { shortName } from "./lib/format";

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

export type Scenario = "planted" | "hidden" | "flaky" | "unstable";

export const SCENARIOS: { value: Scenario; title: string; desc: string }[] = [
  { value: "planted", title: "Planted bug", desc: "Replays follow the recorded runs exactly." },
  { value: "hidden", title: "Write not observable", desc: "As if the write went through reflection. The order still replays." },
  { value: "flaky", title: "Nondeterministic replays", desc: "The same order reproduces only some of the time." },
  { value: "unstable", title: "Unstable build", desc: "The target sometimes fails with nothing run before it." },
];

export type ScanRow = PlannedCandidate & { result: RunResult; reproduced: boolean };

export type CertRun = {
  status: "running" | "done";
  scenario: Scenario;
  polluter: string;
  order: string[];
  controls: boolean[];
  replays: boolean[];
  signature: string | null;
  alone?: RunResult;
  polluting?: RunResult;
  outcome: CertOutcome | null;
  cost: CostLine[];
  deletionMinimal: boolean;
  resourceSupported: boolean;
  issuedAt: string;
  wallMs: number;
  error?: string;
};

export type VerifyRun = { status: "running" | "done"; order?: RunResult; alone?: RunResult; full?: RunResult };

export type State = {
  mode: Mode;
  step: StepId;
  health: Health | null;
  healthError: string | null;
  source: Source | null;
  git: GitInfo | null;
  analysis: Analysis | null;
  target: string;
  order: string[];
  budget: number;
  replays: number;
  threshold: number;
  scenario: Scenario;
  repairOn: boolean;
  evoOn: boolean;
  scan: ScanRow[] | null;
  scanDone: boolean;
  scanError: string | null;
  cert: CertRun | null;
  patch: PatchResult | null;
  applied: boolean;
  verify: VerifyRun | null;
  evo: EvoResult | null;
};

const initialState = (mode: Mode): State => ({
  mode,
  step: "source",
  health: null,
  healthError: null,
  source: null,
  git: null,
  analysis: null,
  target: "",
  order: [],
  budget: 400,
  replays: mode === "live" ? 5 : 20,
  threshold: 0.7,
  scenario: "planted",
  repairOn: true,
  evoOn: false,
  scan: null,
  scanDone: false,
  scanError: null,
  cert: null,
  patch: null,
  applied: false,
  verify: null,
  evo: null,
});

export const activeScenario = (s: State): Scenario => (s.mode === "demo" ? s.scenario : "planted");

export function planCost(s: State) {
  const candidates = s.analysis ? Math.max(0, s.analysis.test_methods.length - 1) : 0;
  return costModel({ candidates, controls: s.replays, replays: s.replays, orderLength: 2 });
}

export const verifyPassed = (v: VerifyRun | null) => !!(v?.order?.passed && v.alone?.passed && v.full?.passed);

export function canVisit(step: StepId, s: State): boolean {
  switch (step) {
    case "source":
      return true;
    case "target":
      return !!s.analysis;
    case "diagnosis":
      return !!s.analysis && !!s.target;
    case "result":
    case "graph":
      return s.scanDone;
    case "repair":
    case "evosuite":
    case "export":
      return s.cert?.status === "done";
    case "verify":
      return s.patch?.status === "ok";
  }
}

export function summary(step: StepId, s: State): string {
  switch (step) {
    case "source":
      return s.source ? `${s.source.name}` : "Not loaded";
    case "target":
      return s.target ? shortName(s.target) : "Not chosen";
    case "diagnosis":
      if (s.scanError) return "Stopped";
      if (s.scanDone) return s.scan?.some((r) => r.reproduced) ? "Polluter found" : "No polluter found";
      return s.scan ? "Running" : "Not run";
    case "result":
      if (s.cert?.outcome) return DECISION[s.cert.outcome.decision].label;
      return s.cert?.status === "running" ? "Replaying" : "Not issued";
    case "graph":
      return s.analysis ? `${s.analysis.findings.length} shared resource${s.analysis.findings.length === 1 ? "" : "s"}` : "";
    case "repair":
      if (!s.repairOn) return "Switched off";
      if (s.cert?.outcome?.decision !== "verified") return "Gated";
      return s.applied ? "Applied" : s.patch?.status === "ok" ? "Proposed" : "Not generated";
    case "verify":
      if (s.verify?.status === "done") return verifyPassed(s.verify) ? "Passed" : "Failed";
      return s.verify ? "Running" : "Not run";
    case "evosuite":
      return s.evo ? s.evo.status.replace("_", " ") : s.evoOn ? "Ready" : "Optional";
    case "export":
      return "Case as JSON";
  }
}

type Patch = Partial<State> | ((prev: State) => Partial<State>);

type Store = {
  s: State;
  set: (p: Patch) => void;
  api: Api;
  go: (step: StepId) => void;
  switchMode: (mode: Mode) => void;
};

const StoreContext = createContext<Store | null>(null);

export function StoreProvider({ children }: { children: ReactNode }) {
  const [s, setState] = useState<State>(() => initialState("demo"));
  const set = useCallback((p: Patch) => setState((prev) => ({ ...prev, ...(typeof p === "function" ? p(prev) : p) })), []);
  const go = useCallback((step: StepId) => setState((prev) => (canVisit(step, prev) ? { ...prev, step } : prev)), []);
  const switchMode = useCallback((mode: Mode) => setState((prev) => (prev.mode === mode ? prev : initialState(mode))), []);
  const api = useMemo(() => makeApi(s.mode), [s.mode]);

  useEffect(() => {
    let alive = true;
    api
      .health()
      .then((health) => alive && set({ health, healthError: null }))
      .catch((e: Error) => alive && set({ health: null, healthError: e.message }));
    return () => {
      alive = false;
    };
  }, [api, set]);

  const value = useMemo(() => ({ s, set, api, go, switchMode }), [s, set, api, go, switchMode]);
  return <StoreContext.Provider value={value}>{children}</StoreContext.Provider>;
}

export function useStore() {
  const store = useContext(StoreContext);
  if (!store) throw new Error("useStore must be used inside StoreProvider");
  return store;
}
