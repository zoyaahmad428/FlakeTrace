import type { Unbuilt } from "../lib/labels";

export function NotBuilt({ item, large = false }: { item: Unbuilt; large?: boolean }) {
  return (
    <div aria-disabled="true" className={`rounded-xl border-2 border-dashed border-line-strong bg-sunken ${large ? "px-6 py-10 text-center" : "p-4"}`}>
      <p className="text-[0.78rem] font-semibold tracking-wide text-ink-3">{item.label}</p>
      <p className={`mt-1 font-medium text-ink-2 ${large ? "text-lg" : ""}`}>{item.feature}</p>
      <p className="mt-1 text-sm text-ink-3">Source: {item.source}</p>
    </div>
  );
}
