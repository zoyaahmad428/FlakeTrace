export const sleep = (ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms));

export function shortName(fq: string) {
  const [cls, method] = fq.split("#");
  const simple = cls.split(".").pop() ?? cls;
  return method ? `${simple}#${method}` : simple;
}

export function simpleClass(fq: string) {
  return fq.split("#")[0].split(".").pop() ?? fq;
}

export function methodName(fq: string) {
  return fq.split("#")[1] ?? "";
}

export function failureSignature(output: string | undefined, target: string): string | null {
  if (!output) return null;
  const label = shortName(target);
  const line = output.split("\n").find((l) => /^\s*FAIL\s/.test(l) && l.includes(label));
  if (!line) return null;
  const cause = line.split("->")[1]?.trim();
  return cause ? cause.replace(/0x[0-9a-f]+/gi, "<hex>").replace(/\d+/g, "#") : "failure without a message";
}

export const reproduces = (output: string | undefined, target: string) => failureSignature(output, target) !== null;

export function jdkVersion(javaPath: string | undefined) {
  if (!javaPath) return "not found";
  return javaPath.match(/jdk-?([\d.]+)/i)?.[1] ?? "on PATH";
}

export const sentence = (text: string) => text.charAt(0).toUpperCase() + text.slice(1);

export const plural = (n: number, word: string) => `${n} ${word}${n === 1 ? "" : "s"}`;
