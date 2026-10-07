"""Measure a sentier-brightway file export without publishing inventory amounts.

Run with pandas and pyarrow installed, for example:
uv run --with pandas==2.2.3 --with pyarrow==19.0.1 scripts/audit_registry.py EXPORT --out REPORT
"""

import argparse
import hashlib
import json
import math
from pathlib import Path

import pandas as pd

CORE_GASES = {
    "methane",
    "methane, fossil",
    "methane, non-fossil",
    "methane, biogenic",
    "methane, peat oxidation",
    "carbon dioxide",
    "carbon dioxide, fossil",
    "carbon dioxide, non-fossil",
    "carbon dioxide, biogenic",
    "carbon dioxide, peat oxidation",
    "dinitrogen monoxide",
    "dinitrogen monoxide, peat oxidation",
}


def digest(path):
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def audit(root):
    manifest = json.loads((root / "manifest.json").read_text())
    files = {
        name: root / "registry" / f"{name}.parquet"
        for name in (
            "processes",
            "biosphere",
            "exchanges",
            "methods",
            "characterization-factors",
        )
    }
    process, bio, exchanges, methods, cfs = (pd.read_parquet(files[name]) for name in files)
    errors = []
    counts = {
        "processes": len(process),
        "production": int(exchanges.type.eq("production").sum()),
        "technosphere": int(exchanges.type.eq("technosphere").sum()),
        "biosphere": int(exchanges.type.eq("biosphere").sum()),
    }
    if sum(counts[k] for k in ("production", "technosphere", "biosphere")) != len(exchanges):
        errors.append("Unexpected exchange kinds; counts do not cover every row")
    if manifest["counts"]["exchanges"] != len(exchanges) or manifest["counts"]["processes"] != len(
        process
    ):
        errors.append("Manifest counts disagree with registry")
    if (
        process.bw_id.duplicated().any()
        or bio.bw_id.duplicated().any()
        or set(process.bw_id) & set(bio.bw_id)
    ):
        errors.append("Process and biosphere identities must be unique and disjoint")
    if not exchanges.process_bw_id.isin(process.bw_id).all():
        errors.append("Exchange references a missing consumer process")
    for kind, ids in [
        ("technosphere", process.bw_id),
        ("production", process.bw_id),
        ("biosphere", bio.bw_id),
    ]:
        if not exchanges.loc[exchanges.type.eq(kind), "input_bw_id"].isin(ids).all():
            errors.append(f"{kind} exchange references a missing target")
    if not all(math.isfinite(float(v)) for v in exchanges.amount):
        errors.append("Non-finite exchange amount")
    if not all(math.isfinite(float(v)) for v in cfs.factor):
        errors.append("Non-finite characterization factor")
    if cfs.duplicated(["method_id", "flow_bw_id"]).any():
        errors.append("Duplicate method/flow factors would accumulate")
    if not cfs.method_id.isin(methods.method_id).all() or not cfs.flow_bw_id.isin(bio.bw_id).all():
        errors.append("Characterization factor references missing method or biosphere identity")
    emitted = set(
        exchanges.loc[exchanges.type.eq("biosphere") & exchanges.amount.ne(0), "input_bw_id"]
    )
    required = (
        set(
            bio.loc[
                bio.name.str.strip().str.casefold().isin(CORE_GASES)
                & bio.categories.str.split("::")
                .str[0]
                .str.casefold()
                .isin(["air", "emissions to air"]),
                "bw_id",
            ]
        )
        & emitted
    )
    results = []
    for method in methods.itertuples(index=False):
        factors = cfs.loc[cfs.method_id.eq(method.method_id)]
        covered = set(factors.flow_bw_id)
        key = str(method.method_id)
        headline_climate = key.endswith(":climate-change")
        missing_required = required - covered if headline_climate else set()
        missing = bio.loc[
            bio.bw_id.isin(missing_required),
            ["database", "code", "name", "categories", "unit"],
        ].to_dict("records")
        if missing_required:
            errors.append(
                f"{key}: {len(missing_required)} emitted core greenhouse gas identities lack factors"
            )
        results.append(
            {
                "method": key,
                "emitted_flows": len(emitted),
                "characterized_flows": len(emitted & covered),
                "explicit_zero_flows": int(
                    factors.loc[factors.flow_bw_id.isin(emitted), "factor"].eq(0).sum()
                ),
                "missing_flows": len(emitted - covered),
                "missing_core_gases": missing,
            }
        )
    if not methods.method_id.astype(str).str.endswith(":climate-change").any():
        errors.append("No headline EF climate-change method available for core-gas coverage gate")
    return {
        "status": "failed" if errors else "passed",
        "errors": errors,
        "source": manifest["source"],
        "release": manifest["source_version"],
        "source_pins": manifest["sources"],
        "served_counts": counts,
        "manifest_counts_match": manifest["counts"]["exchanges"] == len(exchanges),
        "mapped_flow_coverage": manifest.get("coverage", {}),
        "applied_packages": manifest.get("bridge_packages", []),
        "artifact_sha256": {name: digest(path) for name, path in files.items()},
        "methods": results,
        "scope": "Exported parquet registry identity and core CO2/CH4/N2O air-flow coverage only. Does not reproduce raw-source parity, validate all greenhouse gases, or calculate LCIA scores.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.export)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(
        f"{result['status']}: {len(result['errors'])} errors; {result['served_counts']}; evidence: {args.out}"
    )
    raise SystemExit(int(bool(result["errors"])))
