"""The import fixes and the patches one by one, as a file of fixes in the format of
sentier-diagnostics (`sentier-diagnostics-fixes/1`, its SPEC section 16).

The chain (`diagnostics_account.py`) measures the import fixes and patches together: one step
from BAFU's release to the patched copy. A reader who wants to know what a set of them does,
say patch 0001 and patch 0007 without the rest, needs each measured on its own against one
base. This writes that file:

- **The base** is BAFU's release as it is, the chain's state `before`.
- **The import fixes** are one fix, built alone (`build --skip` every patch). The patch tool
  always applies them, so every patch requires them: its effect is measured against their
  build, and choosing a patch chooses them.
- **A patch whose changes reach a result** is built alone, with the import fixes
  (`build --only` the patch). Which ones do is read from the comparison of the run: a patch
  has a reach when it changed a row a score is computed from (an amount, a flow, a unit, a
  supplier), in the build with every fix. On BAFU:2026 v1 that is patch 0001 only.
- **A patch with no reach** is not built alone, and its effect is empty: in the build with
  every fix, none of its changes reaches a score. Its claim says so, and the method of the
  interactions says how it was found.
- **Two patches are a pair** where the datasets their changes reach overlap, of the kind the
  rows they change give (SPEC 16.6). A pair is not built, so its size is not measured, and a
  set that holds it is estimated.
- **The patched copy, with every fix,** is a built set, and the chain's state `after`. The checks of
  sentier-diagnostics hold it to that state and to the sum of the effects, item by item: it
  is the test of every claim above.

Noise is not measured: no build is made twice. The file is local, as the matrix is: it holds
a result for every dataset, so it never leaves the machine that built it. The run prints
what it holds, in counts.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from release_build import compare_builds as compare  # noqa: E402
from release_build import diagnostics_account  # noqa: E402

#: The id of the import fixes, taken together as one fix.
IMPORT_FIXES = "import-fixes"
#: The index of the builds `build_release.py fix-builds` made, in the folder it wrote.
INDEX = "fix-builds.json"
#: The files beside the chain the fixes file belongs to.
FIXES = "fixes.json"
#: The kinds of row change, from the rows of a comparison: a technosphere or production row
#: changes A; an elementary row changes B.
TECHNOSPHERE_ROWS = {"technosphere", "production"}


class FixesError(ValueError):
    """A file of fixes this module refuses to write."""


def read_json(path: Path):
    return diagnostics_account.read_json(path)


# ------------------------------------------------------------------------ what to build


def steps_of(summary: dict) -> tuple[list[dict], list[dict]]:
    """The import fixes and the patches of a run, in the order the patch tool applied them."""
    steps = (summary or {}).get("steps") or []
    imports = [s for s in steps if s.get("kind") == "import fix"]
    patches = [s for s in steps if s.get("kind") == "patch"]
    return imports, patches


def reached(comparison: dict) -> dict[str, int]:
    """Per step, how many datasets its changes reach in some category, from the comparison
    of BAFU's release with the build with every fix (its largest count over categories)."""
    out: dict[str, int] = {}
    for method in comparison["scores"]["methods"]:
        for step, n in method["datasets_that_could_move"].items():
            out[step] = max(out.get(step, 0), int(n))
    return out


def plan(summary: dict, comparison: dict) -> dict:
    """What `fix-builds` builds: the import fixes alone, and each patch with a reach alone with
    the import fixes; and the patches it leaves out, each with why."""
    imports, patches = steps_of(summary)
    if not imports and not patches:
        raise FixesError("the run applied no import fix and no patch: there is nothing to measure")
    reach = reached(comparison)
    ids = [p["id"] for p in patches]
    builds = [
        {
            "id": IMPORT_FIXES,
            "fixes": [IMPORT_FIXES],
            "label": "import fixes only",
            "skip": ids,
            "only": None,
        }
    ]
    not_built = []
    for patch in ids:
        if reach.get(patch, 0):
            builds.append(
                {
                    "id": patch,
                    "fixes": [IMPORT_FIXES, patch],
                    "label": f"import fixes and patch {patch} alone",
                    "skip": None,
                    "only": [patch],
                }
            )
        else:
            not_built.append(patch)
    return {"builds": builds, "not_built": not_built, "reach": {p: reach.get(p, 0) for p in ids}}


