"""The comparison of the builds, as a chain of states in the format of sentier-diagnostics.

`compare_builds.py` finds what changed between two builds and explains it (`comparison.json`).
This writes what it found as `diagnostics.json`, in the format every Sentier dataset repository
writes (sentier-dev/sentier-diagnostics, `sentier-diagnostics/1`): the results of every dataset
in every impact category in each state, one class per value by one counting rule, and each
step held against its claim.

The chain of a run's own comparison has three states and two steps:

1. BAFU's release with the world's factors (`build --skip-located`), then with the countries'
   factors: a flow that names a country takes that country's factor. The claim of that step
   is read from the build, not written by hand: the categories in which a country's own
   factor is used (`located_by_method` of the install report). On BAFU:2026 v1 those are
   water use and land use.
2. BAFU's release, then the patched copy: the import fixes and the community patches,
   applied together. Its claim is the comparison's own reach: every dataset whose supply
   chain reaches what a step changed may move, in the categories the change can affect.
   The list of those datasets stays here (`claim_lists=False`); the file says how many.

Without a build of the world's factors the chain has the last two states only. A
contribution's comparison is the patched copy, then the patched copy with that contribution.

Noise belongs to a state: two builds of it differ by it (sentier-diagnostics, SPEC 5.3). It is
not measured here, since no state is built twice in a run, and each state says so.

Scores are read exactly, as they were written. A default CSV reader rounds the last bit of
about half of them, which merges distinct results and drops changes: read that way, patch
0001 of BAFU:2026 v1 changes 79 results instead of 86 (SPEC 16.4). Both sides of every
comparison are read the same way (`compare_builds.read_scores`).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from release_build import before_after_account  # noqa: E402

LISTED = before_after_account.LISTED
#: The files of a local chain: the chain, and its full matrix beside it. They hold a result
#: for every dataset, so they stay on the machine that built them (`chain(..., local=True)`).
CHAIN_FILE = "diagnostics.json"
MATRIX_FILE = "matrix.json"
#: What the comparison counts as moved. The steps of the chain use it too, so that a value
#: the comparison calls unexplained is never one the chain calls "agrees".
TOLERANCE_NOTE = "the threshold of the comparison of two builds (compare_builds.py)"
#: The comparison judges every value, however small. sentier-diagnostics sets values below
#: a floor aside as "near zero" (1 % of a category's median size, unless told otherwise),
#: and a value the comparison calls unexplained could then go unjudged in the chain. With
#: no floor the two files count by one rule.
FLOOR_FACTOR = 0.0
#: The comparison's label for a moved value that no step explains. It is the comparison's
#: finding and no step: it is no part of what the steps claim to reach.
UNEXPLAINED = "unexplained"


class ChainError(ValueError):
    """A chain this module refuses to write."""


def read_json(path: Path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def scores_of(build: Path, methods: list[str], codes: list[str]) -> dict:
    """`{method: {code: score}}` of one build's audit, for the datasets compared."""
    import pandas as pd

    frame = pd.read_csv(Path(build) / "audit" / "scores.csv", float_precision="round_trip")
    frame = frame.set_index("code")
    missing = [m for m in methods if m not in frame.columns]
    if missing:
        raise ChainError(f"{build}: the audit has no scores in {', '.join(missing)}")
    return {
        m: {c: (float(frame.at[c, m]) if c in frame.index else None) for c in codes}
        for m in methods
    }


def items_of(build: Path) -> tuple[dict[str, str], dict[str, str | None]]:
    """The reference unit of each dataset of a build, and its sector: the group a reader
    filters by (a dataset without a sector has none)."""
    from release_build import compare_builds

    processes = compare_builds.read_inventory(Path(build))[0].set_index("process_id")
    units = {code: str(unit) for code, unit in processes["reference_unit"].items()}
    groups = {
        code: str(sector).strip() or None
        for code, sector in processes["sector"].items()
        if isinstance(sector, str)
    }
    return units, groups


def tolerance_of(comparison: dict) -> dict:
    """The tolerance of a step: the comparison's own threshold."""
    from sentier_diagnostics import chain as build_chain

    return build_chain.tolerance(comparison["scores"]["tolerance"], "declared", TOLERANCE_NOTE)


def located_by_method(build: Path) -> list[str] | None:
    """The categories in which a flow that names a country takes that country's own factor,
    from the install report of a build; None where the report does not say."""
    report = read_json(Path(build) / "logs" / "install-report.json") or {}
    found = (report.get("coverage") or {}).get("located_by_method")
    if found is None:
        return None
    return sorted(method for method, n in found if n)


