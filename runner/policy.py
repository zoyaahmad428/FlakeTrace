"""Search policy (W25, ADR-014 sections 4-6, Interface 7): the order the single-polluter search tries
candidates in. The policy chooses the order only; every step after it is the same for all three, so
two policies on one case reach the same endpoint and their invocations can be compared."""

import random
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from eval.baseline import TestIdentifier
from evidence.extract import DEFAULT_DEPTH, MAX_DEPTH, AnalysisCache, ExtractError, Project, rank_candidates

POLICIES = ("original", "ranked", "random")
SCOPES = ("module", "package")
DEEPEN_SHARE = 0.20  # ADR-014 section 6: analysis may use this share of a seconds limit


@dataclass(frozen=True)
class SearchPolicy:
    policy: str
    scope: str
    seed: Optional[int]
    depths: List[int]
    deepen_share: float
    candidates_with_evidence: Optional[int]
    note: Optional[str]


def choose_order(policy: str, candidates: List[TestIdentifier], *, scope: str = "module", seed: int = 0,
                 ranker=None, limit_seconds: Optional[float] = None,
                 ) -> Tuple[List[TestIdentifier], SearchPolicy, List[tuple], Optional[float]]:
    """Returns (candidate order, SearchPolicy, scores in that order, analysis seconds). A ranker has
    rank(depth) -> [(test, score)], cut_off(depth) -> bool and .seconds (Interface 7, P2-P4)."""
    if policy not in POLICIES:
        raise ValueError(f"unknown policy {policy!r}")
    candidates = list(candidates)
    if policy == "original":
        return candidates, SearchPolicy(policy, scope, None, [], DEEPEN_SHARE, None, None), [], None
    if policy == "random":
        shuffled = list(candidates)
        random.Random(seed).shuffle(shuffled)
        return shuffled, SearchPolicy(policy, scope, seed, [], DEEPEN_SHARE, None, None), [], None
    if ranker is None:
        raise ValueError("the ranked policy needs a ranker")

    depth, depths, ranked = DEFAULT_DEPTH, [], None
    while True:
        try:
            result = ranker.rank(depth)
        except ExtractError as error:
            if ranked is None:  # P3: nothing can be ranked against an unanalysable victim
                note = f"ranking fell back to the original order: the victim could not be analysed ({error})"
                return candidates, SearchPolicy(policy, scope, None, [], DEEPEN_SHARE, None, note), [], ranker.seconds
            break  # a deeper depth failed: keep the last ranking that worked
        ranked = result
        depths.append(depth)
        if any(score[0] > 0 for _, score in ranked):
            break  # one edge is enough to order the search (Interface 7 point 2)
        if not ranker.cut_off(depth) or depth >= MAX_DEPTH:
            break
        if limit_seconds is not None and ranker.seconds >= DEEPEN_SHARE * limit_seconds:
            break
        depth += 1
    order = [test for test, _ in ranked]
    if Counter(order) != Counter(candidates):
        # Ranking may only reorder (P2); a ranker bug must never shrink the search or stop the diagnosis.
        note = "ranking fell back to the original order: the ranker returned a different set of candidates"
        return candidates, SearchPolicy(policy, scope, None, [], DEEPEN_SHARE, None, note), [], ranker.seconds
    with_evidence = sum(score[0] > 0 for _, score in ranked)
    return (order, SearchPolicy(policy, scope, None, depths, DEEPEN_SHARE, with_evidence, None),
            [score for _, score in ranked], ranker.seconds)


def in_package(order: List[TestIdentifier], victim: TestIdentifier) -> List[TestIdentifier]:
    """`--scope package` (Interface 7): only tests whose class is in the victim's own package, not sub-packages."""
    def package(test: TestIdentifier) -> str:
        return test.class_name.rpartition(".")[0]
    return [test for test in order if package(test) == package(victim)]


class EvidenceRanker:
    """The ranker for `ranked`: M1's rank_candidates (Interface 5) on the project's compiled classes, with one
    AnalysisCache, so each test is analysed once per depth and `seconds` is the analysis time."""

    def __init__(self, project_dir: Path, victim: TestIdentifier, candidates: List[TestIdentifier]):
        self.target = Path(project_dir) / "target"
        self._project = None
        self.victim = victim
        self.candidates = list(candidates)
        self.by_name = {str(test): test for test in self.candidates}
        self.cache = AnalysisCache()

    @property
    def project(self) -> Project:
        # Built on first use, so a missing target/classes raises ExtractError inside rank() and reaches P3's
        # fallback instead of stopping the diagnosis.
        if self._project is None:
            self._project = Project([str(self.target / "classes"), str(self.target / "test-classes")])
        return self._project

    @property
    def seconds(self) -> float:
        return self.cache.seconds

    def rank(self, depth: int) -> List[Tuple[TestIdentifier, tuple]]:
        ranked = rank_candidates(self.project, str(self.victim), list(self.by_name), depth, self.cache)
        return [(self.by_name[item.test], tuple(item.score)) for item in ranked]

    def cut_off(self, depth: int) -> bool:
        """P4: did the victim's or a candidate's analysis stop at the depth limit (Interface 2, DEPTH_LIMIT)?"""
        for test in [str(self.victim)] + list(self.by_name):
            try:
                analysis = self.cache.get(self.project, test, depth)
            except ExtractError:
                continue
            if any(o["kind"] == "DEPTH_LIMIT" for o in analysis["unsupported_observations"]):
                return True
        return False
