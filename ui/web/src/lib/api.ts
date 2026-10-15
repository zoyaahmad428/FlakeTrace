import type { Report } from "./report";

export type Health = { tools: Record<string, string | null>; missing: string[]; python: string; fixture: string };
export type ReportEntry = { name: string; victim: string; outcome: string };
export type JobKind = "input" | "tool" | "no_report" | "timeout" | "invalid_report";
export type Job = {
  id: string;
  state: "running" | "done" | "failed";
  started: string;
  command: string;
  records?: string;
  report?: Report;
  report_path?: string;
  kind?: JobKind;
  message?: string;
  output_tail?: string;
};
export type DiagnoseRequest = { project: string; victim: string; n: number; order?: string[] };

export const BACKEND_DOWN = "Backend not running. Start ui\\start.cmd, then press Check again.";

export class ApiError extends Error {
  status: number;
  body: Record<string, unknown>;
  constructor(status: number, body: Record<string, unknown>, message: string) {
    super(message);
    this.status = status;
    this.body = body;
  }
}

export const isBackendDown = (e: unknown) => e instanceof ApiError && e.status === 0;

const pause = (ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms));

/** Repeats `call` while the backend is unreachable: ui\start.cmd opens the page before the backend window is up. */
export async function retryWhileDown<T>(call: () => Promise<T>, attempts = 8, wait: () => Promise<void> = () => pause(2000)): Promise<T> {
  for (let attempt = 1; ; attempt++) {
    try {
      return await call();
    } catch (e) {
      if (!isBackendDown(e) || attempt >= attempts) throw e;
      await wait();
    }
  }
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`/api/${path}`, { cache: "no-store", ...init });
  } catch {
    throw new ApiError(0, {}, BACKEND_DOWN);
  }
  const body = (await res.json().catch(() => null)) as Record<string, unknown> | null;
  // The Vite dev server answers without JSON when the backend behind /api is not running.
  if (body === null) throw new ApiError(0, {}, BACKEND_DOWN);
  if (!res.ok) throw new ApiError(res.status, body, String(body.message ?? body.error ?? `HTTP ${res.status}`));
  return body as T;
}

const post = <T,>(path: string, data: unknown) =>
  call<T>(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });

export const api = {
  health: () => call<Health>("health"),
  reports: () => call<ReportEntry[]>("reports"),
  report: (name: string) => call<Report>(`reports/${encodeURIComponent(name)}`),
  diagnose: (req: DiagnoseRequest) => post<{ job_id: string }>("diagnose", req),
  job: (id: string) => call<Job>(`jobs/${encodeURIComponent(id)}`),
  validate: (report: unknown) => post<{ valid: boolean; message: string | null }>("validate", report),
};