def refuse_another_state(world: dict, provider: dict, folder: Path) -> None:
    """The state "the world's factors" is BAFU's release, built as the provider build was,
    with the countries' factors left out. Any other build under that name would make the
    step "the countries' factors" show something else."""
    install, of_provider = world.get("install") or {}, provider.get("install") or {}
    if install.get("located") is not False:
        raise ChainError(
            f"{folder}: not a build with the world's factors (its record does not say "
            "`install.located: false`; build it with --skip-located)"
        )
    if world.get("patched"):
        raise ChainError(f"{folder}: a patched copy, not BAFU's release as it is")
    for what, one, other in (
        ("release", (world.get("release") or {}).get("name"),
         (provider.get("release") or {}).get("name")),
        ("linking", install.get("flow_links"), of_provider.get("flow_links")),
    ):  # fmt: skip
        if one != other:
            raise ChainError(
                f"{folder}: built with another {what} than the build of BAFU's release it is "
                f"compared with ({one!r}, not {other!r})"
            )


def reach_claim(reach: dict[str, dict[str, set]], text: str) -> dict:
    """The claim of a step whose scope is the comparison's reach, per category."""
    from sentier_diagnostics import claims

    reached = {
        method: set().union(*(found for step, found in by_step.items() if step != UNEXPLAINED))
        for method, by_step in sorted(reach.items())
    }
    entries = [
        claims.scope([method], found, "any", None, claims.MAY)
        for method, found in reached.items()
        if found
    ]
    union = set().union(*(e["items"] for e in entries)) if entries else set()
    return claims.claim(
        text, entries, by=claims.origin("code", "compare_builds.py, reach"), reach=len(union)
    )


