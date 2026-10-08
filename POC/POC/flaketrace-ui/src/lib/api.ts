import recordedJson from "../data/recorded.json";
import type { Analysis, EvoParams, EvoResult, GitInfo, Health, PatchResult, Recorded, RunResult, Source, Toolchain } from "./types";
import { simulateOrder } from "./sim";
import { sleep } from "./format";

export const recorded = recordedJson as unknown as Recorded;

export type Mode = "demo" | "live";
export type SourceKind = "demo" | "local" | "github" | "zip";

export type Api = {
  health: () => Promise<Health>;
  source: (kind: SourceKind, value: string) => Promise<Source>;
  git: (repoPath: string) => Promise<GitInfo>;
  analyze: (repoPath: string, module: string) => Promise<Analysis>;
  run: (repoPath: string, order: string[], patched: boolean) => Promise<RunResult>;
  patch: (repoPath: string, module: string, apply: boolean) => Promise<PatchResult>;
  revert: (repoPath: string) => Promise<{ status: string; error?: string }>;
  evosuite: (repoPath: string, module: string, params: EvoParams, execute: boolean) => Promise<EvoResult>;
};

const START_HINT = "Start it from newPOC_Accordingtonewinstructions with: py flaketrace_backend.py";

async function get<T>(path: string, params: Record<string, string> = {}): Promise<T> {
  const qs = new URLSearchParams(params).toString();
  let res: Response;
  try {
    res = await fetch(`/api/${path}${qs ? `?${qs}` : ""}`, { cache: "no-store" });
  } catch {
    throw new Error(`The backend is not reachable. ${START_HINT}`);
  }
  if (!res.ok) throw new Error(`The backend answered HTTP ${res.status}. ${START_HINT}`);
  return (await res.json()) as T;
}

export function evoCommand(p: EvoParams, tool: Toolchain | undefined, testDir: string) {
  const parts = [
    tool?.java || "java", "-jar", tool?.evosuite_jar || "evosuite.jar",
    "-class", p.targetClass || "<class>", "-criterion", p.criteria,
    `-Dsearch_budget=${p.searchBudget}`, `-Dassertion_strategy=${p.assertionStrategy}`, `-Dtest_dir=${testDir}`,
    "-Dassertions=true", "-Djunit_check=true", "-Dminimize=true", `-seed=${p.seed}`,
  ];
  if (p.deterministic) parts.push("-Dno_runtime_dependency=true", "-Dreplace_calls=false", "-Dvirtual_fs=false", "-Dvirtual_net=false");
  return parts.join(" ");
}

const sameOrder = (a: string[], b: string[]) => a.length === b.length && a.every((x, i) => x === b[i]);

function recordedRun(order: string[], patched: boolean): RunResult | undefined {
  const keys = patched ? ["patched_order", "patched_alone", "patched_full"] : ["alone", "polluting", "full"];
  for (const k of keys) {
    const r = recorded.runs[k];
    if (r?.status === "ok" && r.order && sameOrder(r.order, order)) return r;
  }
  if (patched) return undefined;
  return recorded.scan.find((s) => s.result.order && sameOrder(s.result.order, order))?.result;
}

const live: Api = {
  health: () => get("health"),
  source: (kind, value) => get("source", kind === "demo" ? { kind } : kind === "github" ? { kind, url: value } : { kind, path: value }),
  git: (repoPath) => get("git-extract", { repoPath }),
  analyze: (repoPath, module) => get("analyze", { repoPath, module }),
  run: (repoPath, order) => get("run", { repoPath, order: order.join("\n") }),
  patch: (repoPath, module, apply) => get("patch", apply ? { repoPath, module, apply: "true" } : { repoPath, module }),
  revert: (repoPath) => get("revert", { repoPath }),
  evosuite: (repoPath, module, p, execute) =>
    get("evosuite-generate", {
      repoPath, module, targetClass: p.targetClass, searchBudget: p.searchBudget, seed: p.seed,
      criteria: p.criteria, assertionStrategy: p.assertionStrategy,
      deterministic: String(p.deterministic), execute: String(execute),
    }),
};

const demo: Api = {
  health: async () => {
    await sleep(150);
    return recorded.health;
  },
  source: async (kind) => {
    await sleep(650);
    if (kind !== "demo") throw new Error("The offline demo only includes the bundled project. Switch to Live backend to load your own.");
    return recorded.source;
  },
  git: async () => {
    await sleep(250);
    return recorded.git;
  },
  analyze: async () => {
    await sleep(300);
    return recorded.analysis;
  },
  run: async (_path, order, patched) => {
    await sleep(420);
    return recordedRun(order, patched) ?? simulateOrder(order, patched);
  },
  patch: async (_path, _module, apply) => {
    await sleep(apply ? 450 : 700);
    return { ...recorded.patch, applied: apply };
  },
  revert: async () => {
    await sleep(350);
    return { status: "ok" };
  },
  evosuite: async (_path, module, p) => {
    await sleep(500);
    return {
      ...recorded.evosuite,
      target_class: p.targetClass,
      suite_class: `${p.targetClass}_ESTest`,
      command: evoCommand(p, recorded.health.toolchain, `${recorded.source.path}/${module}/src/test/java`),
    };
  },
};

export const makeApi = (mode: Mode): Api => (mode === "live" ? live : demo);
