# POC — Raw Numbers

*Every figure the defence may quote. If a number is not here, do not say it.*

⚠ **Before quoting externally:** the victim/brittle vs reproduction-count wording is
unreconciled. See [[07-Defense/weak-points]] §4.

---

## Scale

| Quantity | Value |
| --- | --- |
| IDoFT starting rows | 8,075 |
| After filtering to OD categories with usable status | 1,438 |
| Subject projects selected | 2 |
| Targets designed | 8 (JI-01–04, FJ-01–04) |
| Targets built at pinned SHAs | 8 |
| Reproduced in clean containers | **4** (all fastjson) |
| Controlled orders executed | **2,606** |
| Test-method invocations | **5,212** |
| fastjson test classes disassembled | 2,132 |
| jsoniter test classes disassembled | 58 |
| Isolation runs per target | 10 |
| Clean-container replays per accepted pair | 10 |

## Isolation classification

| Result | Count |
| --- | --- |
| Passed 10/10 alone → **victim** | 6 |
| Failed 10/10 alone → **brittle** | 2 |

⚠ Two fastjson targets classified brittle here also appear in the reproduction set. Reconcile.

## Gates vs outcomes

| Gate | Threshold | Result | Verdict |
| --- | --- | --- | --- |
| Reproduction yield | ≥3 of 4 reproduce | 4 of 8 (50%) | **Partial** |
| Ranking quality | True polluter top-5 or top-20% for ≥3 cases | No ranking existed | **Failed** |
| Execution saving | ≥30% fewer median confirmations vs OBO | **0%** | **Failed** |
| Replay reliability | ≥9 of 10 matching failures | **10/10** on all four | **Passed** |
| Evidence integrity | Exact field + bytecode locations | Present both sides | **Passed** |

## The central negative

| Measure | Value |
| --- | --- |
| `\|writes(candidate) ∩ reads(victim)\|` at depth 1 | **0** — every candidate, every case |
| Ranked strategy vs one-by-one | **Byte-identical ordering** |
| Execution saving | **0%** (gate: 30%) |

## The depth-2 ablation — FJ-02 only

| Item | Value |
| --- | --- |
| Write site | `DateParserTest.setUp@5` writes `JSON.defaultTimeZone` |
| Read site | `TypeUtils.cast@536` |
| Call-chain distance | **2 hops** |
| Rank at depth 1 | **39** |
| Rank at depth 2 | **1** |
| Confirmation reduction, this case | **97.4%** |
| Other reproduced cases that moved | **0 of 3**, at any depth tested |

**Say:** "one case moved; that is a mechanism finding, not a method."

## Replay statistics

| Measure | Value |
| --- | --- |
| Matching failures per accepted pair | 10 / 10 |
| Wilson 95% interval | **[0.72, 1.00]** |

Wilson rather than Wald because the proportion is near 1 and n is small — at 20/20 the
normal approximation degenerates to a point, which would be a false statement.

## Harness defects

| Defect | Before | After |
| --- | --- | --- |
| jsoniter candidates reported as polluters (missing suite `@BeforeClass` context) | **182 of 210** | **0** |
| fastjson targets reproducing under `TZ=Asia/Shanghai` | Phenomenon **erased** | Override removed; classified empirically |

## Candidate-set sizes (why cost matters)

| Subject | Candidates |
| --- | --- |
| fastjson worst case, after package restriction | **730** |
| fastjson, two further cases | 529 each |
| jsoniter entire module | 384 |

## Environment

| Item | Value |
| --- | --- |
| Container | `maven:3.9-eclipse-temurin-8`, digest recorded |
| JDK | 8 — required (fastjson source 1.5, jsoniter 1.6) |
| Network during test execution | **Disabled** |
| Network during dependency fetch | Separate allowlisted stage |
| json-iterator/java | `6925cf4c`, MIT |
| alibaba/fastjson | `e05e9c5e`, Apache-2.0, archived on GitHub |

## Resources consumed / planned

| Resource | Value |
| --- | --- |
| Hardware | Consumer laptops, integrated graphics — **no GPU anywhere in committed scope** |
| Disk | ~25 GB (Maven caches + subject checkouts) |
| Cloud/API budget | ~$100 total; **committed product uses none of it** |
