import { useStore } from "../state";
import { WILSON_FLOOR, toView } from "../lib/report";
import { Badge, FlowNav, Missing, Panel, ScreenHeader, TONE, Terminal } from "../components/ui";

function Count({ label, value, bounds }: { label: string; value: string; bounds: string }) {
  return (
    <div className="rounded-lg border border-line bg-sunken p-4">
      <p className="text-sm text-ink-3">{label}</p>
      <p className="mt-1 text-[1.8rem] font-semibold leading-none tabular">{value}</p>
      <p className="mt-1 font-mono text-[0.8rem] text-ink-2">{bounds}</p>
    </div>
  );
}

export default function CertificateScreen() {
  const { s, go } = useStore();
  if (!s.loaded)
    return (
      <Missing title="No report yet" action="Go to Source" onAction={() => go("source")}>
        Run a diagnosis or open a report first.
      </Missing>
    );
  const v = toView(s.loaded.report);
  return (
    <>
      <ScreenHeader index={4} title="Certificate">
        The outcome, how reliably the failure replays, and what the result does not cover.
      </ScreenHeader>
      <div className="grid gap-5">
        <Panel>
          <h2 className={`text-[2.2rem] font-semibold leading-none ${TONE[v.outcomeTone].text}`}>{v.outcome}</h2>
          {v.reason && <p className="mt-2 text-ink-2">{v.reason}</p>}
          <p className="mt-3 text-sm text-ink-3">
            VERIFIED needs a shared-resource edge and a Wilson lower bound of at least {WILSON_FLOOR.toFixed(2)} for the failing sequence.
          </p>
        </Panel>
        <Panel title="Reliability">
          <div className="grid gap-4 md:grid-cols-2">
            <Count label="Failing sequence fails" value={v.reproduction} bounds={v.reproductionBounds} />
            <Count label="Victim alone fails" value={v.alone} bounds={v.aloneBounds} />
          </div>
        </Panel>
        <Panel title="Failure signature">
          <p className="font-mono text-[0.9rem] [overflow-wrap:anywhere]">{v.signature}</p>
          {v.stackTrace && <Terminal className="mt-3" text={v.stackTrace} />}
        </Panel>
        <Panel title="Source integrity" aside={<Badge tone={v.integrityPassed ? "verified" : "unresolved"}>{v.integrityPassed ? "passed" : "failed"}</Badge>}>
          <p className="text-ink-2">{v.integrity}</p>
        </Panel>
        <Panel title="Limitations" aside={v.instrumentation}>
          <ul className="list-disc space-y-1 pl-5 text-ink-2">
            {v.limitations.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        </Panel>
      </div>
      <FlowNav back={() => go("diagnosis")} next={() => go("graph")} nextLabel="See the evidence" />
    </>
  );
}
