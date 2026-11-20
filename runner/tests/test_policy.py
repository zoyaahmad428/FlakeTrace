import dataclasses
import shutil
import unittest
from pathlib import Path

from eval.baseline import TestIdentifier
from evidence.extract import ExtractError
from runner.policy import DEEPEN_SHARE, EvidenceRanker, SearchPolicy, choose_order, in_package

V = TestIdentifier("pkg.VictimTest", "v")
C = [TestIdentifier(f"pkg.C{i}Test", "c") for i in range(10)]


class FakeRanker:
    """FAKE ranker for unit tests only: scripted scores per depth, no bytecode analysed.
    `edges[depth]` maps a candidate index to its shared-resource count at that depth."""

    def __init__(self, candidates, edges=None, cut_off=True, seconds_per_rank=0.5, fails_at=()):
        self.candidates = list(candidates)
        self.edges = edges or {}
        self.always_cut_off = cut_off
        self.seconds_per_rank = seconds_per_rank
        self.fails_at = set(fails_at)
        self.seconds = 0.0
        self.asked = []

    def rank(self, depth):
        self.asked.append(depth)
        self.seconds += self.seconds_per_rank
        if depth in self.fails_at:
            raise ExtractError("no class", 1)
        shared = self.edges.get(depth, {})
        scored = [(t, (shared.get(i, 0), depth if shared.get(i) else None, i)) for i, t in enumerate(self.candidates)]
        return sorted(scored, key=lambda item: (-item[1][0], item[1][2]))

    def cut_off(self, depth):
        return self.always_cut_off


class TestChooseOrder(unittest.TestCase):
    def test_original_keeps_the_order(self):
        order, search, scores, analysis = choose_order("original", C)
        self.assertEqual(order, C)
        self.assertEqual(search, SearchPolicy("original", "module", None, [], DEEPEN_SHARE, None, None))
        self.assertEqual((scores, analysis), ([], None))

    def test_random_is_repeatable_and_keeps_the_set(self):
        first, search, _, _ = choose_order("random", C, seed=3)
        again, _, _, _ = choose_order("random", C, seed=3)
        other, _, _, _ = choose_order("random", C, seed=4)
        self.assertEqual(first, again)
        self.assertNotEqual(first, other)
        self.assertEqual(sorted(first, key=str), sorted(C, key=str))
        self.assertEqual((search.policy, search.seed, search.depths), ("random", 3, []))

    def test_ranked_puts_evidence_first(self):
        ranker = FakeRanker(C, edges={2: {8: 1}})
        order, search, scores, analysis = choose_order("ranked", C, ranker=ranker)
        self.assertEqual(order[0], C[8])
        self.assertEqual(sorted(order, key=str), sorted(C, key=str))
        self.assertEqual((search.depths, search.candidates_with_evidence, search.note), ([2], 1, None))
        self.assertEqual(scores[0], (1, 2, 8))
        self.assertEqual(analysis, ranker.seconds)

    def test_no_edge_keeps_the_original_order(self):
        order, search, _, _ = choose_order("ranked", C, ranker=FakeRanker(C, cut_off=False))
        self.assertEqual((order, search.depths, search.candidates_with_evidence), (C, [2], 0))

    def test_victim_not_analysable_falls_back(self):
        order, search, scores, _ = choose_order("ranked", C, ranker=FakeRanker(C, fails_at={2}))
        self.assertEqual((order, search.policy, search.depths, scores), (C, "ranked", [], []))
        self.assertEqual(search.note,
                         "ranking fell back to the original order: the victim could not be analysed (no class)")

    def test_deepens_until_an_edge(self):
        ranker = FakeRanker(C, edges={3: {5: 2}})
        order, search, _, _ = choose_order("ranked", C, ranker=ranker)
        self.assertEqual((search.depths, order[0], ranker.asked), ([2, 3], C[5], [2, 3]))

    def test_stops_without_a_depth_limit_observation(self):
        _, search, _, _ = choose_order("ranked", C, ranker=FakeRanker(C, edges={3: {5: 2}}, cut_off=False))
        self.assertEqual(search.depths, [2])

    def test_stops_at_depth_five(self):
        _, search, _, _ = choose_order("ranked", C, ranker=FakeRanker(C))
        self.assertEqual(search.depths, [2, 3, 4, 5])

    def test_share_stops_deepening(self):
        ranker = FakeRanker(C, seconds_per_rank=1.5)
        _, search, _, _ = choose_order("ranked", C, ranker=ranker, limit_seconds=10)
        self.assertEqual(search.depths, [2, 3])  # 1.5 s < 2.0 s after depth 2; 3.0 s after depth 3

    def test_no_seconds_limit_means_no_share(self):
        _, search, _, _ = choose_order("ranked", C, ranker=FakeRanker(C, seconds_per_rank=100))
        self.assertEqual(search.depths, [2, 3, 4, 5])

    def test_error_at_a_deeper_depth_keeps_the_last_ranking(self):
        order, search, _, _ = choose_order("ranked", C, ranker=FakeRanker(C, fails_at={3}))
        self.assertEqual((order, search.depths, search.note), (C, [2], None))

    def test_a_ranker_cannot_drop_candidates(self):
        """Review finding 6: a ranker bug falls back to the original order (every candidate), not a traceback."""
        order, search, scores, _ = choose_order("ranked", C, ranker=FakeRanker(C[:9]))
        self.assertEqual((order, scores, search.depths), (C, [], []))
        self.assertEqual(search.note, "ranking fell back to the original order: the ranker returned a different "
                                      "set of candidates")

    def test_ranked_needs_a_ranker_and_policies_are_checked(self):
        with self.assertRaises(ValueError):
            choose_order("ranked", C)
        with self.assertRaises(ValueError):
            choose_order("best", C)

    def test_scope_is_carried(self):
        self.assertEqual(choose_order("original", C, scope="package")[1].scope, "package")

    def test_fields_are_the_contract(self):
        self.assertEqual([f.name for f in dataclasses.fields(SearchPolicy)],
                         ["policy", "scope", "seed", "depths", "deepen_share", "candidates_with_evidence", "note"])


