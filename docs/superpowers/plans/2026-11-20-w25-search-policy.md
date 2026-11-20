# W25 runner half — search policy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** one diagnosis orders its single-polluter search by `original`, `ranked` (M1's evidence, with ADR-014 §6 deepening) or `random`, limited to a `module` or `package` scope, and records what it chose (Interface 7, P1–P6).

**Architecture:** a new `runner/policy.py` holds `SearchPolicy`, `choose_order()` (the three policies and P4's deepening loop over an injected ranker) and `EvidenceRanker` (the adapter to `evidence.extract`). `run_steps` calls `choose_order` after the alone check and passes the order to `find_polluter`'s existing `priority` hook.

**Tech Stack:** Python 3.11 `unittest`, `FakeOrderRunner`, a `FakeRanker` under `runner/tests/`, the od-fixture (JDK 8+, Maven, javap).

**Spec:** `docs/superpowers/specs/2026-11-20-w25-search-policy-design.md`; `docs/contracts/interfaces.md` Interface 7 (and 5, 6); ADR-014 §4–§6.

## Global Constraints

- `POLICIES = ("original", "ranked", "random")`, `SCOPES = ("module", "package")`, `DEEPEN_SHARE = 0.20`, start depth `evidence.extract.DEFAULT_DEPTH` (2), cap `evidence.extract.MAX_DEPTH` (5).
- `SearchPolicy` fields exactly, in order: `policy, scope, seed, depths, deepen_share, candidates_with_evidence, note`.
- The candidate set never changes; only its order. A policy changes nothing after the candidate order.
- `random`: `random.Random(seed).shuffle(copy)` with `seed = seed_base` (`--seed`).
- Fallback note text: `"ranking fell back to the original order: the victim could not be analysed (<error>)"`.
- Record line: `{"type": "ranking", "policy", "scope", "seed", "depths", "order", "scores", "note"}`, written before the first `search` run; `order` as `str(test)`, `scores` as lists; `[]` unless ranked.
- Default `policy="original"`, `scope="module"`: runs, records (apart from the new header keys and the ranking line) and verdicts unchanged.
- Never "cause" for a rank (claims G3). Test-first; failing output into `docs/evidence-m2.md`. Agent never commits.

## Review Focus

1. Default policy: the runner call sequence is unchanged → Task 2 `test_original_policy_changes_nothing`.
2. Ranked when the reproducing order came from a shuffle: candidates are that order's tests before the victim → Task 2 `test_candidates_are_the_order_searched`.
3. A ranker that returns a different set (bug in a ranker) must not shrink the search → Task 1 `test_a_ranker_cannot_drop_candidates`.
4. `--scope package` when the victim's class has no package, or the package has no other test → Task 3 `test_package_scope_edges`.
5. A seconds limit with `ranked`: analysis time reaches `wall_seconds` and the 20% share stops deepening → Task 1 `test_share_stops_deepening`, Task 2 `test_analysis_seconds_in_the_account`.

---

### Task 1: `runner/policy.py` — policies and the deepening loop

**Files:** Create `runner/policy.py`; Test `runner/tests/test_policy.py` (with `FakeRanker`).

**Interfaces — Produces:**
- `SearchPolicy` frozen dataclass (fields above).
- A ranker is any object with `rank(depth) -> List[Tuple[TestIdentifier, tuple]]` (raises `evidence.extract.ExtractError` if the victim cannot be analysed), `cut_off(depth) -> bool`, and `seconds: float`.
- `choose_order(policy, candidates, *, scope="module", seed=0, ranker=None, limit_seconds=None) -> Tuple[List[TestIdentifier], SearchPolicy, List[tuple], Optional[float]]` — (order, search, scores in order, analysis_seconds). `ranker` is required for `ranked` (`ValueError` otherwise).
- Deepening (P4): rank at 2; stop if any score[0] > 0, or not `cut_off(depth)`, or depth == 5, or (`limit_seconds` set and `ranker.seconds >= DEEPEN_SHARE * limit_seconds`); else depth + 1. `ExtractError` at the first depth → original order + note; at a later depth → keep the last ranking. Then the order is checked to be a permutation of `candidates`; if not, `ValueError` (Review Focus 3: a ranker bug is loud, never a smaller search).

- [ ] **Step 1: failing tests** (`C = [C0..C9]`, `V`):
  - `test_original_keeps_the_order`: order == C; `search == SearchPolicy("original", "module", None, [], 0.2, None, None)`; scores `[]`; analysis None.
  - `test_random_is_repeatable_and_keeps_the_set`: seed 3 twice → same order; seed 4 → different; sorted equal to C; `search.seed == 3`.
  - `test_ranked_puts_evidence_first`: FakeRanker scores C8 `(1, 2, 8)`, others `(0, None, i)` → order starts `C8`, `depths == [2]`, `candidates_with_evidence == 1`, analysis == ranker.seconds.
  - `test_no_edge_keeps_the_original_order`: all `(0, None, i)`, `cut_off` False → order == C, depths [2].
  - `test_victim_not_analysable_falls_back`: rank raises `ExtractError("no class")` → order == C, policy "ranked", note equals the fallback text with `no class`, depths [].
  - `test_deepens_until_an_edge`: no edge at 2, edge at 3, cut_off True → depths [2, 3].
  - `test_stops_without_a_depth_limit_observation`: cut_off False → [2].
  - `test_stops_at_depth_five`: never an edge, always cut off → [2, 3, 4, 5].
  - `test_share_stops_deepening`: `limit_seconds=10`, ranker adds 1.5 s per rank → [2, 3] (3.0 ≥ 2.0 after depth 3).
  - `test_error_at_a_deeper_depth_keeps_the_last_ranking`: depth 3 raises → depths [2], order from depth 2, note None.
  - `test_a_ranker_cannot_drop_candidates`: ranker returns 9 of 10 → `ValueError`.
  - `test_fields_are_the_contract`: `[f.name for f in fields(SearchPolicy)]` as in Global Constraints.
- [ ] **Step 2:** `py -3 -m unittest runner.tests.test_policy` → `No module named 'runner.policy'`.
- [ ] **Step 3:** implement. **Step 4:** same → OK.

### Task 2: wire the policy into `run_steps` and the ledger

**Files:** Modify `runner/diagnose.py`, `runner/budget.py`; Test `runner/tests/test_diagnose.py` (new `TestSearchPolicy`), `runner/tests/test_budget.py`.

**Interfaces:**
- `run_steps(..., policy="original", scope="module", ranker_for=None)` where `ranker_for(candidates, victim) -> ranker` (Task 1's shape); `seed_base` is the random seed.
- `DiagnosisRuns.search: Optional[SearchPolicy] = None` (last field; `run_steps` always sets it).
- `BudgetedRunner.account(candidates_total, policy="original", analysis_seconds=None)`; `BudgetedRunner.write_event(entry)` forwards to the inner runner when it has one.
- The ranking line is written with `write_event` after `choose_order`, before `_label(runner, "search")`'s first run.

- [ ] **Step 1: failing tests:**
  - `test_original_policy_changes_nothing`: TEN scenario (W24's), no policy → 51 calls, `search.policy == "original"`, `budget.policy == "original"`.
  - `test_ranked_tries_one_pair_where_original_tries_nine` (ADR-014): victim fails iff `C8` precedes it; FakeRanker puts `C8` first → ranked `spent["search"] == 2`, original `== 18`, same `status`/`polluters`, totals differ by 16.
  - `test_candidates_are_the_order_searched`: starting order never fails, a shuffle reproduces → the ranker received exactly that shuffled order's tests before the victim.
  - `test_ranking_line_comes_before_the_first_search_run`: through `RecordingRunner` → the line after the last `alone` run is `type "ranking"` with `order` of 10 strings and `policy "ranked"`.
  - `test_analysis_seconds_in_the_account`: FakeRanker `seconds = 1.25` → `budget.analysis_seconds == 1.25`; `original` → None.
  - `test_random_policy_uses_the_seed`: `seed_base=7` → `search.seed == 7`, two runs give the same runner calls.
  - `test_status_that_never_searches_still_has_a_search_policy`: VICTIM_FAILS_ALONE → `search.policy` set, ranker never asked.
  - In `test_budget.py`: `test_write_event_forwards` and `account(..., policy="ranked", analysis_seconds=2.0)` fields.
- [ ] **Step 2:** run → fail (unexpected keyword `policy`). **Step 3:** implement. **Step 4:** `py -3 -m unittest runner.tests.test_policy runner.tests.test_budget runner.tests.test_diagnose` → OK.

### Task 3: `EvidenceRanker`, `diagnose()` scope and policy, CLI, real runs, docs

**Files:** Modify `runner/policy.py` (`EvidenceRanker`), `runner/diagnose.py` (`diagnose(..., policy, scope)`, `in_package`), `runner/cli.py`; Test `runner/tests/test_policy.py`, `test_diagnose.py`, `test_cli.py`; docs.

**Interfaces:**
- `EvidenceRanker(project_dir: Path, victim: TestIdentifier, candidates: List[TestIdentifier])`: `Project([target/classes, target/test-classes])`, one `AnalysisCache`; `rank(depth)` → `rank_candidates(project, str(victim), [str(c) for c in candidates], depth, cache)` mapped back to `TestIdentifier`; `cut_off(depth)` → any `DEPTH_LIMIT` kind in `cache.get(project, t, depth)["unsupported_observations"]` for the victim and every candidate (skipping those that raise `ExtractError`); `seconds` → `cache.seconds`.
- `in_package(order, victim) -> List[TestIdentifier]`: classes whose package (text before the last `.`, `""` if none) equals the victim's.
- `diagnose(..., policy="original", scope="module")`: `scope == "package"` with `original_order` → `DiagnoseInputError("--scope package cannot be combined with --order: the order file already fixes the tests")`; else filters the discovered order before `check_budget`. Header gains `"policy"`, `"scope"`. Passes `ranker_for=lambda c, v: EvidenceRanker(project, v, c)` only for `ranked`.
- CLI: `--policy {original,ranked,random}`, `--scope {module,package}` → `diagnose`; `summary(..., search=None)` adds `search_line(search)`: `"  search:     original order"`, `"  search:     random order (seed 7)"`, `"  search:     ranked at depth 2 (1 of 7 candidates with evidence)"` (depths shown as `2→3` when deepened), and the note on its own line `"              <note>"`.

- [ ] **Step 1: failing tests:**
  - `test_package_scope_edges` (`in_package`): mixed packages → only the victim's; victim with no package → only package-less tests; sub-package `pkg.sub.X` excluded for victim `pkg.V`.
  - `test_scope_package_with_an_order_is_refused`: `diagnose(<empty temp dir>, V, original_order=[V], scope="package")` raises `DiagnoseInputError` (the check sits with the other `original_order` checks at the top of `diagnose`, before any snapshot or Maven call); unknown `policy`/`scope` strings raise too. CLI: `--scope package --order f` exits 2.
  - `test_policy_and_scope_reach_diagnose`; `test_unknown_policy_is_a_usage_error`; `TestSearchLine` (the three forms + note).
  - Real (`TestEvidenceRanker`, needs the compiled fixture, skipped without JVM like M1's tests): F1's victim and its 2 earlier tests → `rank(2)` returns both, polluter `odfixture.ConfigPolluterTest#pollute` first with score[0] ≥ 1; `seconds > 0`.
  - Real CLI (`TestCliOnFixture`): F1–F4 with `--policy ranked` → the same outcome as ground truth (`VERIFIED` for all four), and the summary has a `search:` line.
- [ ] **Step 2:** run → fail. **Step 3:** implement. **Step 4:** `py -3 -m unittest runner.tests.test_policy runner.tests.test_cli` → OK; then whole runner suite, eval, `ui.tests.test_server`, `ui/web npm test`.
- [ ] **Step 5: real runs:** F2 with `--policy original` and `--policy ranked` (same budget, none) — record `spent["search"]`, the `search:` line and the ranking line; and `--scope package` on F1. Numbers written as they come.
- [ ] **Step 6: docs:** runner README (module table, options, status of `priority`), `docs/04-Implementation/` notes, W25 plan row, members, evidence, GenAI log, register row; demo plan if the demo gains `--policy ranked`. Hand over the commit, the PR text and the messages for M1/M3.
