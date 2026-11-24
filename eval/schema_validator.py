"""Validates FlakeTrace diagnosis reports against eval/schema/report.schema.json.

Uses the `jsonschema` package so the validator can never drift from the
schema document itself -- it validates directly against the .schema.json
file rather than re-implementing the rules by hand.

2026-11-24 (M2's finding): reproduced_by (W35) became required while schema_version stayed 2,
so every one of the 16 bundles committed before W35 failed validation. Fixed by bumping the
active schema to v3 (report.schema.json, reproduced_by required) and keeping a frozen copy of
the pre-W35 shape (report.v2.schema.json, it is not) -- a report validates against the schema
its OWN schema_version names, so old evidence stays valid without weakening the current schema
for new reports. See report.v2.schema.json's own description for why that file is never edited
to add a field retroactively.
"""

import json
from pathlib import Path

import jsonschema

SCHEMA_DIR = Path(__file__).resolve().parent / "schema"
SCHEMA_PATH = SCHEMA_DIR / "report.schema.json"  # the current, active schema (v3)
SCHEMA_VERSIONS = {2: SCHEMA_DIR / "report.v2.schema.json", 3: SCHEMA_PATH}


def load_schema(schema_version: int = None) -> dict:
    """The schema for `schema_version` (2 or 3); the current schema (v3) if omitted or not one
    of those two -- which, for an unrecognized version, means validation fails on its own
    schema_version mismatch rather than needing a separate check here."""
    path = SCHEMA_VERSIONS.get(schema_version, SCHEMA_PATH)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_report(report: dict, schema: dict = None) -> None:
    """Raises jsonschema.exceptions.ValidationError if `report` does not
    conform to the report schema. Returns None on success."""
    if schema is None:
        schema = load_schema(report.get("schema_version"))
    jsonschema.validate(instance=report, schema=schema)


def validate_report_file(path) -> dict:
    """Loads and validates a report JSON file. Returns the parsed report on
    success; raises jsonschema.exceptions.ValidationError otherwise."""
    with open(path, encoding="utf-8") as f:
        report = json.load(f)
    validate_report(report)
    return report