class TestInPackage(unittest.TestCase):
    def test_package_scope_edges(self):
        victim = TestIdentifier("pkg.VictimTest", "v")
        order = [TestIdentifier("pkg.ATest", "a"), TestIdentifier("pkg.sub.BTest", "b"),
                 TestIdentifier("other.CTest", "c"), TestIdentifier("NoPackageTest", "d"), victim]
        self.assertEqual(in_package(order, victim), [order[0], victim])
        bare = TestIdentifier("BareVictimTest", "v")
        self.assertEqual(in_package(order + [bare], bare), [order[3], bare])
        self.assertEqual(in_package([victim], victim), [victim])


FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "od-fixture"


@unittest.skipUnless((FIXTURE / "target" / "test-classes").is_dir() and shutil.which("javap"),
                     "needs the compiled od-fixture (mvn test-compile) and javap")
class TestEvidenceRanker(unittest.TestCase):
    """The real adapter to M1's rank_candidates (Interface 5) on the od-fixture's compiled classes."""

    def test_the_f1_polluter_is_ranked_first(self):
        victim = TestIdentifier("odfixture.ConfigVictimTest", "expectsDefaultMode")
        other = TestIdentifier("odfixture.FeaturePolluterTest", "enableTurbo")
        polluter = TestIdentifier("odfixture.ConfigPolluterTest", "pollute")
        ranker = EvidenceRanker(FIXTURE, victim, [other, polluter])
        ranked = ranker.rank(2)
        self.assertEqual([test for test, _ in ranked], [polluter, other])
        self.assertGreaterEqual(ranked[0][1][0], 1)
        self.assertEqual(ranked[1][1][0], 0)
        self.assertGreater(ranker.seconds, 0)
        self.assertIsInstance(ranker.cut_off(2), bool)

    def test_an_unknown_victim_raises_extract_error(self):
        ranker = EvidenceRanker(FIXTURE, TestIdentifier("odfixture.NoSuchTest", "x"),
                                [TestIdentifier("odfixture.ConfigPolluterTest", "pollute")])
        with self.assertRaises(ExtractError):
            ranker.rank(2)


class TestEvidenceRankerWithoutClasses(unittest.TestCase):
    def test_a_project_without_compiled_classes_falls_back(self):
        """Review finding 1: a missing target/classes must reach P3's fallback, not crash the diagnosis."""
        import tempfile
        empty = Path(tempfile.mkdtemp(prefix="flaketrace-noclasses-"))
        ranker = EvidenceRanker(empty, V, C[:3])
        order, search, _, _ = choose_order("ranked", C[:3], ranker=ranker)
        self.assertEqual(order, C[:3])
        self.assertTrue(search.note.startswith("ranking fell back to the original order: the victim could not "
                                               "be analysed (class directory not found"), search.note)

if __name__ == "__main__":
    unittest.main()
