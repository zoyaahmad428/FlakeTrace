# FlakeTrace one-day POC — decision record

**Date:** 2026-08-28  **Executed by:** Zoya Ahmad
**Protocol:** `manifest/definitions.md` (frozen before any run)
**Environment:** `manifest/environment.txt` — `maven:3.9-eclipse-temurin-8`,
image id `sha256:15522857a08b…`, JDK 1.8.0_502, Maven 3.9.16, volume `ftm2`
**Dataset provenance:** IDoFT snapshot `4903dc9233eead4e4191c66f9ed0b14eea091052` (2026-05-03)

---

## 1. What was tested

The POC tests the project's *incremental* claim, not that OD failures can be
rerun: **can a bounded static-field overlap signal prioritise true OD-relevant
tests and reduce confirmation executions against OBO/random baselines?**

Eight cases across two Maven projects, pinned by commit:

| | project | SHA | cases |
|---|---|---|---|
| JI-01…04 | json-iterator/java | `6925cf4c` | 4 |
| FJ-01…04 | alibaba/fastjson | `e05e9c5e` | 4 |

Single-scan protocol: one exhaustive `[candidate, victim]` scan per case
(**2,606 orders / 5,212 test-method invocations**); OBO, 5 random seeds and the
resource-ranked strategy all replayed offline from that one outcome table.

## 2. Results against the pre-registered gates

| # | Gate | Threshold | Observed | Verdict |
|---|---|---|---|---|
| 1 | Build / reproduction yield | ≥3 of 4 reproduce | 8/8 build; **4/8 reproduce** (fastjson 4/4, jsoniter 0/4) | **BELOW** |
| 2 | True OD-relevant ranking | top-5 or top-20% in ≥3 reproduced cases | overlap score **0 for every candidate in every case**; ranking degenerates to OBO | **BELOW** |
| 3 | Execution saving vs OBO | ≥30% fewer median confirmations | **0.0%** — resource order is byte-identical to OBO | **BELOW** |
| 4 | Replay reliability | ≥9/10 matching for each accepted pair | **10/10 all four**, Wilson 95% CI [0.72, 1.00] | **MEETS** |
| 5 | Evidence integrity | every overlap names exact field + bytecode location | identifiers are `owner.field:descriptor` with `@offset`; no false edges emitted | **MEETS (vacuously at hop-1)** |

## 3. The three findings that matter

**(a) The frozen one-hop resource scope is uninformative on these subjects.**
`|writes(candidate) ∩ reads(victim)|` is **zero for all 1,842 scanned candidate
pairs**. The signal does not rank badly — it does not discriminate at all, so
the "resource-ranked" strategy and OBO produce identical orders and identical
cost. Gate 3 is not a weak result; it is a null result.

The cause is depth, not principle. FJ-01's state-setter writes
`com/alibaba/fastjson/JSON.defaultTimeZone` in `DateFieldTest8.setUp@5`. The
target reads it only inside `SerializeWriter`, more than one hop below
`JSON.toJSONString`. The frozen scope cannot see the read.

Hop-depth ablation (`results/hop_ablation.json`):

| hops | FJ-01 | FJ-02 | FJ-03 | FJ-04 |
|---|---|---|---|---|
| 1 (frozen) | 0% | 0% | 0% | 0% |
| 2 | 0% | **97.4%** (rank 39 → 1) | 0% | 0% |
| 3 | 0% | 97.4% | 0% | 0% |

Depth-2 rescues exactly one of four cases, completely. Depth-3 adds nothing.
So deepening is necessary but not sufficient — three cases carry their
interference through paths static field analysis does not model at all.

**(b) Two of the eight "OD victims" are brittle tests, and the distinction was
nearly masked by an environment fix.** FJ-01 and FJ-02 fail **alone** and pass
**after** a predecessor. They need `JSON.defaultTimeZone` to have been set by
someone else; `DateFieldTest8.setUp` writes it globally and never restores it.

An earlier revision of the harness set `TZ=Asia/Shanghai` to make these pass in
isolation. That made the state-setter's write a no-op and erased the effect
under measurement. The override was removed and the direction is now classified
empirically (`results/alone.csv`). Any future harness must treat "target fails
alone" as a *classification*, never as an environment defect to be fixed.

**(c) jsoniter produced zero reproductions, and the reason is structural.**
Its Surefire config never runs test classes directly — it runs five *suite*
classes with `reuseForks=false`, each in a fresh JVM, whose `@BeforeClass`
selects the codegen mode. Running raw test methods without that context made
**182 of 210** candidates "fail" with an identical `LinkageError` — a pure
harness artifact. After reproducing the suite context the artifact vanished
(182 → 0). A widened diagnostic scan over the **full module** (382 candidates)
also found 0, so no single predecessor reproduces these failures: they are
multi-predecessor or suite-level effects outside the frozen pairwise model.

## 4. Decision — **NARROW**

Not Go: three of five gates fail, and the headline mechanism produced a null
result at its frozen scope. Not Pivot: the product contract is intact — the
diagnosis loop, containerised runner, failure-signature equivalence and
statistical replay all worked, and the one case where the signal could see the
resource showed a 97.4% saving, which is the effect the project claims.

### Scope changes carried into the proposal

1. **Redefine the resource scope.** Replace "direct references plus one hop"
   with transitive intra-project reachability to a declared depth (≥2), with
   the depth and its cost reported. Hop-1 must be retained only as an ablation.
2. **Commit to classifying OD direction** (victim / brittle) before search, and
   forbid environment changes that alter isolation behaviour without a recorded
   justification.
3. **Require execution-context fidelity** as a build-gate artefact: the harness
   must reproduce the project's declared Surefire execution context (suites,
   forks, categories) and prove it by matching an uninstrumented baseline.
   Report harness-induced outcomes as a first-class failure mode.
4. **Add order-history evidence** as a ranked component, since static-field
   overlap alone was uninformative on 3 of 4 reproduced cases.
5. **Re-scope subject selection** away from suite-driven projects for the
   pairwise model, or extend the model to multi-predecessor orders. Record the
   yield honestly: 8 attempted, 8 built, 4 reproduced.

### What did NOT change

Failure-signature equivalence, the budget unit (test-method invocations), the
single-scan protocol, the replay contract and the abstention principle all held
up and are unchanged.

## 5. Blank results record (guide §7.4), completed

| Field | Result |
|---|---|
| Projects and exact commits | json-iterator/java `6925cf4c19d313504b416f58a349a36bf563e0e1`; alibaba/fastjson `e05e9c5e4be580691cc55a59f3256595393203a1` |
| Cases attempted / reproduced | 8 attempted, 8 built, **4 reproduced** (FJ-01…04) |
| Baseline results | OBO cost-to-first: 5 / 39 / 368 / 220. Random (5 seeds) median: 3 / 29 / 43 / 224 |
| Resource-guided results | Identical to OBO at frozen hop-1 (0% saving). Hop-2 ablation: 97.4% saving on FJ-02, 0% elsewhere |
| Failure cases and errors | jsoniter ×4 not reproduced (no single predecessor, full-module scan also 0); 1 harness artifact found and corrected (suite context, 182 false polluters); 1 methodological error found and corrected (TZ override masking brittleness) |
| Go / Narrow / Pivot | **NARROW** |
| Changes made to scope/design | 5 changes listed in §4 |
| Evidence folder / commit | `results/`, `logs/raw/`, `manifest/`, this record |
