# A6 — M3's nearest baseline: certification and statistical acceptance

*Panel action A6 (proposal defence); W40 (supervisor review, 23 Nov). v1 · 2026-11-27 · M3 (Zarpash Nasim),
written with Claude ([[genai-log-m3]]). Status: `DRAFT` -- every fact about a paper below is to be checked
against the paper itself before report v2.*
*Sources cited: only the two I have opened myself: [20] McConnell et al., [21] Wilson. I have **not** opened
[22] (Brown/Cai/DasGupta) or [12] (Gruber et al.) -- both already cited elsewhere in this project by work I
did not do the reading for -- so neither is named as a comparator in this note, even where it would be
directly relevant ([[01-Literature/references]]).*

## My part, and why it has no single nearest *tool*

My part of FlakeTrace is `eval/`/`fixtures/`: given the runner's raw counts, **decide** the verdict
(`eval.outcome.decide`'s 13-row table), **bound** the reproduction rate with a real confidence interval
(`eval.stats.wilson_interval`), **account** for what the budget actually spent, and **measure** the fixture
and real-case comparisons (policy vs. invocation count, the yield reports).

Unlike M2's part ([[07-Defense/a6-baseline-m2]], search/minimisation/verification), this does not map onto a
single flaky-test *tool*. The intellectual basis for FlakeTrace's output being called a **certificate** --
not just a pass/fail verdict -- comes from outside the flaky-test literature entirely, from algorithmics and
statistics:

| What I own | Nearest *idea* (not a flaky-test tool) | Why it is the nearest |
| --- | --- | --- |
| The report is checkable by someone who did not run it | **Certifying algorithms** [20] | McConnell et al.'s model: an algorithm returns output *y* plus a **witness** *w* that lets the user check *y* is correct **without trusting the algorithm**. A bundle (report + record + checksums, replayable by a third party) is exactly this witness |
| A reproduction rate is a bound, not a bare count | **The Wilson score interval** [21] | Wilson's own 1927 result: for a small number of trials, the naive (Wald) interval's coverage is unreliable; a score interval behaves correctly at the sample sizes we actually run (tens, not thousands) |

## What they give us, and what we had to build ourselves

- [20] gives the **model**, not an implementation: "user supplies input, receives output and certificate,
  checks the certificate proves the output" is a description of the *shape* FlakeTrace's bundle/`verify`
  pair fills, not something the paper builds for software testing at all. The mapping (pinned commit +
  budget as input; the bundle as witness; a third party re-running `verify`/`replay` as the checker) is
  ours, not theirs.
- [21] gives the **interval formula**, not the decision that an `UNRESOLVED (NOT_REPRODUCED)` report should
  *report* that bound rather than claim the test is fine. The decision table (`eval.outcome.decide`, ADR-010)
  -- which of 13 rows a given tally lands in, and what each one is and is not allowed to claim -- is ours.

## What we must not claim

- **Not that [20] or [21] are about flaky tests at all.** Neither paper mentions test flakiness; the mapping
  onto FlakeTrace's report/bundle/verdict is our own application of a general model, not something either
  paper's authors proposed or validated for this domain.
- **Not that FlakeTrace is the first "certifying" test-flakiness tool.** I have not opened iDFlakies [3],
  iFixFlakies [4] or RankF [5] myself (M2 has, [[07-Defense/a6-baseline-m2]]) and so cannot honestly say
  whether or how their own reported results are checked by a third party -- that comparison is his to make,
  not mine to assume.
- **Not a claim about which interval method is "best".** [22] (Brown/Cai/DasGupta, who compare Wilson against
  several alternatives) is directly relevant to this exact question and is already cited in this project's
  own literature notes -- but not by me, and I have not opened it. Wilson is used here because it is what
  `eval/stats.py` implements and the one paper behind it I have actually read, not because I have compared
  it against the field.

## What this means for the evaluation methodology itself (fixtures, the FJ-03 measurement)

The fixture set (F1-F4, N1-N4) and the policy comparison (`original`/`ranked`/`random`, by invocation count)
are this project's own design, not drawn from a published benchmark -- A5's scenario table
([[07-Defense/a5-scenario-table]]) is the real inventory, not reproduced here. The one external number used
in the search-budget design, Gruber et al.'s 31-shuffle figure (ADR-008), is **not re-cited as a baseline in
this note** for the same reason as [22]: I have not opened that paper myself, and the honesty rule in
`CLAUDE.md` §4.5 is explicit that a citation needs a member who actually opened the source -- not "already in
the docs", and not "sounds right".

## To check against the papers before report v2

1. [20]: the exact wording of the certifying-algorithm model, and whether McConnell et al. ever discuss
   software testing (checked assumption above: they do not focus on it).
2. [21]: Wilson's own stated conditions for the score interval's validity (small-*n* behaviour), since that
   is the entire reason it is used here rather than a simpler bound.
