import { useStore } from "../state";
import { UNBUILT } from "../lib/labels";
import { NotBuilt } from "../components/NotBuilt";
import { FlowNav, ScreenHeader } from "../components/ui";

export default function VerifyScreen() {
  const { go } = useStore();
  return (
    <>
      <ScreenHeader index={7} title="Verify">
        Checking a suggested repair by re-running the tests. The 20 repeated runs of the diagnosis itself are on the Certificate step.
      </ScreenHeader>
      <NotBuilt item={UNBUILT.verify} large />
      <FlowNav back={() => go("repair")} next={() => go("evosuite")} nextLabel="Next" />
    </>
  );
}
