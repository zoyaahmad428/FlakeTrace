import { useId } from "react";
import { motion } from "motion/react";
import { EyeOff, OctagonX, PenLine, Variable } from "lucide-react";

export type TraceEnd = { title: string; sub?: string; line?: string; detail?: string };

const ROLE = {
  polluter: { label: "Polluter", Icon: PenLine, box: "border-polluter bg-polluter-soft", text: "text-polluter", hex: "#c2410c" },
  resource: { label: "Shared state", Icon: Variable, box: "border-resource bg-resource-soft", text: "text-resource", hex: "#0f766e" },
  victim: { label: "Victim", Icon: OctagonX, box: "border-victim bg-victim-soft", text: "text-victim", hex: "#be123c" },
};

const EASE = [0.16, 1, 0.3, 1] as const;

function Node({ role, end, hidden }: { role: keyof typeof ROLE; end: TraceEnd; hidden?: boolean }) {
  if (hidden) {
    return (
      <div className="min-w-0 rounded-xl border-2 border-dashed border-line-strong bg-sunken p-4">
        <div className="flex items-center gap-2 text-sm font-semibold text-ink-3">
          <EyeOff className="size-4" aria-hidden />
          Not observed
        </div>
        <p className="mt-1.5 text-sm text-ink-2">{end.detail}</p>
      </div>
    );
  }
  const r = ROLE[role];
  return (
    <div className={`min-w-0 rounded-xl border-2 p-4 ${r.box}`}>
      <div className={`flex items-center gap-2 text-sm font-semibold ${r.text}`}>
        <r.Icon className="size-4" aria-hidden />
        {r.label}
      </div>
      <p className="mt-2 font-mono text-[1rem] font-semibold leading-snug text-ink [overflow-wrap:anywhere]">{end.title}</p>
      {end.sub && <p className="font-mono text-[0.82rem] text-ink-2 [overflow-wrap:anywhere]">{end.sub}</p>}
      {end.line && <p className="mt-1 font-mono text-[0.8rem] text-ink-3">{end.line}</p>}
      {end.detail && <p className="mt-2 text-sm text-ink-2">{end.detail}</p>}
    </div>
  );
}

function Link({ from, to, label, delay, dashed }: { from: string; to: string; label: string; delay: number; dashed?: boolean }) {
  const id = useId().replace(/:/g, "");
  const draw = dashed
    ? { initial: { opacity: 0 }, animate: { opacity: 1 } }
    : { initial: { pathLength: 0 }, animate: { pathLength: 1 } };
  return (
    <div className="flex flex-col items-center justify-center py-1 md:w-24 md:px-1 md:py-0">
      <span className="text-center text-[0.8rem] font-medium leading-tight text-ink-2 md:mb-1.5">{label}</span>
      <svg viewBox="0 0 120 16" className="hidden h-4 w-full md:block" aria-hidden>
        <defs>
          <linearGradient id={`h${id}`} gradientUnits="userSpaceOnUse" x1="4" y1="8" x2="106" y2="8">
            <stop offset="0" stopColor={from} />
            <stop offset="1" stopColor={to} />
          </linearGradient>
        </defs>
        <motion.path
          d="M4 8 H104"
          stroke={`url(#h${id})`}
          strokeWidth="3.5"
          strokeLinecap="round"
          strokeDasharray={dashed ? "6 6" : undefined}
          fill="none"
          {...draw}
          transition={{ duration: 0.5, delay, ease: EASE }}
        />
        <motion.path d="M103 2 L116 8 L103 14 Z" fill={to} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: delay + 0.4 }} />
      </svg>
      <svg viewBox="0 0 16 44" className="h-11 w-4 md:hidden" aria-hidden>
        <defs>
          <linearGradient id={`v${id}`} gradientUnits="userSpaceOnUse" x1="8" y1="2" x2="8" y2="34">
            <stop offset="0" stopColor={from} />
            <stop offset="1" stopColor={to} />
          </linearGradient>
        </defs>
        <motion.path
          d="M8 2 V31"
          stroke={`url(#v${id})`}
          strokeWidth="3.5"
          strokeLinecap="round"
          strokeDasharray={dashed ? "5 5" : undefined}
          fill="none"
          {...draw}
          transition={{ duration: 0.5, delay, ease: EASE }}
        />
        <motion.path d="M2 30 L8 42 L14 30 Z" fill={to} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: delay + 0.4 }} />
      </svg>
    </div>
  );
}

export function Trace({ polluter, resource, victim, hiddenResource }: { polluter: TraceEnd; resource: TraceEnd; victim: TraceEnd; hiddenResource?: boolean }) {
  const mid = hiddenResource ? "#a9b4c4" : ROLE.resource.hex;
  return (
    <div
      role="img"
      aria-label={`${polluter.title}${polluter.sub ?? ""} writes ${hiddenResource ? "unobserved state" : resource.title}, which ${victim.title}${victim.sub ?? ""} reads`}
      className="grid items-stretch md:grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)_auto_minmax(0,1fr)]"
    >
      <Node role="polluter" end={polluter} />
      <Link from={ROLE.polluter.hex} to={mid} label={hiddenResource ? "effect observed" : "writes, never restores"} delay={0.15} dashed={hiddenResource} />
      <Node role="resource" end={resource} hidden={hiddenResource} />
      <Link from={mid} to={ROLE.victim.hex} label={hiddenResource ? "breaks" : "read by"} delay={0.6} dashed={hiddenResource} />
      <Node role="victim" end={victim} />
    </div>
  );
}
