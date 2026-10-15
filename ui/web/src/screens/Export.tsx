import { useStore } from "../state";
import { Button, CopyButton, FlowNav, Missing, Panel, ScreenHeader, Terminal } from "../components/ui";

export default function ExportScreen() {
  const { s, go } = useStore();
  if (!s.loaded)
    return (
      <Missing title="No report yet" action="Go to Source" onAction={() => go("source")}>
        Run a diagnosis or open a report first.
      </Missing>
    );
  const json = JSON.stringify(s.loaded.report, null, 2);
  const download = () => {
    const url = URL.createObjectURL(new Blob([`${json}\n`], { type: "application/json" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = "flaketrace-report.json";
    link.click();
    URL.revokeObjectURL(url);
  };
  return (
    <>
      <ScreenHeader index={9} title="Export">
        The report's content, as the runner wrote it.
      </ScreenHeader>
      <Panel
        title="Report JSON"
        aside={
          <span className="flex gap-2">
            <CopyButton text={json} label="Copy JSON" />
            <Button size="sm" onClick={download}>Download</Button>
          </span>
        }
      >
        <Terminal text={json} className="max-h-[60vh]" />
      </Panel>
      <FlowNav back={() => go("evosuite")} />
    </>
  );
}
