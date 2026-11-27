import { describe, expect, it } from "vitest";
import { ApiError, BACKEND_DOWN, retryWhileDown } from "./api";

const down = () => new ApiError(0, {}, BACKEND_DOWN);
const noWait = async () => {};

describe("retryWhileDown (start.cmd opens the page before the backend is up)", () => {
  it("keeps asking while the backend is down, then returns its answer", async () => {
    let calls = 0;
    const result = await retryWhileDown(async () => {
      calls += 1;
      if (calls < 3) throw down();
      return "health";
    }, 8, noWait);
    expect([result, calls]).toEqual(["health", 3]);
  });

  it("gives up after the last attempt with the backend-down error", async () => {
    let calls = 0;
    await expect(retryWhileDown(async () => {
      calls += 1;
      throw down();
    }, 4, noWait)).rejects.toThrow(BACKEND_DOWN);
    expect(calls).toBe(4);
  });

  it("does not retry other errors", async () => {
    let calls = 0;
    await expect(retryWhileDown(async () => {
      calls += 1;
      throw new ApiError(500, {}, "boom");
    }, 8, noWait)).rejects.toThrow("boom");
    expect(calls).toBe(1);
  });
});

describe("review fix 11 (2026-11-27): a bundle name's # reaches the server", () => {
  it("encodes the name as one path segment", async () => {
    const { api } = await import("./api");
    const seen: string[] = [];
    const original = globalThis.fetch;
    globalThis.fetch = (async (url: string) => {
      seen.push(url);
      return new Response(JSON.stringify({ name: "x", run_date: null, report: {}, verify: { ok: true, problem: null } }),
                          { status: 200, headers: { "Content-Type": "application/json" } });
    }) as typeof fetch;
    try {
      await api.bundle("20261122T120044Z-a.B#c");
    } finally {
      globalThis.fetch = original;
    }
    expect(seen).toEqual(["/api/bundles/20261122T120044Z-a.B%23c"]);
  });
});