# ------------------------------------------------------------------------ the file


def scores(build: Path) -> dict[str, dict[str, float]]:
    """`{method: {code: score}}` of a build's audit, read exactly."""
    frame = compare.read_scores(Path(build))
    return {m: {c: float(v) for c, v in frame[m].items()} for m in frame.columns}


def _union(by_method: dict[str, set]) -> set:
    return set().union(*by_method.values()) if by_method else set()


def claim_of(reach: dict[str, set], text: str, origin: str) -> dict:
    """A fix's claim: the datasets its changes reach may move, in the categories they can
    affect; nothing else moves. Its list of datasets is kept: the file is local."""
    from sentier_diagnostics import claims

    entries = [
        claims.scope([method], sorted(items), "any", None, claims.MAY)
        for method, items in sorted(reach.items())
        if items
    ]
    return claims.claim(text, entries, by=claims.origin("code", origin))


def step_reach(reach: dict[str, dict[str, set]], steps: set[str]) -> dict[str, set]:
    """`{method: datasets}` that any of `steps` can move, from a comparison's reach."""
    return {
        method: set().union(*(items for step, items in by_step.items() if step in steps))
        for method, by_step in reach.items()
    }


def rows_of(base: Path, cand: Path) -> list:
    """The changed rows of two builds, each with the steps that explain it."""
    recorded = compare.read_steps(cand)
    steps = compare.steps_of_the_candidate_alone(recorded, compare.read_steps(base))
    fields = compare.step_fields(read_json(cand / "release-summary.json"))
    return compare.compare_rows(
        compare.read_inventory(base), compare.read_inventory(cand), steps, fields
    )["rows"]


def changes_of(rows: list, steps: set[str]) -> dict[str, set]:
    """What `steps` change, by row: `{"rows": {(dataset, position)}, "technosphere": bool,
    "emission": bool}`, counting only changes a score can follow."""
    keys, technosphere, emission = set(), False, False
    for row, found in rows:
        if not (row.groups & compare.SCORE_RELEVANT) or not (set(found) & steps):
            continue
        keys.add((row.process_id, row.position))
        kinds = {row.flow_type_before, row.flow_type_after}
        technosphere |= bool(kinds & TECHNOSPHERE_ROWS)
        emission |= "biosphere" in kinds
    return {"rows": keys, "technosphere": technosphere, "emission": emission}


def pair_kind(one: dict, other: dict) -> str | None:
    """Where two patches' changes meet (SPEC 16.3), the first kind that applies; None where
    they add up exactly: both change only amounts of elementary flows, in different rows."""
    from sentier_diagnostics import fixes

    if one["rows"] & other["rows"]:
        return fixes.SAME_ENTRY
    if one["technosphere"] and other["technosphere"]:
        return fixes.TECHNOSPHERE
    if (one["technosphere"] and other["emission"]) or (one["emission"] and other["technosphere"]):
        return fixes.TECHNOSPHERE_AND_EMISSION
    return None


def pairs_of(built: list[str], reach: dict[str, set], changes: dict[str, dict]) -> list[dict]:
    """Every pair of patches built alone that can interact: where the datasets their changes
    reach in the build with both overlap, and their changes meet. Neither its size nor what
    its cross term reaches is measured: a pair is not built."""
    from sentier_diagnostics import fixes

    out = []
    for k, one in enumerate(built):
        for other in built[k + 1 :]:
            if not (reach.get(one, set()) & reach.get(other, set())):
                continue
            kind = pair_kind(changes[one], changes[other])
            if kind is not None:
                out.append(fixes.pair(one, other, kind))
    return out


METHOD = (
    "Each patch that changes a row a score is computed from, in the build with every fix, was "
    "built alone with the import fixes, and its effect measured against their build. The "
    "others change no such row there, are not built alone, and have no effect. Two patches "
    "are a pair where the datasets their changes reach overlap and their changes meet; no "
    "pair is built, so none is sized. The patched copy, with every fix, is built and held to "
    "the sum of the effects."
)


