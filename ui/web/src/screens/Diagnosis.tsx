import { useStore } from "../state";
import { toView } from "../lib/report";
import { UNBUILT } from "../lib/labels";
import { NotBuilt } from "../components/NotBuilt";
import { FlowNav, Missing, Panel, ScreenHeader, Status, TestName } from "../components/ui";

function Order({ tests, polluters, victim }: { tests: string[]; polluters: string[]; victim: string }) {
  return (
    <ol className="grid gap-1">
      {tests.map((test, i) => (
        <li key={`${test}-${i}`} className="flex items-center gap-3">
          <span className="w-6 text-right text-sm text-ink-3 tabular">{i + 1}</span>
          <TestName fq={test} role={test === victim ? "victim" : polluters.includes(test) ? "polluter" : undefined} />
        </li>
      ))}
    </ol>
  );
}

export default function DiagnosisScreen() {
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
      <ScreenHeader index={3} title="Diagnosis">
        How the runner got from the failing order to the polluters.
      </ScreenHeader>
      {!s.loaded.validated && (
        <Status state="warn" className="mb-5">
          NOT VALIDATED: the backend is not running, so this file was not checked against the report schema.
        </Status>
      )}
      <div className="grid gap-5">
        <Panel title="Report" aside={s.loaded.from}>
          <p className="text-ink-2">
            Victim <TestName fq={v.victim} role="victim" />
          </p>
        </Panel>
        <Panel title="Original failing order" aside={`${v.originalOrder.length} tests`}>
          <Order tests={v.originalOrder} polluters={v.polluters} victim={v.victim} />
        </Panel>
        <Panel title="Polluters found">
          {v.polluters.length ? (
            <ul className="grid gap-1">
              {v.polluters.map((p) => (
                <li key={p}>
                  <TestName fq={p} role="polluter" />
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-ink-2">{v.pollutersNote}</p>
          )}
        </Panel>
        <Panel title="Reduced sequence" aside={`${v.reducedSequence.length} of ${v.originalOrder.length} tests`}>
          <Order tests={v.reducedSequence} polluters={v.polluters} victim={v.victim} />
        </Panel>
        <Panel title="Order exploration">
          <p className="text-ink-2">{v.exploration}</p>
        </Panel>
        <NotBuilt item={UNBUILT.ranking} />
      </div>
      <FlowNav back={() => go("target")} next={() => go("result")} nextLabel="See the certificate" />
    </>
  );
}
