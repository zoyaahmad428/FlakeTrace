# Supervisor feedback register — FT001 to FT022

*v1 · 2026-11-13 · Status: `OPEN` register. Update a row only when its closure evidence exists.*

Every issue the supervisor raised at the Mid, with the same identifiers the supervisor uses.
**Bring this file to every supervision meeting.**

**How a row closes** (the supervisor's rule, kept exactly): a correction names its commit, has its
acceptance evidence, has been **reproduced by a member who did not write it**, and is accepted by
the supervisor. A status label, a green CI badge or a screenshot does not close a row. Failed
attempts stay in the record.

**Severity** is the supervisor's: Critical threatens a central conclusion, High needs prompt
substantive correction, Medium is bounded, Low is a refinement. These are not marks.

**"Checked by us"** says what we confirmed ourselves on `main` `7cf453d` on 2026-11-13, and how.

---

## Corrections to the product

| ID | Severity | Finding | Required output | Owner → verifier | Closes when | Plan |
| --- | --- | --- | --- | --- | --- | --- |
| **FT003** | **Critical** | When the victim runs alone, only failures matching the reference signature are counted. A victim that fails alone with a *different* exception is treated as passing alone and can get `VERIFIED` | Keep four outcome categories (pass, matching failure, other real failure, infrastructure) from runner to decision to schema to report. Define the mixed case. A regression that cannot get an unqualified `VERIFIED` | M2 capture, M3 decision and schema → M1 reproduces | An integrated regression (Java fixture, B alone / A after P) cannot get `VERIFIED`; matching-alone, all-pass, mixed, crash and timeout cases behave as agreed; raw outputs and the correction commit are kept | ADR-010 · W17, W18, W19 |
| **FT004** | High | `ddmin` caches one trial per subset. The final check repeats the kept sequence but never each deletion. A sequence with an unneeded test can get `VERIFIED` | Qualify the 1-minimal claim now. Define a bounded repeated-deletion rule with its uncertainty and cost. Record the result of removing each kept test. Gate the stronger claim | M2 runs, M3 gate and storage → M1 reproduces | Stored deletion trials support every kept test; variable, deterministic, one-polluter, multi-polluter and budget-exhausted cases are tested; insufficient evidence gives a qualified result | ADR-011 · W20 |
| **FT005** | High | The extractor intersects *possible* writes and reads and reports the first sorted edge. That is a potential overlap, not the cause. `VERIFIED` wording implies more | Separate confidence in the *sequence* from evidence for the *resource* in requirement, schema, decision and displayed report. Label static evidence as potential overlap. Add a write-then-restore control and an unrelated-overlap control | M1 leads, M3 report, M2 execution → M2 reproduces | The controls do not get a causal label; edge ordering and extra edges are disclosed; any causal claim that remains has its own measured evidence | ADR-010 (wording), ADR-015 (causal check) · W16, W21 |
| **FT006** | High | The harness runs each test as its own JUnit request, so `@BeforeClass` and `@AfterClass` run per method, unlike normal execution | State the supported lifecycle. Build a class-lifecycle control compared against normal execution. Keep the behaviour or reject unsupported cases explicitly | M2 → M1 compares normal and diagnostic execution | Expected setup counts and signatures are recorded for both paths; unsupported cases are named. Needed **before** any real-project claim | ADR-012 · W22 |
| **FT021** | High | Source hashes compare the project before and after, excluding `target/` and `.git/`. They cannot show that nothing was written in between, or outside the project. A fresh JVM does not reset files or external state. There is no sandbox | Use trusted subjects only. Describe the hash property accurately. Add a reset-sensitive control. Plan container work against the approved milestone | M2 → M3 checks recorded provenance | The reset boundary is written down and matches the code; no sandbox or "never modified" claim is made | ADR-012 · W16, W22, W27 |
| **FT009** | High | Committed reports point at raw records by an absolute path on one machine. The records are not in the repository | Export one bundle: report, matching record, tool and subject commits, environment, seed and order, reset assumptions, replay steps, checksums. Label it a fresh run | M3 packages, M2 capture and replay → M1 reproduces on another machine | M1 unpacks it elsewhere, finds every record without the author's paths, matches counts and signatures, and reproduces the outcome | ADR-013 · W23 |
| **FT010** | High | The status `NO_SINGLE_POLLUTER` has no report. The command exits with code 3 and leaves only a record | A typed reason and a schema-valid report for an inconclusive search, with the counts that exist. Never invent a polluter | M2 status, M3 schema and report → M1 exercises it | An integration regression reaches this status and gets the agreed structured abstention with a next step | ADR-010 · W19 |
| **FT007** | High | No shared execution budget, no verification reserve. Evidence is extracted after the search; the `priority` hook is unused | A small measurable increment: count total cost, stop at a shared limit, keep verification resources, compare with unranked search at the same endpoint | M2 integrates, M1 candidate evidence and order, M3 measures | The budget cannot be exceeded silently; matched comparisons exist. The **plan** is due at the next review, the implementation by the Final | ADR-014 · W24, W25 |
| **FT008** | High | All seven diagnosed cases come from one fixture we wrote. fastjson was used for extraction only. Random-order detection is not the same endpoint as a verified diagnosis. The 25% target is unmeasured | One buildable real case, pinned. A task-matched comparator, total invocations including verification, yield, uncertainty. Development and held-out cases kept apart | M3 leads, M2 execution, M1 resource coverage → M1 or M2 repeats the measurement | Next review: a feasible case and protocol. Final: complete pipeline results and comparator records, **including failed builds and negative results** | [[05-Testing/real-case-protocol]] · W26 |

## Corrections to scope, planning and approval

| ID | Severity | Finding | Required output | Owner | Closes when | Plan |
| --- | --- | --- | --- | --- | --- | --- |
| **FT012** | High | The schedule contradicts itself: essential integration in May–June in one place, a stable demo by mid-April in another. Defence dated 9 September in one place and 11 September in another | One owner-assigned schedule against confirmed cohort dates | All, M2 integrates; supervisor confirms dates | One dated plan with owners, interfaces, evidence gates and a contingency | [[00-Meta/roadmap]] · [[10-Final1/iteration-2-plan]] · W31 |
| **FT011** | High | Team ADRs are not approval. The resource boundary (A10), the static-only refinement and the three-member roster need the supervisor's confirmation | The supervisor's recorded decisions. Material reductions go through the proper route | Supervisor and all | Each decision is recorded with its date | [[10-Final1/supervisor-agenda]] · W31 |
| **FT022** | High | The worksheet marked panel actions A1–A9 complete. The original panel result sheet was not supplied. A1–A6 are partly addressed, A7–A9 are supervisory follow-ups, A10 is undecided | Authentic panel wording. Evidence-based statuses, with incomplete work left visible | All by evidence owner | Each action has its authority, milestone, evidence and the supervisor's closure decision | [[10-Final1/action-register]] · W31 |
| **FT018** | Medium | Three practitioner interviews, none in Java, Maven or JUnit | One Java/Maven practitioner workflow check: a realistic input, the expected decision, an acceptable runtime, the evidence needed to act | M1 coordinates, M2 use case, M3 acceptance task | A dated, consented record linked to an acceptance task, or a recorded blocker and an agreed substitute | W32 |
| **FT020** | Medium | Integration knowledge sits with M2. No handover has been exercised | One interface and release handover, performed by each member for their own part | All; M1 reproduction backup, M3 report and schema backup | Another member reproduces the end-to-end command, locates the runner → evidence → report contract and makes a small recorded change | W23, W33 |

## Corrections to the report and worksheet

| ID | Severity | Finding | Required output | Owner | Closes when | Plan |
| --- | --- | --- | --- | --- | --- | --- |
| **FT013** | Medium, **mandatory** | The report's signature page (physical page 10) has three blank lines, though the worksheet says signatures were added. The worksheet was submitted as PDF only | Signed report. Editable filled worksheet | Each member signs for themselves; M2 compiles | Genuine signatures present; the supervisor can edit the worksheet. **Due before report acceptance** | W28, W29 |
| **FT014** | Medium | All nine declarations per member, the dated confirmations and the twelve group confirmations are blank | Each student completes their own, truthfully, after the facts are corrected | Each member | Declarations and dates match the corrected content | W29 |
| **FT015** | High | Member 3's GenAI level is L3 in one worksheet table and L2 in another, in the report and in the repository register | One consistent per-artefact account: what was generated, changed, rejected, tested | M3; each member checks their own rows | Consistent across worksheet, report and register, with samples. A changed label alone is not enough | W29 |
| **FT016** | Medium | The worksheet's design table is clipped at the right edge (page 8); rationale text is cut off | Recover the full rationale; re-export within the page, landscape if needed | M1; M3 checks every exported page | Every column and row readable at normal size | W29 |
| **FT017** | Medium | Stale status: the report says the tag is not set; FR-1 is Partial in one table and Done in another; member table and certificate semantics disagree with the code | One authoritative implemented / planned table at the submission commit. Historical statements labelled with their date | Chapter and module owners; M2 compiles; M3 checks | A cited requirement or status resolves the same way everywhere | W28 |
| **FT019** | Low | The committee's template has inherited defects (duplicate lists, page-zero reset, blank versos). Abstract length guidance conflicts: handbook 50–125 words, template comment 150–200 | The supervisor confirms the interpretation. Shorten the abstract conservatively | Supervisor; M2 compiles, M1 checks the abstract against measured claims | Final report follows the confirmed interpretation | W28 |

## Baseline records, not corrections

| ID | What it records | Status |
| --- | --- | --- |
| FT001 | The frozen build is tag `mid-eval-v1` → `86d8355`. Later work is identified separately | Closed for the documentary baseline. The version actually demonstrated live is not recorded |
| FT002 | Executed checks are separated from claims: 268 tests passed for the reviewer; they do not cover the two counterexamples | Partially addressed |

---

## Checked by us

Run on `main` `7cf453d`, 2026-11-13, in a scratch script using `eval/tests/fake_runner.py` and the
real `runner.diagnose.run_steps` and `eval.report.assemble_report`. Details and the exact output:
[[evidence-m2]].

| Issue | What we ran | Result |
| --- | --- | --- |
| FT003 | Victim fails alone 20/20 with exception B, and after P 20/20 with exception A | **`VERIFIED`**, polluter P, report shows alone 0/20. Defect confirmed |
| FT004 | P alone is enough, but `[P, victim]` happens to pass on the two single trials the search and `ddmin` give it | **`VERIFIED`** with P and Q kept. `[P, victim]` then fails 20/20. Defect confirmed |
| FT003 | Read `runner/diagnose.py` lines 109–112 and 129–132 | `alone_any` is computed and then dropped; the result always carries `alone_successes = 0` on the search path |
| FT010 | Read `eval/report.py` line 100 and `runner/cli.py` lines 86–91 | `NO_SINGLE_POLLUTER` raises `UnhandledStatus`; the command prints "No report" and returns 3 |
| FT005 | Read `evidence/extract.py` `find_edges` and `report_fields` | Edges are the intersection of WRITE and READ resource ids, sorted by depth then name; the first is reported |
| FT006 | Read `runner/harness/FtHarness.java` `runOne` | One `Request.method(cls, name)` per test |
| FT021 | Read `runner/integrity.py` | Hash of every file except top-level `target/` and `.git/`, before and after |
| FT007 | Read `runner/cli.py` and `runner/search.py` | `--n`, `--shuffles`, `--seed` only. `priority` is never passed by the CLI |

Not checked by us: FT006 against a real project, FT008, FT009 on a second machine, and every
report and worksheet finding (taken from the supervisor's audit).

## Decisions only the supervisor can make

Tracked with their answers in [[10-Final1/supervisor-agenda]].

| Decision | Until it is made |
| --- | --- |
| What `VERIFIED` means: the pass-alone, minimality and resource rules | We qualify the claims and build the bounded FT003 fix |
| Approved scope: resource boundary (A10), static-only refinement, three-member roster | We keep the committed scope and correct engineering claims only |
| Authentic panel wording and due dates for A1–A6 | Statuses stay "Partly", with evidence links |
| Cohort dates: poster, Final, next review | We plan against the handbook's week numbers and say so |
| Handbook and template: abstract length, the "missing abstract" comment | We keep the content and shorten conservatively |
| Scope weights for the 60% rule | We show our unweighted count and label it as ours |
