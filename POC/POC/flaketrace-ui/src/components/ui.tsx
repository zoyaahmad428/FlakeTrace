import { useState, type ButtonHTMLAttributes, type ReactNode } from "react";
import { motion } from "motion/react";
import { ArrowLeft, Check, Circle, CircleCheck, CircleX, Copy, LoaderCircle, TriangleAlert } from "lucide-react";
import { shortName } from "../lib/format";

export type Tone = "neutral" | "action" | "polluter" | "resource" | "victim" | "verified" | "candidate" | "unresolved";

export const TONE: Record<Tone, { text: string; badge: string; fill: string; soft: string }> = {
  neutral: { text: "text-ink-2", badge: "text-ink-2 bg-sunken border-line-strong", fill: "bg-ink-3", soft: "bg-sunken" },
  action: { text: "text-action", badge: "text-action bg-action-soft border-action/35", fill: "bg-action", soft: "bg-action-soft" },
  polluter: { text: "text-polluter", badge: "text-polluter bg-polluter-soft border-polluter/35", fill: "bg-polluter", soft: "bg-polluter-soft" },
  resource: { text: "text-resource", badge: "text-resource bg-resource-soft border-resource/35", fill: "bg-resource", soft: "bg-resource-soft" },
  victim: { text: "text-victim", badge: "text-victim bg-victim-soft border-victim/35", fill: "bg-victim", soft: "bg-victim-soft" },
  verified: { text: "text-verified", badge: "text-verified bg-verified-soft border-verified/35", fill: "bg-verified", soft: "bg-verified-soft" },
  candidate: { text: "text-candidate", badge: "text-candidate bg-candidate-soft border-candidate/35", fill: "bg-candidate", soft: "bg-candidate-soft" },
  unresolved: { text: "text-unresolved", badge: "text-unresolved bg-unresolved-soft border-unresolved/35", fill: "bg-unresolved", soft: "bg-unresolved-soft" },
};

