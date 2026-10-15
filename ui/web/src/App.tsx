import { useEffect, type ComponentType } from "react";
import { AnimatePresence, MotionConfig, motion } from "motion/react";
import { StoreProvider, useStore, type StepId } from "./state";
import { Header } from "./components/Header";
import { StepRail } from "./components/StepRail";
import SourceScreen from "./screens/Source";
import TargetScreen from "./screens/Target";
import DiagnosisScreen from "./screens/Diagnosis";
import CertificateScreen from "./screens/Certificate";
import GraphScreen from "./screens/Graph";
import RepairScreen from "./screens/Repair";
import VerifyScreen from "./screens/Verify";
import EvoSuiteScreen from "./screens/EvoSuite";
import ExportScreen from "./screens/Export";

const SCREENS: Record<StepId, ComponentType> = {
  source: SourceScreen,
  target: TargetScreen,
  diagnosis: DiagnosisScreen,
  result: CertificateScreen,
  graph: GraphScreen,
  repair: RepairScreen,
  verify: VerifyScreen,
  evosuite: EvoSuiteScreen,
  export: ExportScreen,
};

function Shell() {
  const { s } = useStore();
  const Screen = SCREENS[s.step];

  useEffect(() => {
    window.scrollTo({ top: 0 });
  }, [s.step]);

  return (
    <div className="min-h-screen">
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-3 focus:z-50 focus:rounded-md focus:bg-surface focus:px-3 focus:py-2">
        Skip to content
      </a>
      <Header />
      <div className="mx-auto max-w-[1320px] px-4 py-5 md:px-6 lg:grid lg:grid-cols-[236px_minmax(0,1fr)] lg:gap-10 lg:py-8">
        <aside className="mb-5 lg:sticky lg:top-[84px] lg:mb-0 lg:self-start">
          <StepRail />
        </aside>
        <main id="main" className="min-w-0">
          <AnimatePresence mode="wait" initial={false}>
            <motion.div
              key={s.step}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
            >
              <Screen />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <MotionConfig reducedMotion="user">
      <StoreProvider>
        <Shell />
      </StoreProvider>
    </MotionConfig>
  );
}
