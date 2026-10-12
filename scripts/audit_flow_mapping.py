"""Read a Randonneur mapping and its XLSX companion; emit aggregate checks only.

uv run --no-project --with openpyxl==3.1.5 scripts/audit_flow_mapping.py \
    mapping.json mapping.xlsx --out audit.json

This checks file consistency, not inventory or LCIA correctness. Input workbooks
are never modified. Keep source attachments outside the public repository.
"""

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import uuid


SOURCE_FIELDS = ("name", "category", "subcategory", "unit")
WORKBOOK_FIELDS = tuple("bafu_" + field for field in SOURCE_FIELDS)
KNOWN_FACTORS = {
    ("Bq", "kBq"): 0.001,
    ("km", "m"): 1000,
    ("kWh", "MJ"): 3.6,
    ("m2a", "m2*a"): 1,
    ("personkm", "p*km"): 1,
    ("tkm", "t*km"): 1,
    ("Nm3", "m3"): 1,  # Workbook declares both at normal conditions.
}


def source_key(row, fields=SOURCE_FIELDS):
    return tuple(row[field] for field in fields)


def positive_number(value):
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(value)
        and value > 0
    )


def audit(pack, rows):
    """Reconcile all mapped and unmatched workbook rows with the JSON file."""
    replacements = pack["replace"]
    json_keys = [source_key(row["source"]) for row in replacements]
    workbook_keys = [source_key(row, WORKBOOK_FIELDS) for row in rows]
    errors = []
    if len(json_keys) != len(set(json_keys)):
        errors.append("JSON contains duplicate source identities")
    if len(workbook_keys) != len(set(workbook_keys)):
        errors.append("Workbook contains duplicate source identities")
    index = dict(zip(json_keys, replacements))
    mapped = [row for row in rows if row["olca_flow_uuid"]]
    unmapped = [row for row in rows if not row["olca_flow_uuid"]]
    if set(index) != {source_key(row, WORKBOOK_FIELDS) for row in mapped}:
        errors.append("Mapped source sets differ between files")
    mismatches = Counter()
    for row in mapped:
        replacement = index.get(source_key(row, WORKBOOK_FIELDS))
        if replacement is None:
            continue
        for column, field in (
            ("olca_flow_uuid", "identifier"),
            ("olca_name", "name"),
            ("olca_context", "context"),
            ("olca_unit", "unit"),
        ):
            if row[column] != replacement["target"].get(field):
                mismatches[column] += 1
        if row["conversion_factor"] != replacement.get("conversion_factor", 1):
            mismatches["conversion_factor"] += 1
        if row["match_step"] != replacement["match_step"]:
            mismatches["match_step"] += 1
        if row["comment"] != replacement["comment"]:
            mismatches["comment"] += 1
        workbook_fallbacks = [
            value.strip()
            for value in (row["factor_fallback_uuids"] or "").split(";")
            if value.strip()
        ]
        json_fallbacks = [
            value["identifier"]
            for value in replacement.get("characterization_factor_fallbacks", [])
        ]
        if workbook_fallbacks != json_fallbacks:
            mismatches["ordered_fallbacks"] += 1
    if mismatches:
        errors.append("Workbook and JSON fields differ")
    for replacement in replacements:
        factor = replacement.get("conversion_factor", 1)
        if not positive_number(factor):
            errors.append("Non-positive or non-finite conversion factor")
        pair = (replacement["source"]["unit"], replacement["target"]["unit"])
        expected = 1 if pair[0] == pair[1] else KNOWN_FACTORS.get(pair)
        if expected is None:
            errors.append("Unit pair needs a separately reviewed conversion")
        elif factor != expected:
            errors.append("Conversion factor differs from the stated unit convention")
        identifiers = [replacement["target"]["identifier"]] + [
            value["identifier"]
            for value in replacement.get("characterization_factor_fallbacks", [])
        ]
        for identifier in identifiers:
            try:
                uuid.UUID(identifier)
            except (ValueError, TypeError, AttributeError):
                errors.append("Invalid target or fallback UUID")
    for row in rows:
        value = row["n_exchanges"]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError("Workbook exchange counts must be non-negative integers")
    exchange_rows = sum(row["n_exchanges"] for row in rows)
    mapped_exchanges = sum(row["n_exchanges"] for row in mapped)
    conversions = Counter(
        (row["source"]["unit"], row["target"]["unit"], row.get("conversion_factor", 1))
        for row in replacements
        if row["source"]["unit"] != row["target"]["unit"]
        or row.get("conversion_factor", 1) != 1
        if positive_number(row.get("conversion_factor", 1))
    )
    fallbacks = [
        value
        for row in replacements
        for value in row.get("characterization_factor_fallbacks", [])
    ]
    return {
        "kind": "mapping-file-consistency-review",
        "status": "failed" if errors else "passed",
        "errors": sorted(set(errors)),
        "mismatched_fields": dict(mismatches),
        "source_id": pack["source_id"],
        "target_id": pack["target_id"],
        "mapping_version": pack["version"],
        "declared_licenses": [entry["name"] for entry in pack.get("licenses", [])],
        "counts": {
            "workbook_source_flows": len(rows),
            "json_mapped_flows": len(replacements),
            "workbook_unmapped_flows": len(unmapped),
            "workbook_exchange_rows": exchange_rows,
            "workbook_mapped_exchange_rows": mapped_exchanges,
            "workbook_unmapped_exchange_rows": exchange_rows - mapped_exchanges,
            "workbook_weighted_mapping_coverage": (
                mapped_exchanges / exchange_rows if exchange_rows else None
            ),
            "explicit_conversion_factors": sum("conversion_factor" in row for row in replacements),
            "rows_with_fallbacks": sum(bool(row.get("characterization_factor_fallbacks")) for row in replacements),
        },
        "match_steps": dict(Counter(row["match_step"] for row in replacements)),
        "unit_mappings": [
            {"source_unit": source, "target_unit": target, "factor": factor, "flows": count}
            for (source, target, factor), count in sorted(conversions.items())
        ],
        "fallback_kinds": dict(Counter(value["kind"] for value in fallbacks)),
        "fallbacks_without_method_scope": sum(
            not value.get("method") and not value.get("methods") for value in fallbacks
        ),
        "inventory_recomputed": False,
        "lcia_recomputed": False,
        "limitations": [
            "Workbook exchange counts are reconciled, not re-counted from the source archive.",
            "Unit factors are compared between files; application to inventories is not tested.",
            "Nm3 to m3 assumes the workbook's stated normal conditions; state conditions are not independently verified.",
            "Target CF existence, factor units, directions and fallback applicability are not validated.",
            "Source archive, method package and scoring code hashes require a separate run manifest.",
        ],
    }


def run(json_path, xlsx_path):
    import openpyxl

    pack = json.loads(json_path.read_text())
    workbook = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=False)
    try:
        sheet_rows = iter(workbook["Mapping"].values)
        headers = next(sheet_rows)
        rows = [dict(zip(headers, values)) for values in sheet_rows if values[1]]
        result = audit(pack, rows)
        result["input_files"] = [
            {"name": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            for path in (json_path, xlsx_path)
        ]
        result["workbook_fallback_method_rows"] = dict(
            Counter(row[6] for row in list(workbook["Factor fallbacks"].values)[1:] if row[0])
        )
        return result
    finally:
        workbook.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mapping_json", type=Path)
    parser.add_argument("mapping_xlsx", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.mapping_json, args.mapping_xlsx)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Mapping file consistency: {result['status']}; inventory and LCIA not recomputed.")
    raise SystemExit(result["status"] != "passed")
