import { useStore } from "../state";
import { UNBUILT } from "../lib/labels";
import { NotBuilt } from "../components/NotBuilt";
import { FlowNav, ScreenHeader } from "../components/ui";

export default function RepairScreen() {
  const { go } = useStore();
  return (
    <>
      <ScreenHeader index={6} title="Repair" />
      <NotBuilt item={UNBUILT.repair} large />
      <FlowNav back={() => go("graph")} next={() => go("verify")} nextLabel="Next" />
    </>
  );
}
