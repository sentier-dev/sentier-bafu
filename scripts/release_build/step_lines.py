"""What a step of a build produced, as lines for the terminal.

`build_release.py release` prints these when a step ends, so that the log of a run says
what was in it and not only that it ran. A transcript of the run then holds them too
(`transcript.py`), and the site shows the transcript line for line.

Every line is read from the record the step wrote, with the functions that fill the
manifest (`release_manifest.py`): counts, checksums, and the names of patches, findings,
databases and files. Nothing of the inventory. A step whose record is missing or can't be
read prints nothing: these lines never fail a run.
"""

import json
from pathlib import Path

try:
    from release_build import release_manifest
except ImportError:  # run as a script, from its own folder
    import release_manifest

READ_BACK = ("brightway", "openlca", "ilcd", "simapro", "ecospold1")
FINDINGS_SHOWN = 5


def build(folder: Path) -> list[str]:
    """A Brightway build: its database, what the audit counted and what it found."""
    section = release_manifest.build_section(folder)
    if section is None or section["audit"] is None:
        return []
    audit = section["audit"]
    marked = audit["marked_as"] or section["label"]
    found = [*audit["errors"], *audit["findings"]]
    on_flow = audit["elementary_exchanges_on_an_ef_3_1_flow"]
    without = audit["elementary_exchanges_without_one"]
    lines = [
        f"  database {section['database']} ({marked}): {audit['datasets']:,} datasets, "
        f"{audit['exchanges']['total']:,} exchanges, "
        f"{audit['unlinked_exchanges']:,} not linked to a supplier",
        f"  elementary exchanges: {on_flow:,} on an EF 3.1 flow, {without:,} without one",
        f"  audit {audit['status']}: {len(audit['errors']):,} errors, "
        f"{len(audit['findings']):,} findings",
    ]
    lines += [f"    {text[:300]}" for text in found[:FINDINGS_SHOWN]]
    if len(found) > FINDINGS_SHOWN:
        lines.append(f"    and {len(found) - FINDINGS_SHOWN:,} more")
    return lines


def patch_run(summary_file: Path) -> list[str]:
    """The run of the patch tool: each patch, the findings it answers, what it changed."""
    summary = release_manifest.load(summary_file)
    if summary is None:
        return []
    core = release_manifest.core(summary, None, None)
    fixes, patches = core["import_fixes"], core["patches"]
    applied = sum(1 for fix in fixes if fix["result"] == "applied")
    lines = [
        f"  import fixes: {len(fixes):,}, of which {applied:,} changed data; "
        f"patches: {len(patches):,}"
    ]
    for patch in patches:
        findings = ", ".join(patch["findings"]) or "no finding"
        changed = f"{patch['datasets_changed']:>7,} datasets"
        lines.append(f"  {patch['id']:<40} {findings:<12} {patch['result']:<10} {changed}")
    totals, output = core["totals"], core["output"]
    if "datasets_changed" in totals and "values_changed" in totals:
        lines.append(
            f"  changed in all: {totals['datasets_changed']:,} datasets, "
            f"{totals['values_changed']:,} values"
        )
    if output:
        fingerprint = str(output["fingerprint"])[:12]
        lines.append(f"  written: {output['files']:,} files, fingerprint {fingerprint}")
    return lines


def comparison(file: Path) -> list[str]:
    """Two builds compared: the rows that differ, and whether a step explains each."""
    section = release_manifest.comparison_section(file)
    if section is None:
        return []
    lines = [
        f"  {section['exchange_rows_compared']:,} exchange rows compared with "
        f"{section['baseline']}: {section['exchange_rows_changed']:,} changed, "
        f"{section['rows_no_step_explains']:,} that no step recorded on their dataset explains",
    ]
    by_step = section["rows_changed_by_step"]
    if by_step:
        changed = ", ".join(f"{step} {rows:,}" for step, rows in by_step.items())
        lines.append(f"  changed by: {changed}")
    moved = section["datasets_whose_score_moved_by_method_and_step"]
    lines.append(
        f"  {section['methods_compared']:,} methods compared: scores moved in {len(moved):,} "
        f"of them, {section['moved_scores_no_change_explains']:,} moved scores that no change "
        "explains"
    )
    lines.append(f"  comparison {section['status']}")
    return lines


