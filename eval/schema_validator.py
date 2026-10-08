"""Validates FlakeTrace diagnosis reports against eval/schema/report.schema.json.

Uses the `jsonschema` package so the validator can never drift from the
schema document itself -- it validates directly against the .schema.json
file rather than re-implementing the rules by hand.
"""

import json
from pathlib import Path

import jsonschema

SCHEMA_PATH = Path(__file__).resolve().parent / "schema" / "report.schema.json"


def load_schema() -> dict:
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        return json.load(f)


def validate_report(report: dict, schema: dict = None) -> None:
    """Raises jsonschema.exceptions.ValidationError if `report` does not
    conform to the report schema. Returns None on success."""
    if schema is None:
        schema = load_schema()
    jsonschema.validate(instance=report, schema=schema)


def validate_report_file(path) -> dict:
    """Loads and validates a report JSON file. Returns the parsed report on
    success; raises jsonschema.exceptions.ValidationError otherwise."""
    with open(path, encoding="utf-8") as f:
        report = json.load(f)
    validate_report(report)
    return report
