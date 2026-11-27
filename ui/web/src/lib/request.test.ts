import { describe, expect, it } from "vitest";
import { DEFAULT_FORM, toRequest, type Form } from "./request";

const form = (patch: Partial<Form> = {}): Form => ({ ...DEFAULT_FORM, project: " p ", victim: " a.B#c ", ...patch });

describe("the diagnose request (UI demo design, goal 1)", () => {
  it("sends only project, victim and n when every option is at the CLI's default", () => {
    expect(toRequest(form())).toEqual({ project: "p", victim: "a.B#c", n: 20 });
  });

  it("uses the server's field names for every option that differs from its default", () => {
    expect(toRequest(form({ search: "pairs", scope: "package", policy: "random", seed: "3", shuffles: "5",
                            budgetInvocations: "80", budgetSeconds: "2.5", bundle: true }))).toEqual({
      project: "p", victim: "a.B#c", n: 20, search: "pairs", scope: "package", policy: "random", seed: 3, shuffles: 5,
      budget_invocations: 80, budget_seconds: 2.5, bundle: true,
    });
  });

  it("sends an empty budget box as no limit, never 0 or an empty string", () => {
    const req = toRequest(form({ budgetInvocations: "  ", budgetSeconds: "" }));
    expect("budget_invocations" in req || "budget_seconds" in req).toBe(false);
  });

  it("sends the known order as a list of lines", () => {
    expect(toRequest(form({ order: "x.Y#z\n\n a.B#c \n" })).order).toEqual(["x.Y#z", "a.B#c"]);
  });

  it("starts at the CLI's defaults", () => {
    expect(DEFAULT_FORM).toEqual({ project: "", victim: "", n: 20, order: "", search: "order", scope: "module",
      policy: "original", seed: "0", shuffles: "31", budgetInvocations: "", budgetSeconds: "", bundle: false });
  });
});

describe("review fix 7 (2026-11-27): a cleared box is the default, never 0", () => {
  it("leaves out a cleared seed or shuffles box, so the CLI's default applies", () => {
    const req = toRequest(form({ seed: "", shuffles: " " }));
    expect("seed" in req || "shuffles" in req).toBe(false);
  });

  it("still sends shuffles 0 when 0 is typed", () => {
    expect(toRequest(form({ shuffles: "0" })).shuffles).toBe(0);
  });
});