def chain(
    comparison: dict,
    records: tuple[dict, dict],
    scores: tuple[dict, dict],
    names: dict[str, dict],
    units: dict[str, str | None],
    steps: dict[str, dict],
    reach: dict[str, dict[str, set]],
    item_units: dict[str, str | None],
    world: Path | None = None,
    candidate: Path | None = None,
    listed: int = LISTED,
    item_groups: dict[str, str | None] | None = None,
    local: bool = False,
) -> dict | tuple[dict, dict]:
    """The chain of one comparison, checked by sentier-diagnostics. `world` is the build of
    BAFU's release with the world's factors, `candidate` the build whose install report names
    the categories of the countries' factors (the build of BAFU's release). `item_groups` is
    each dataset's sector, by which a reader filters.

    `local`: the chain for this machine only, and its full matrix, as `(chain, matrix)`: every
    dataset with its result in every state, and each claim with its list of datasets. A file
    of fixes hangs on it (`fixes_account.py`). Without it, the chain that may be published:
    the datasets listed, each claim's size only."""
    from sentier_diagnostics import chain as build_chain
    from sentier_diagnostics import claims

    before, after = scores
    methods = list(before)
    codes = sorted(set().union(*(set(v) for v in before.values())))
    title, one, other = before_after_account.sides(*records)
    contribution = (records[1] or {}).get("contribution")
    tolerance = tolerance_of(comparison)
    # noise belongs to a state; none is built twice in a run
    not_measured = build_chain.noise(note="No state is built twice in a run.")

    def state(id_, side, record):
        tools = (record or {}).get("tools") or {}
        identity = {
            "commit": str(tools.get("this repository") or "")[:12] or None,
            "database": ((record or {}).get("databases") or {}).get("inventory"),
            "machine": tools.get("platform"),
        }
        return build_chain.state(
            id_, side[0], about=side[1], identity={k: str(v) for k, v in identity.items() if v},
            noise=not_measured,
        )  # fmt: skip

    fixes = [s for s in steps.values() if s.get("kind") in ("import fix", "patch")]
    if contribution:
        step_text = (
            f"Contribution {contribution['id']}, applied to the patched copy. Every dataset "
            "whose supply chain reaches an input it changed may move, in every category. "
            "Nothing else moves."
        )
        last = build_chain.step(
            "contribution", f"Contribution {contribution['id']}", kind="contribution",
            about=(contribution.get("title") or None), claim=reach_claim(reach, step_text),
            tolerance=tolerance,
        )  # fmt: skip
    else:
        n_fix = sum(1 for s in fixes if s["kind"] == "import fix")
        n_patch = sum(1 for s in fixes if s["kind"] == "patch")
        last = build_chain.step(
            "fixes", "Import fixes and patches", kind="fix",
            about=f"{n_fix} import fixes and {n_patch} community patches, applied together; "
            "they are not built one at a time.",
            claim=reach_claim(
                reach,
                "Every dataset whose supply chain reaches what an import fix or patch changed may "
                "move, in the categories the change can affect. Nothing else moves.",
            ),
            tolerance=tolerance,
        )  # fmt: skip
    states = [state("before", one, records[0]), state("after", other, records[1])]
    values = {"before": before, "after": after}
    steps_out = [last]
    if world is not None and not contribution:
        categories = located_by_method(candidate) if candidate else None
        if categories is None:
            raise ChainError(
                "the install report of BAFU's release does not say in which categories a "
                "country's own factor is used (coverage.located_by_method)"
            )
        unknown = sorted(set(categories) - set(methods))
        if unknown:
            raise ChainError(
                f"the countries' factors are used in categories not compared: {unknown}"
            )
        # in words, the category a reader looks for first ("water use and land use")
        words = sorted(
            (before_after_account.name_of(m).lower() for m in categories),
            key=lambda word: (word != "water use", word),
        )
        names_of = " and ".join([", ".join(words[:-1]), words[-1]] if len(words) > 1 else words)
        located = build_chain.step(
            "located-factors", "The countries' factors", kind="method",
            about="A flow that names a country takes that country's factor instead of the world's.",
            claim=claims.claim(
                f"{names_of[:1].upper() + names_of[1:]} may move; nothing else moves."
                if categories else "Nothing moves.",
                [claims.scope(categories, "*", "any", None, claims.MAY)] if categories else [],
                by=claims.origin("code", "install report, located_by_method"),
            ),
            tolerance=tolerance,
        )  # fmt: skip
        world_record = read_json(Path(world) / "build.json") or {}
        refuse_another_state(world_record, records[0], world)
        world_side = (
            "BAFU's release, the world's factors",
            "Every elementary flow on the world's factor, also one that names a country.",
        )
        states.insert(0, state("world", world_side, world_record))
        values = {"world": scores_of(world, methods, codes), **values}
        steps_out = [located, last]
    corrected = comparison["linked_on_the_declared_flow"]["exchanges"]
    notes = []
    if corrected:
        notes.append(
            f"{corrected} elementary exchanges whose name or compartment a patch corrects are "
            "linked on the flow as BAFU declared it, so the correction changes the label and "
            "moves no result."
        )
    make = (
        (lambda *a, **k: build_chain.build_with_matrix(*a, matrix_file=MATRIX_FILE, **k))
        if local
        else build_chain.build
    )
    found = make(
        title,
        about="The builds of one run, compared score by score in every impact category.",
        indicators=[
            (m, before_after_account.name_of(m), before_after_account.SHORT.get(m), units.get(m))
            for m in methods
        ],  # fmt: skip
        states=states,
        steps=steps_out,
        values=values,
        units=item_units,
        names={
            c: {
                "name": (names.get(c) or {}).get("name") or c,
                "place": (names.get(c) or {}).get("location"),
                "group": (item_groups or {}).get(c) or None,
            }
            for c in codes
        },  # fmt: skip
        item_word=("dataset", "datasets"),
        floor_factor=FLOOR_FACTOR,
        listed=listed,
        audience="local" if local else "public",
        claim_lists=local,
        notes=notes,
    )
    data = found[0] if local else found
    # the chain and the comparison must agree on what nothing explains, or neither is believed
    unexplained = sum(
        m["moved_by_step"].get(UNEXPLAINED, 0) for m in comparison["scores"]["methods"]
    )
    outside = sum(
        (block.get("verdicts") or {}).get("not claimed", 0)
        for block in data["counts"]["steps"][last["id"]].values()
    )
    if outside != unexplained:
        raise ChainError(
            f"{outside} values moved outside the reach of every step, and the comparison calls "
            f"{unexplained} unexplained"
        )
    return found


def write(data: dict, path: Path) -> Path:
    from sentier_diagnostics import chain as build_chain

    return build_chain.write(data, Path(path))


def write_matrix(full: dict, path: Path) -> Path:
    """The full matrix of a local chain, beside it."""
    from sentier_diagnostics import matrix

    return matrix.write(full, Path(path))
