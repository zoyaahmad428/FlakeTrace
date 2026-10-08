import type { RunResult } from "./types";
import { shortName } from "./format";

const REJECT = "com.example.UserServiceTest#shouldRejectAnonymousUser";
const NAME = "com.example.UserServiceTest#shouldNameAnonymousPrincipal";
const WRITERS: Record<string, string> = {
  "com.example.LoginTest#shouldLoginUser": "ada",
  "com.example.LoginTest#shouldReportAuthenticatedRole": "grace",
};
const CLEANERS = new Set(["com.example.SessionTest#shouldExpireStaleSession"]);

export function simulateOrder(order: string[], patched: boolean): RunResult {
  let user: string | null = null;
  const lines: string[] = [];
  const failures: string[] = [];

  for (const test of order) {
    const label = shortName(test);
    let failure: string | null = null;
    if (test in WRITERS) user = patched ? null : WRITERS[test];
    else if (CLEANERS.has(test)) user = null;
    else if (test === REJECT && user) failure = "java.lang.AssertionError: expected: <ANONYMOUS> but was: <AUTHENTICATED>";
    else if (test === NAME && user) failure = `java.lang.AssertionError: expected: <anonymous> but was: <${user}>`;

    if (failure) {
      lines.push(`  FAIL  ${label}  -> ${failure}`);
      failures.push(label);
    } else {
      lines.push(`  PASS  ${label}`);
    }
  }

  lines.push("", failures.length ? `RESULT: ${failures.length} failed -> [${failures.join(", ")}]` : "RESULT: all passed");
  return {
    status: "ok",
    order,
    exit_code: failures.length ? 1 : 0,
    passed: failures.length === 0,
    output: lines.join("\n").trim(),
    command: `java -cp build/classes FlakeDemo ${order.join(" ")}`,
  };
}
