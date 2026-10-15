import { useStore } from "../state";
import { toView } from "../lib/report";
import { shortName } from "../lib/format";
import { UNBUILT } from "../lib/labels";
import { NotBuilt } from "../components/NotBuilt";
import { Trace } from "../components/Trace";
import { FlowNav, Missing, Panel, ScreenHeader, Status } from "../components/ui";

export default function GraphScreen() {
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
      <ScreenHeader index={5} title="Evidence graph">
        The shared state that links the polluter to the victim, found by static bytecode analysis.
      </ScreenHeader>
      <div className="grid gap-5">
        <Panel title="Polluter → shared state → victim">
          {v.resource && v.write && v.read ? (
            <>
              <Trace
                polluter={{ title: shortName(v.write.at), sub: v.write.cls, line: `bytecode offset ${v.write.offset}`, detail: v.write.note }}
                resource={{ title: v.resource.name, sub: v.resource.kind }}
                victim={{ title: shortName(v.read.at), sub: v.read.cls, line: `bytecode offset ${v.read.offset}`, detail: v.read.note }}
              />
              {v.polluters.length > 1 && (
                <Status state="warn">
                  This report holds one shared resource for {v.polluters.length} polluters; the limitations on the Certificate step name any others.
                </Status>
              )}
            </>
          ) : (
            <p className="text-ink-2">{v.resourceNote}</p>
          )}
        </Panel>
        <div className="grid gap-3 md:grid-cols-3">
          <NotBuilt item={UNBUILT.filesystem} />
          <NotBuilt item={UNBUILT.runtime} />
          <NotBuilt item={UNBUILT.teardown} />
        </div>
      </div>
      <FlowNav back={() => go("result")} next={() => go("repair")} nextLabel="Next" />
    </>
  );
}