export function Badge({ tone = "neutral", children, className = "" }: { tone?: Tone; children: ReactNode; className?: string }) {
  return (
    <span className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border px-2.5 py-px text-[0.8rem] font-medium leading-5 ${TONE[tone].badge} ${className}`}>
      {children}
    </span>
  );
}

type Variant = "primary" | "secondary" | "ghost";

const VARIANT: Record<Variant, string> = {
  primary: "bg-action text-white hover:bg-action-strong shadow-[0_1px_0_rgba(12,26,48,0.3)]",
  secondary: "border border-line-strong bg-surface text-ink hover:border-ink-3 hover:bg-sunken",
  ghost: "text-ink-2 hover:bg-sunken hover:text-ink",
};

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  size?: "sm" | "md";
  busy?: boolean;
  icon?: ReactNode;
};

export function Button({ variant = "secondary", size = "md", busy = false, icon, children, className = "", disabled, ...rest }: ButtonProps) {
  return (
    <button
      type="button"
      {...rest}
      disabled={disabled || busy}
      aria-busy={busy || undefined}
      className={`inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md font-medium transition-colors duration-150 active:translate-y-px disabled:cursor-not-allowed disabled:opacity-45 ${size === "sm" ? "h-8 px-3 text-sm" : "h-10 px-4"} ${VARIANT[variant]} ${className}`}
    >
      {busy ? <LoaderCircle className="size-4 animate-spin" aria-hidden /> : icon}
      {children}
    </button>
  );
}

export function Panel({ title, aside, children, className = "", pad = true }: { title?: ReactNode; aside?: ReactNode; children: ReactNode; className?: string; pad?: boolean }) {
  return (
    <section className={`min-w-0 rounded-xl border border-line bg-surface ${className}`}>
      {title && (
        <header className="flex flex-wrap items-center gap-x-3 gap-y-1 border-b border-line px-5 py-3">
          <h2 className="text-base font-semibold text-ink">{title}</h2>
          {aside && <div className="ml-auto text-sm text-ink-3">{aside}</div>}
        </header>
      )}
      <div className={pad ? "p-5" : ""}>{children}</div>
    </section>
  );
}

export type StatusState = "idle" | "busy" | "ok" | "warn" | "error";

const STATUS = {
  idle: { Icon: Circle, icon: "text-ink-3", box: "border-line bg-sunken" },
  busy: { Icon: LoaderCircle, icon: "text-action animate-spin", box: "border-action/30 bg-action-soft" },
  ok: { Icon: CircleCheck, icon: "text-verified", box: "border-verified/30 bg-verified-soft" },
  warn: { Icon: TriangleAlert, icon: "text-candidate", box: "border-candidate/30 bg-candidate-soft" },
  error: { Icon: CircleX, icon: "text-victim", box: "border-victim/30 bg-victim-soft" },
};

export function Status({ state, children, className = "mt-4" }: { state: StatusState; children: ReactNode; className?: string }) {
  const { Icon, icon, box } = STATUS[state];
  return (
    <div role="status" aria-live="polite" className={`flex items-start gap-2.5 rounded-lg border px-3.5 py-2.5 text-[0.93rem] text-ink-2 ${box} ${className}`}>
      <Icon className={`mt-0.5 size-4 shrink-0 ${icon}`} aria-hidden />
      <span className="min-w-0 break-words">{children}</span>
    </div>
  );
}

export const inputClass =
  "h-10 w-full rounded-md border border-line-strong bg-surface px-3 font-mono text-[0.9rem] text-ink placeholder:text-ink-3/70 focus:border-action focus:outline-none focus:ring-3 focus:ring-action/25";

export function Field({ label, hint, htmlFor, children }: { label: string; hint?: ReactNode; htmlFor?: string; children: ReactNode }) {
  return (
    <div className="flex min-w-0 flex-col gap-1.5">
      <label htmlFor={htmlFor} className="text-sm font-medium text-ink-2">
        {label}
      </label>
      {children}
      {hint && <p className="text-[0.85rem] text-ink-3">{hint}</p>}
    </div>
  );
}

export function Switch({ checked, onChange, label, description }: { checked: boolean; onChange: (v: boolean) => void; label: string; description?: string }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className="flex w-full items-start gap-3 rounded-lg border border-line bg-surface p-3.5 text-left transition-colors hover:border-line-strong"
    >
      <span className={`mt-0.5 inline-flex h-6 w-10 shrink-0 items-center rounded-full p-0.5 transition-colors duration-200 ${checked ? "bg-action" : "bg-line-strong"}`}>
        <motion.span layout transition={{ type: "spring", stiffness: 600, damping: 36 }} className={`size-5 rounded-full bg-white shadow ${checked ? "ml-auto" : ""}`} />
      </span>
      <span className="min-w-0">
        <span className="block font-medium text-ink">{label}</span>
        {description && <span className="block text-sm text-ink-3">{description}</span>}
      </span>
    </button>
  );
}

export function Segmented<T extends string | number>({
  value,
  options,
  onChange,
  label,
  name,
}: {
  value: T;
  options: { value: T; label: string }[];
  onChange: (v: T) => void;
  label: string;
  name: string;
}) {
  return (
    <div role="radiogroup" aria-label={label} className="inline-flex max-w-full self-start rounded-lg border border-line-strong bg-sunken p-1">
      {options.map((o) => {
        const on = o.value === value;
        return (
          <button
            key={String(o.value)}
            type="button"
            role="radio"
            aria-checked={on}
            onClick={() => onChange(o.value)}
            className={`relative h-8 rounded-md px-3 text-sm font-medium transition-colors ${on ? "text-ink" : "text-ink-3 hover:text-ink"}`}
          >
            {on && (
              <motion.span
                layoutId={`segmented-${name}`}
                className="absolute inset-0 rounded-md bg-surface shadow-sm ring-1 ring-line-strong"
                transition={{ type: "spring", stiffness: 500, damping: 40 }}
              />
            )}
            <span className="relative whitespace-nowrap">{o.label}</span>
          </button>
        );
      })}
    </div>
  );
}

export function CopyButton({ text, label = "Copy" }: { text: string; label?: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <Button
      size="sm"
      variant="ghost"
      icon={copied ? <Check className="size-4 text-verified" aria-hidden /> : <Copy className="size-4" aria-hidden />}
      onClick={() =>
        navigator.clipboard
          .writeText(text)
          .then(() => {
            setCopied(true);
            setTimeout(() => setCopied(false), 1400);
          })
          .catch(() => setCopied(false))
      }
    >
      {copied ? "Copied" : label}
    </Button>
  );
}

function lineTone(line: string) {
  if (/^\s*PASS\s/.test(line)) return "text-verified";
  if (/^\s*FAIL\s/.test(line)) return "font-medium text-victim";
  if (/^RESULT/.test(line)) return "font-semibold text-ink";
  if (/error:/i.test(line)) return "text-victim";
  return "";
}

export function Terminal({ text, wrap = false, className = "" }: { text: string; wrap?: boolean; className?: string }) {
  return (
    <pre className={`scrollbar-thin overflow-x-auto rounded-lg border border-line bg-sunken px-4 py-3 font-mono text-[0.82rem] leading-6 text-ink-2 ${className}`}>
      {text.split("\n").map((line, i) => (
        <span key={i} className={`block ${wrap ? "whitespace-pre-wrap [overflow-wrap:anywhere]" : "whitespace-pre"} ${lineTone(line)}`}>
          {line || " "}
        </span>
      ))}
    </pre>
  );
}

export function ScreenHeader({ index, title, children }: { index: number; title: string; children?: ReactNode }) {
  return (
    <div className="mb-6">
      <p className="mb-1 text-sm font-medium text-ink-3 tabular">Step {index} of 9</p>
      <h1 className="text-[1.9rem] font-semibold leading-tight tracking-[-0.015em] text-ink">{title}</h1>
      {children && <p className="mt-2 max-w-[70ch] text-[1.02rem] leading-relaxed text-ink-2">{children}</p>}
    </div>
  );
}

export function FlowNav({ back, next, nextLabel, nextDisabled, hint }: { back?: () => void; next?: () => void; nextLabel?: string; nextDisabled?: boolean; hint?: string }) {
  return (
    <div className="mt-8 flex flex-wrap items-center gap-3 border-t border-line pt-5">
      {back && (
        <Button variant="ghost" onClick={back} icon={<ArrowLeft className="size-4" aria-hidden />}>
          Back
        </Button>
      )}
      <span className="ml-auto text-sm text-ink-3">{nextDisabled ? hint : ""}</span>
      {next && (
        <Button variant="primary" onClick={next} disabled={nextDisabled}>
          {nextLabel}
        </Button>
      )}
    </div>
  );
}

const ROLE_TEXT = { polluter: "text-polluter", victim: "text-victim", resource: "text-resource" };

export function TestName({ fq, role, className = "" }: { fq: string; role?: keyof typeof ROLE_TEXT; className?: string }) {
  const [cls, method] = shortName(fq).split("#");
  return (
    <code className={`font-mono text-[0.9em] font-medium [overflow-wrap:anywhere] ${role ? ROLE_TEXT[role] : "text-ink"} ${className}`}>
      {cls}
      {method && <span className="opacity-60">#</span>}
      {method}
    </code>
  );
}

export function Missing({ title, children, action, onAction }: { title: string; children: ReactNode; action: string; onAction: () => void }) {
  return (
    <div className="rounded-xl border border-dashed border-line-strong bg-surface px-6 py-10 text-center">
      <p className="text-lg font-semibold">{title}</p>
      <p className="mx-auto mt-1 max-w-[56ch] text-ink-2">{children}</p>
      <Button className="mt-5" onClick={onAction}>
        {action}
      </Button>
    </div>
  );
}
