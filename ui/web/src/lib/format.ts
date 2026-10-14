export function shortName(fq: string) {
  const [cls, method] = fq.split("#");
  const simple = cls.split(".").pop() ?? cls;
  return method ? `${simple}#${method}` : simple;
}

export const plural = (n: number, word: string) => `${n} ${word}${n === 1 ? "" : "s"}`;