def exports(folder: Path) -> list[str]:
    """The export files with size and checksum, and whether each was read back."""
    section = release_manifest.exports_section(folder)
    if section is None:
        return []
    lines = []
    for file in section["files"]:
        read = ""
        if file["kind"] in READ_BACK:
            matches = section["read_back_matches"].get(file["kind"])
            read = "read back: " + {True: "matches", "counted": "counted only"}.get(
                matches, "differs"
            )
        line = f"  {file['name']:<38} {file['bytes']:>12,} bytes  sha256 {file['sha256'][:12]}"
        lines.append(f"{line}  {read}".rstrip())
    for kind, entry in sorted(section["held_back"].items()):
        lines.append(
            f"  {kind}: written, read back and held back, not among the files "
            f"({entry['differences']:,} difference(s)). {entry['reason']}"
        )
    lines.append(
        f"  label {section['label']}; "
        "a build with a tag keeps these files under its tag; any other keeps none"
    )
    return lines


def fix_builds(folder: Path) -> list[str]:
    """Each fix built on its own: what each build holds, and the patches left out."""
    index = json.loads((folder / "fix-builds.json").read_text())
    lines = []
    for one in index["builds"]:
        lines.append(f"  {one['label']}: {one['status']} in {one['seconds']} s")
        lines += [f"  {line}" for line in build(folder / one["folder"])]
    if index["not_built"]:
        lines.append(
            f"  not built alone, since none of their changes reaches a result: "
            f"{', '.join(index['not_built'])}"
        )
    return lines


def fixes(file: Path) -> list[str]:
    """The file of fixes, in counts: what each fix changes, and the built sets. It stays on
    the machine; no dataset is named."""
    data = json.loads(file.read_text())

    def entries(sparse: dict) -> int:
        return sum(len(v) for v in sparse.values())

    lines = [
        f"  {len(data['fixes']):,} fixes over {len(data['items']):,} datasets in "
        f"{len(data['indicators']):,} categories, measured against "
        f"{data['of']['base']!r} of {data['of']['file']}, checked"
    ]
    for one in data["fixes"]:
        lines.append(f"  {one['id']:<44} {entries(one['effect']):>9,} results it changes")
    for one in data["built"]:
        lines.append(
            f"  built: {one['label']}, {entries(one['results']):,} results it changes, "
            "held to the chain and to the sum of the fixes"
        )
    pairs = data["interactions"]["pairs"]
    lines.append(f"  pairs of fixes that can interact: {len(pairs):,}")
    return lines


def lines(name: str, out: Path) -> list[str]:
    """The lines of one step of a build that wrote into `out`. Never raises."""
    try:
        if name == "provider build":
            return build(out / "provider")
        if name == "world factors build":
            return build(out / "world-factors")
        if name == "patched build":
            return patch_run(out / "patched" / "release-summary.json") + build(out / "patched")
        if name == "comparison":
            return comparison(out / "comparison.json")
        if name == "exports":
            return exports(out / "exports" / "patched")
        if name == "fix builds":
            return fix_builds(out / "fix-builds")
        if name == "fixes":
            return fixes(out / "local" / "fixes.json")
        for ending, make, place in (
            (" build", build, "build"),
            (" comparison", comparison, "comparison.json"),
            (" exports", exports, "exports"),
        ):
            if name.endswith(ending):
                return make(out / "contributions" / name[: -len(ending)].lower() / place)
    except Exception:  # noqa: BLE001 - a line that can't be written is left out
        return []
    return []