def fixes_file(
    data: dict,
    full: dict,
    summary: dict,
    index: dict,
    *,
    results: dict[str, dict],
    every_fix: dict,
    claims_of: dict[str, dict],
    pairs: list[dict],
    tolerance: dict,
    notes: list[str] = (),
) -> dict:
    """The file of fixes of one run, counted and checked by sentier-diagnostics.

    - `data`, `full`: the run's local chain and its matrix; its state `before` is the base.
    - `index`: what `fix-builds` built and left out (`plan` with the outcome of each build).
    - `results`: `{fix id: {method: {code: score}}}` of each fix built alone.
    - `every_fix`: the scores of the patched copy, with every fix: the chain's state `after`.
    - `claims_of`: `{fix id: claim}`; `pairs`: `pairs_of(...)`.
    """
    from sentier_diagnostics import chain as build_chain
    from sentier_diagnostics import claims, fixes

    imports, patches = steps_of(summary)
    not_measured = build_chain.noise(note="No build is made twice.")
    built = {b["id"] for b in index["builds"]}
    made = [
        fixes.fix(
            IMPORT_FIXES,
            "Import fixes",
            kind="fix",
            about=f"{len(imports)} import fixes, applied together: they make BAFU's files "
            "readable to the importer and are applied before every patch.",
            claim=claims_of[IMPORT_FIXES],
            tolerance=tolerance,
            noise=not_measured,
        )  # fmt: skip
    ]
    for patch in patches:
        if patch["id"] in built:
            if patch["id"] not in claims_of or patch["id"] not in results:
                raise FixesError(
                    f"{patch['id']} was built alone, and its results or claim are missing"
                )
            claim = claims_of[patch["id"]]
        else:
            if patch["id"] in results:
                raise FixesError(f"{patch['id']} has results but was not built alone")
            claim = claims.claim(
                "Nothing this patch changed can move a result, in the build with every fix: it "
                "was not built alone, and its effect is empty.",
                [],
                by=claims.origin("code", "compare_builds.py, reach"),
            )
        made.append(
            fixes.fix(
                patch["id"],
                f"Patch {patch['id'].split('-', 1)[0]}",
                kind="fix",
                requires=[IMPORT_FIXES],
                about=(patch.get("description") or "").strip() or None,
                claim=claim,
                tolerance=tolerance,
                noise=not_measured,
            )  # fmt: skip
        )
    every = [IMPORT_FIXES, *(p["id"] for p in patches)]
    sets = []
    if patches:
        sets.append(
            fixes.built_set(
                "patched",
                "The patched copy, with every fix",
                every,
                every_fix,
                state="after",
                noise=not_measured,
            )  # fmt: skip
        )
    return fixes.build(
        f"{data['title']}, each fix on its own",
        data=data,
        full=full,
        base="before",
        fixes=made,
        results=results,
        interactions=fixes.interactions(
            True,
            method=METHOD,
            by=claims.origin("code", "build_release.py fixes"),
            pairs=pairs,
        ),
        built=sets,
        about=(
            "Each import fix and patch measured on its own against BAFU's release as it is, so "
            "that any set of them can be shown."
        ),
        notes=list(notes),
    )


def summary_lines(f: dict, index: dict) -> list[str]:
    """What the file holds, in counts: for the run's own lines. No dataset is named."""
    from sentier_diagnostics import fixes

    lines = [f"  {fixes.size_note(f)}"]
    for one in f["fixes"]:
        entries = sum(len(v) for v in one["effect"].values())
        how = (
            "built alone"
            if one["id"] in {b["id"] for b in index["builds"]}
            else "not built alone: no reach"
        )
        lines.append(f"  {one['id']:<44} {entries:>7} changed results  {how}")
    for one in f["built"]:
        entries = sum(len(v) for v in one["results"].values())
        lines.append(f"  {one['label']}: {entries} changed results, held to the chain and the sum")
    pairs = f["interactions"]["pairs"]
    lines.append(f"  {len(pairs)} pair(s) of fixes that can interact")
    return lines


def write(f: dict, path: Path) -> Path:
    from sentier_diagnostics import fixes

    return fixes.write(f, Path(path))


# ------------------------------------------------------------------------ the run's step


