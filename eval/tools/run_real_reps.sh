#!/bin/bash
# Runs od-fixture's cases 20 times each via plain Maven inside the
# maven:3.9-eclipse-temurin-8 container, to get REAL measured counts
# (not hand-picked numbers) for the Phase 3 examples. One-off tool, not
# part of the test suite -- see docs/evidence-m3.md for the output this
# produced.
set -u
cd /workspace

run_n_times() {
  local label="$1"
  local testarg="$2"
  local n=20
  local pass=0
  local fail=0
  for i in $(seq 1 "$n"); do
    mvn -q -Dtest="$testarg" test >/tmp/last_run.log 2>&1
    rc=$?
    if [ $rc -eq 0 ]; then pass=$((pass+1)); else fail=$((fail+1)); fi
  done
  echo "${label}: pass=${pass} fail=${fail} n=${n}"
}

echo "=== F1 isolation (ConfigVictimTest alone) ==="
run_n_times "F1_isolation" "odfixture.ConfigVictimTest#expectsDefaultMode"
echo "=== F1 reproduction (Polluter,Victim) ==="
run_n_times "F1_reproduction" "odfixture.ConfigPolluterTest,odfixture.ConfigVictimTest"

echo "=== F2 isolation ==="
run_n_times "F2_isolation" "odfixture.FeatureVictimTest#expectsTurboDisabled"
echo "=== F2 reproduction ==="
run_n_times "F2_reproduction" "odfixture.FeaturePolluterTest,odfixture.FeatureVictimTest"

echo "=== F3 isolation ==="
run_n_times "F3_isolation" "odfixture.ToggleVictimTest#expectsNotBothFlagsSet"
echo "=== F3 reproduction ==="
run_n_times "F3_reproduction" "odfixture.ToggleAPolluterTest,odfixture.ToggleBPolluterTest,odfixture.ToggleVictimTest"

echo "=== N1 isolation (== reproduction, no polluters) ==="
run_n_times "N1_isolation" "odfixture.NegativeAloneFailTest#alwaysFails"

echo "=== N2 isolation (== reproduction, no polluters) ==="
run_n_times "N2_isolation" "odfixture.NegativeFlakyTest#sometimesFails"
