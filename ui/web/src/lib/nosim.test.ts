import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const SRC = fileURLToPath(new URL("..", import.meta.url));
const SELF = fileURLToPath(import.meta.url);

function files(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    return statSync(path).isDirectory() ? files(path) : [path];
  });
}

describe("no simulated or recorded POC data (ADR-009)", () => {
  it("has none of the POC's data or decision files", () => {
    for (const file of ["lib/sim.ts", "data/recorded.json", "lib/certificate.ts", "lib/evidence.ts"]) {
      expect(existsSync(join(SRC, file)), file).toBe(false);
    }
  });

  it("never names the POC's simulator, recording or replay formula", () => {
    for (const file of files(SRC).filter((p) => p !== SELF && /\.(ts|tsx)$/.test(p))) {
      const text = readFileSync(file, "utf-8");
      for (const word of ["simulateOrder", "recorded.json", "flakyReproduces"]) {
        expect(text.includes(word), `${word} in ${file}`).toBe(false);
      }
    }
  });
});