def account(
    provider: Path, patched: Path, builds: Path, out: Path, world: Path | None = None
) -> dict:
    """Write the run's local chain, its matrix and its file of fixes into `out`, from the
    builds of the run and those `fix-builds` made in `builds`. Returns the file of fixes."""
    index = read_json(Path(builds) / INDEX)
    if not index:
        raise FixesError(f"{Path(builds) / INDEX} is missing: run fix-builds first")
    failed = [b["id"] for b in index["builds"] if b.get("status") != "completed"]
    if failed:
        raise FixesError(f"not built: {', '.join(failed)}")
    folder = {b["id"]: Path(builds) / b["folder"] for b in index["builds"]}
    summary = read_json(Path(patched) / "release-summary.json")
    imports, patches = steps_of(summary)

    # The chain of the run, local and with its matrix: the fixes file hangs on its state
    # `before`, and holds the patched copy to its state `after`.
    parts: list = []
    result = compare.compare(Path(provider), Path(patched), parts)
    records, both, _moved, names, units, steps, reach = parts
    item_units, item_groups = diagnostics_account.items_of(Path(patched))
    data, full = diagnostics_account.chain(
        result, records, both, names, units, steps, reach, item_units,
        world=world, candidate=Path(provider), item_groups=item_groups, local=True,
    )  # fmt: skip
    out = Path(out)
    diagnostics_account.write(data, out / diagnostics_account.CHAIN_FILE)
    diagnostics_account.write_matrix(full, out / diagnostics_account.MATRIX_FILE)

    # Each fix against what it was measured with: the import fixes against BAFU's release,
    # a patch against the import fixes.
    imported = folder[IMPORT_FIXES]
    measured = []
    compare.compare(Path(provider), imported, measured)
    claims_of = {
        IMPORT_FIXES: claim_of(
            step_reach(measured[6], {s["id"] for s in imports}),
            "Every dataset whose supply chain reaches what an import fix changed may move, in the "
            "categories the change can affect. Nothing else moves.",
            "compare_builds.py, reach",
        )
    }
    results = {IMPORT_FIXES: scores(imported)}
    changes, alone = {}, []
    for patch in patches:
        if patch["id"] not in folder:
            continue
        alone.append(patch["id"])
        measured = []
        compare.compare(imported, folder[patch["id"]], measured)
        claims_of[patch["id"]] = claim_of(
            step_reach(measured[6], {patch["id"]}),
            "Every dataset whose supply chain reaches what this patch changed may move, in the "
            "categories the change can affect. Nothing else moves.",
            "compare_builds.py, reach",
        )
        results[patch["id"]] = scores(folder[patch["id"]])
        changes[patch["id"]] = changes_of(rows_of(imported, folder[patch["id"]]), {patch["id"]})
    # two patches meet where what they reach overlaps in the build with every fix
    pairs = pairs_of(alone, {p: _union(step_reach(reach, {p})) for p in alone}, changes)
    tolerance = diagnostics_account.tolerance_of(result)
    f = fixes_file(
        data, full, summary, index,
        results=results, every_fix=scores(Path(patched)), claims_of=claims_of, pairs=pairs,
        tolerance=tolerance,
    )  # fmt: skip
    write(f, out / FIXES)
    return f


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("provider", type=Path, help="Build folder of BAFU's release, as it is")
    parser.add_argument(
        "patched", type=Path, help="Build folder of the patched copy, with every fix"
    )
    parser.add_argument("--builds", type=Path, required=True, help="Folder fix-builds wrote")
    parser.add_argument("--out", type=Path, required=True, help="Folder for the local files")
    parser.add_argument("--world-factors", type=Path, metavar="BUILD", help="See compare")
    args = parser.parse_args(argv)
    try:
        f = account(args.provider, args.patched, args.builds, args.out, args.world_factors)
    except (FixesError, compare.CompareError, diagnostics_account.ChainError, ValueError) as error:
        print(f"The file of fixes was not written: {error}", file=sys.stderr)
        return 2
    index = read_json(args.builds / INDEX)
    print(f"Wrote {args.out / FIXES}, checked; it stays on this machine")
    for line in summary_lines(f, index):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
