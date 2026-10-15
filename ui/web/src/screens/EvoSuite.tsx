import { useStore } from "../state";
import { UNBUILT } from "../lib/labels";
import { NotBuilt } from "../components/NotBuilt";
import { FlowNav, ScreenHeader } from "../components/ui";

export default function EvoSuiteScreen() {
  const { s, go } = useStore();
  return (
    <>
      <ScreenHeader index={8} title="EvoSuite" />
      <NotBuilt item={UNBUILT.evosuite} large />
      <FlowNav back={() => go("verify")} next={() => go("export")} nextLabel="Export" nextDisabled={!s.loaded} hint="Run a diagnosis or open a report first" />
    </>
  );
}
