# RankF (RankFL / RankFO) — Rahman, Chanumolu, Rafi, Shi, Lam (ICSE 2025)

**Role for us:** `BASELINE` — **our closest prior work and strongest baseline.**
**Ref:** [5]

> This is the paper that most threatens our contribution claim, and the one whose *stated
> future work* creates our opening. Know it cold.

---

## What it does

Ranks candidate tests by likelihood of being **OD-relevant**, so fewer tests are run before a
true one is confirmed.

- **RankFL** — fine-tunes BigBird over test-method bodies (learned)
- **RankFO** — scores candidates from outcomes and positions of tests across previously
  observed test orders, using five heuristics: Plus One, #Methods, Distance, and two Combined
  variants (history-based)

## Results — quote these accurately

| Measure | Value |
| --- | --- |
| Evaluated on | **155 OD tests, 34 modules, 24 projects** |
| Median time to first OD-relevant test | **9.4 – 14.1 s** (by OD-relevant type) |
| Baselines | **34.2 – 118.5 s** |
| RankFO ranking cost | **< 100 ms** (negligible) |
| RankFL inference cost | a substantial fraction of its total time |
| MAP on polluters | RankFO **0.251**, RankFL 0.007, OBO **0.000** |

**OBO cost they measured** (our baseline floor): mean rank of first polluter **86.7**, median
**29.0**; time to rank+confirm mean **680.8 s**, median **83.8 s**. Their worst-case
construction OBOmax: rank **211.9**, **1518.4 s**.

**Reproducibility cost they measured** (our dataset-amber evidence): started from **249** OD
tests, retained **155** after confirming reproducibility — some could not be reproduced under
Maven Surefire, confirmed with the original authors, and excluded.

## Three published limitations — the space we occupy

| Limitation | What it lets us do |
| --- | --- |
| **Excludes joint multi-test dependence**, citing Shi et al.'s rarity finding | Zhang et al.'s **82%-revealed-by-two-tests** figure bounds how rare — a non-empty remainder single-test search cannot explain. Our multi-test candidate retention addresses it |
| **RankFO requires prior test-order data**; where a developer has few or no orders, the authors recommend RankFL | Our resource evidence needs no order history |
| **The authors explicitly state future work should give the ranker other information sources, naming dynamic execution traces** | **This is our opening, stated by them.** Our resource-event evidence directly occupies it |

**Plus a stability caveat:** RankFO needs on average **206.0 / 86.2 / 171.5 orders** (polluters
/ state-setters / cleaners) before a correct OD-relevant test is ranked first **and stays
first** — far more than the 20 used in the main configuration. The authors note 20 orders
nevertheless substantially reduce ranking-plus-confirmation time.

→ We inherit both facts: **20 orders is a defensible operating point, and Rank-1 stability is
not to be claimed from it.**

## The answer when asked "why is your ranking interesting?" (Q14)

> It is not, on its own — which is exactly why RankF is a **mandatory baseline** rather than a
> related-work citation. RankFL and RankFO were evaluated on 155 reproducible OD tests across
> 24 projects and reported faster discovery than one-by-one and delta debugging, so comparing
> our guidance against random ordering would be a rigged comparison.
>
> Our ranking signal is different **in kind**: RankF's positional and lexical signals are
> static properties of the suite; ours is resource-overlap evidence collected from execution,
> and **the two are combinable**. The interesting question is whether resource evidence adds
> anything on top of RankF — **and we have committed to reporting the answer even if it is no.**
> That is the resource-only and order-only ablation.

## The one-word-answer trap (Q105)

*"Will your approach beat RankF? One word."*

> I would rather not give a one-word answer, because the honest answer has a condition
> attached. **On ranking accuracy alone, we may not** — RankF is validated at a far larger
> scale than we will reach. Our claim is about **cost to a verified, replayable result under a
> budget**, which RankF does not produce, and about whether resource evidence adds anything on
> top of RankF's signals — an open question we have committed to answering either way.

*Declining the format while answering the substance is correct and is not evasion.*

## What it does better than us (Q19)

**Its ranking is validated at a far larger scale than ours will be** — 155 reproduced tests
across 24 projects. Say this plainly.

## Metrics we adopt from it (deliberately, for comparability)

Rank-1 count · rank of first relevant test · time to rank plus confirm · MAP/MRR alongside.
Using their metrics makes our results **directly comparable to the strongest published
baseline**.

## Evaluation plan against it

**RankFO**, and where feasible RankFL, on the same candidate sets. Report top-k recall, MRR,
and time/invocations to first confirmed relevant test.
`STATUS: not yet run — Final-1 exit condition.`
