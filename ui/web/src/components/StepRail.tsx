import { motion } from "motion/react";
import { STEPS, canVisit, summary, useStore } from "../state";

export function StepRail() {
  const { s, go } = useStore();
  const furthest = STEPS.reduce((max, step, i) => (canVisit(step.id, s) ? i : max), 0);

  return (
    <nav aria-label="Diagnosis steps">
      <div className="relative hidden lg:block">
        <div aria-hidden className="absolute bottom-6 left-[15px] top-6 w-[3px] rounded-full bg-line" />
        <motion.div
          aria-hidden
          className="absolute bottom-6 left-[15px] top-6 w-[3px] origin-top rounded-full bg-linear-to-b from-polluter via-resource to-victim"
          initial={false}
          animate={{ scaleY: furthest / (STEPS.length - 1) }}
          transition={{ type: "spring", stiffness: 110, damping: 24 }}
        />
        <ol className="relative space-y-1">
          {STEPS.map((step, i) => {
            const on = step.id === s.step;
            const ok = canVisit(step.id, s);
            return (
              <li key={step.id}>
                <button
                  type="button"
                  disabled={!ok}
                  onClick={() => go(step.id)}
                  aria-current={on ? "step" : undefined}
                  className={`flex w-full items-center gap-3 rounded-lg py-1.5 pr-2 text-left transition-colors ${on ? "" : ok ? "hover:bg-sunken" : "opacity-55"}`}
                >
                  <span
                    className={`relative grid size-[33px] shrink-0 place-items-center rounded-full border-2 text-sm font-semibold tabular transition-colors duration-200 ${
                      on
                        ? "border-action bg-action text-white shadow-[0_0_0_4px_var(--color-action-soft)]"
                        : ok
                          ? "border-ink bg-surface text-ink"
                          : "border-line-strong bg-surface text-ink-3"
                    }`}
                  >
                    {i + 1}
                  </span>
                  <span className="min-w-0">
                    <span className={`block text-[0.95rem] leading-tight ${on ? "font-semibold text-ink" : "font-medium text-ink-2"}`}>{step.label}</span>
                    <span className="block truncate text-[0.8rem] text-ink-3">{summary(step.id, s)}</span>
                  </span>
                </button>
              </li>
            );
          })}
        </ol>
      </div>

      <ol className="scrollbar-thin -mx-4 flex gap-2 overflow-x-auto px-4 pb-1 lg:hidden">
        {STEPS.map((step, i) => {
          const on = step.id === s.step;
          const ok = canVisit(step.id, s);
          return (
            <li key={step.id} className="shrink-0">
              <button
                type="button"
                disabled={!ok}
                onClick={() => go(step.id)}
                aria-current={on ? "step" : undefined}
                className={`flex h-9 items-center gap-2 rounded-full border px-3 text-sm font-medium ${
                  on ? "border-action bg-action text-white" : ok ? "border-line-strong bg-surface text-ink" : "border-line bg-surface text-ink-3 opacity-60"
                }`}
              >
                <span className="tabular">{i + 1}</span>
                {step.label}
              </button>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
