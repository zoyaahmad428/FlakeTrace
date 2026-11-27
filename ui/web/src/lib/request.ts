import type { DiagnoseRequest } from "./api";

// The Target form. Run options carry the CLI's names and defaults (UI demo design, goal 1); budgets are the
// text of their boxes, so an empty box can mean "no limit".
export type Form = {
  project: string; victim: string; n: number; order: string;
  search: "order" | "pairs"; scope: "module" | "package"; policy: "original" | "ranked" | "random";
  // Number boxes are kept as their text: a cleared box means "the CLI's default", never 0 (review, 2026-11-27).
  seed: string; shuffles: string; budgetInvocations: string; budgetSeconds: string; bundle: boolean;
};

export const DEFAULT_FORM: Form = {
  project: "", victim: "", n: 20, order: "", search: "order", scope: "module", policy: "original", seed: "0",
  shuffles: "31", budgetInvocations: "", budgetSeconds: "", bundle: false,
};

export const orderLines = (text: string) => text.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);

// Only what differs from the CLI's default is sent, so the server adds no flag the user did not choose.
export function toRequest(form: Form): DiagnoseRequest {
  const order = orderLines(form.order);
  const req: DiagnoseRequest = { project: form.project.trim(), victim: form.victim.trim(), n: form.n };
  if (order.length) req.order = order;
  if (form.search !== DEFAULT_FORM.search) req.search = form.search;
  if (form.scope !== DEFAULT_FORM.scope) req.scope = form.scope;
  if (form.policy !== DEFAULT_FORM.policy) req.policy = form.policy;
  const chosen = (text: string, fallback: string) => (text.trim() && text.trim() !== fallback ? Number(text) : null);
  const seed = chosen(form.seed, DEFAULT_FORM.seed);
  const shuffles = chosen(form.shuffles, DEFAULT_FORM.shuffles);
  if (seed !== null) req.seed = seed;
  if (shuffles !== null) req.shuffles = shuffles;
  if (form.budgetInvocations.trim()) req.budget_invocations = Number(form.budgetInvocations);
  if (form.budgetSeconds.trim()) req.budget_seconds = Number(form.budgetSeconds);
  if (form.bundle) req.bundle = true;
  return req;
}
