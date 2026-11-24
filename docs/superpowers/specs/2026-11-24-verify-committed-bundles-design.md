# Verify every committed bundle in the tests: short design

**Status:** approved by M2 on 2026-11-24 (approach C); M3 agreed to the test living in `eval/tests/`.

**Intent.** PR #164 made `reproduced_by` required without bumping `schema_version`; 16 of 24 committed bundles
failed `eval.bundle verify` and nothing noticed for two days, because no test ran the verifier on `eval/bundles/`
(`runner/tests/test_bundle.py::TestCommittedBundles` checks only checksums and line endings). A schema or verifier
change must fail on the changer's own machine and in CI before it can break committed evidence.

**Approaches.** (A) extend M2's `TestCommittedBundles`: runs only in the runner job, which M3 does not run when
changing the schema. (B) a CI step in the python-eval job: CI only, not run by `eval/tests` locally. (C, chosen) a
test in `eval/tests/`, beside the schema and verifier it protects: fails locally for whoever changes them, and CI
already runs every `eval/tests/test_*.py`.

**Design.** New file `eval/tests/test_committed_bundles.py` (M3's `test_bundle.py` untouched):
- `test_every_committed_bundle_verifies`: `verify_bundle` on every folder under `eval/bundles/` holding a
  `manifest.json`; the failure message lists each failing bundle with its first problem; at least one bundle.
- `test_the_check_catches_a_required_field_without_a_version_bump`: the #164 incident, re-enacted: validate v2
  reports against v3 (patching `eval.schema_validator.SCHEMA_VERSIONS`) and the same collector must report exactly
  the committed bundles whose report has no `reproduced_by`. Proves the check is not vacuous.

**Verification.** Both tests pass on `main`; the second shows the check names the 16 pre-W35 bundles.
