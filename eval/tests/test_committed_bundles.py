"""Every evidence bundle committed under eval/bundles/ must pass eval.bundle's own verify.

Why (2026-11-24): PR #164 made `reproduced_by` required while `schema_version` stayed 2, and 16 of the 24
committed bundles failed `verify` for two days without anyone noticing -- no test ran the verifier on the committed
bundles. This test sits beside the schema and the verifier it protects, so whoever changes either sees it fail on
their own machine, and CI (which runs every eval/tests/test_*.py) does too. Added by M2 with M3's agreement.
"""

import json
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import eval.schema_validator as schema_validator
from eval.bundle import verify_bundle

BUNDLES = Path(__file__).resolve().parents[1] / "bundles"


def committed_bundles():
    return sorted(manifest.parent for manifest in BUNDLES.rglob("manifest.json"))


def failing_bundles():
    """{bundle folder name: its first problem} for every committed bundle verify rejects."""
    failing = {}
    for folder in committed_bundles():
        problems = verify_bundle(folder)
        if problems:
            failing[folder.name] = problems[0].splitlines()[0]
    return failing


class TestCommittedBundles(unittest.TestCase):
    def test_every_committed_bundle_verifies(self):
        self.assertTrue(committed_bundles(), f"no committed bundle found under {BUNDLES}")
        failing = failing_bundles()
        self.assertEqual(failing, {}, "committed bundles that no longer verify:\n"
                         + "\n".join(f"  {name}: {problem}" for name, problem in failing.items()))

    def test_the_check_catches_a_required_field_without_a_version_bump(self):
        """The #164 incident re-enacted: the v2 schema itself made to require reproduced_by (a field made required
        without a version bump); exactly the committed bundles whose report has no reproduced_by must be reported."""
        without_field = {folder.name for folder in committed_bundles()
                         if "reproduced_by" not in json.loads((folder / "report.json").read_text(encoding="utf-8"))}
        self.assertTrue(without_field, "no committed bundle predates reproduced_by; this check needs one")
        real_load = schema_validator.load_schema

        def v2_requiring_the_field(version=None):
            schema = real_load(version)
            return dict(schema, required=schema["required"] + ["reproduced_by"]) if version == 2 else schema
        with mock.patch.object(schema_validator, "load_schema", v2_requiring_the_field):
            failing = failing_bundles()
        self.assertEqual(set(failing), without_field)
        for problem in failing.values():
            self.assertIn("reproduced_by", problem)


if __name__ == "__main__":
    unittest.main()
