"""BAFU's release in Brightway, with what this repository adds to the Brightway installer.

The installer is sentier-brightway (`sentier_brightway`), pinned by commit in this project's
`brightway` extra. It reads a Sentier data root and writes an inventory, the EF 3.1 flows
and the EF 3.1 methods into a Brightway project, or as files. This package calls its parts
and adds two steps of this repository's own:

* a flow that names a country takes that country's factor (`located`);
* the elementary flows can be linked through Brightway Flows, with the links of patch 0010,
  in place of the mapping of sentier-mappings (`brightway_flows`).

It also reads the data this repository's build is measured on (`pins`), lets a patched copy
use the flow terms of the release it was made from (`flow_terms_of`), and writes a report
of what was linked. It needs the `brightway` extra, which the patch tool does not.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from importlib.util import find_spec
from pathlib import Path
from types import MappingProxyType

if find_spec("sentier_brightway") is None:  # the patch tool alone is installed
    raise ModuleNotFoundError(
        "bafu_brightway needs the `brightway` extra of bafu-community-fixes, which is not "
        "installed here. In a checkout of sentier-bafu: `uv sync --extra brightway`, or run "
        "the command with `uv run --extra brightway`."
    )

import pandas as pd  # noqa: E402
from sentier_brightway import backtest  # noqa: E402
from sentier_brightway.bridge import BridgeEntry, load_bridge  # noqa: E402
from sentier_brightway.build import BoundMethod, BuildResult  # noqa: E402
from sentier_brightway.build import build as build_installer  # noqa: E402
from sentier_brightway.constants import BIOSPHERE_DB, DEFAULT_SOURCE  # noqa: E402
from sentier_brightway.flows import load_ef_flows, load_source_flows  # noqa: E402
from sentier_brightway.inventory import Inventory, load_inventory  # noqa: E402
from sentier_brightway.methods import MethodSpec, load_methods  # noqa: E402

from . import brightway_flows  # noqa: E402
from .countries import load_factors_of_countries  # noqa: E402
from .located import Countries, locate  # noqa: E402
from .pins import resolve_data_root  # noqa: E402
from .report import Coverage, render  # noqa: E402

__all__ = [
    "import_db",
    "import_files",
    "DEFAULT_SOURCE",
    "coverage",
    "assemble",
    "build",
    "render",
    "Coverage",
    "Installed",
    "backtest",
]


@dataclass(frozen=True)
class Installed:
    """What a build made: the installer's result, and what this package knows beside it."""

    #: the installer's own result, with the nodes of countries completed; what its writers take
    built: BuildResult
    #: the installer's counts, and the flows that name a country and how the flows were linked
    coverage: Coverage
    #: source flow code -> its link, as the exchanges were linked
    links: Mapping[str, BridgeEntry]

    @property
    def biosphere(self) -> Mapping:
        return self.built.biosphere

    @property
    def residual(self) -> Mapping:
        return self.built.residual

    @property
    def inventory(self) -> Mapping:
        return self.built.inventory

    @property
    def methods(self) -> tuple[BoundMethod, ...]:
        return self.built.methods

    @property
    def source(self) -> str:
        return self.built.source

    @property
    def source_version(self) -> str | None:
        return self.built.source_version

    @property
    def inventory_db(self) -> str:
        return self.built.inventory_db

    @property
    def residual_db(self) -> str:
        return self.built.residual_db


def _with_flows_of_countries(
    ef_flows: pd.DataFrame, methods: tuple[MethodSpec, ...], nodes: Mapping[str, tuple[str, str]]
) -> pd.DataFrame:
    """The flow table with one row for each flow of a country: the flow again, with the
    country in its name. The installer makes a node of each row; name and compartment are
    worked out as the installer works them out for the flow itself."""
    names = dict(zip(ef_flows["code"], ef_flows["name"], strict=True))
    cas = dict(zip(ef_flows["code"], ef_flows["cas_number"], strict=True))
    categories = dict(zip(ef_flows["code"], ef_flows["categories"], strict=True))
    from_methods: dict[str, tuple[str, ...]] = {}
    for spec in methods:
        for code, name in spec.flow_name.items():
            names.setdefault(code, name)
        for code, context in spec.flow_context.items():
            if context:
                from_methods.setdefault(code, context)
    categories |= from_methods
    rows = [
        {
            "code": key,
            "name": f"{names.get(code, code)}, {location}",
            "categories": tuple(categories.get(code, ())),
            "cas_number": cas.get(code),
        }
        for key, (code, location) in sorted(nodes.items())
    ]
    if not rows:
        return ef_flows
    added = pd.DataFrame(rows, columns=["code", "name", "categories", "cas_number"]).astype(object)
    return pd.concat([ef_flows, added], ignore_index=True)


def build(
    inventory: Inventory,
    ef_flows: pd.DataFrame,
    source_flows: pd.DataFrame,
    bridge: Mapping[str, BridgeEntry],
    methods: tuple[MethodSpec, ...],
    countries: Countries | None = None,
    include_located: bool = True,
    linking: str = "sentier-mappings",
    link_lines: tuple[str, ...] = (),
) -> Installed:
    """The nodes of the three databases and the methods, from the tables: the installer's
    `build()`, after a linked flow that names a country was given the target and the factors
    of that country (`located.locate`). `include_located=False` leaves every flow on the
    factor without a location."""
    nodes: Mapping[str, tuple[str, str]] | None = None
    if include_located:
        found = locate(bridge, methods, countries or {})
        bridge, methods, nodes = found.bridge, found.methods, found.nodes
        ef_flows = _with_flows_of_countries(ef_flows, methods, nodes)
    built = build_installer(
        inventory=inventory,
        ef_flows=ef_flows,
        bafu_flows=source_flows,
        bridge=bridge,
        methods=methods,
    )
    for key, (_, location) in (nodes or {}).items():
        node = built.biosphere.get((BIOSPHERE_DB, key))
        if node is not None:
            node["location"] = location
    bio = inventory.exchanges[inventory.exchanges["flow_type"] == "biosphere"]
    used = set(bio["flow"])
    named = [code for code in used if code in bridge and bridge[code].target_location]
    cover = Coverage(
        **asdict(built.coverage),
        flows_located=sum(1 for code in named if bridge[code].target_code in (nodes or {})),
        flows_named_without=0
        if nodes is None
        else sum(1 for code in named if bridge[code].target_code not in nodes),
        linking=linking,
        link_lines=tuple(link_lines),
    )
    return Installed(built=built, coverage=cover, links=MappingProxyType(dict(bridge)))


def _assemble_from_root(
    root: Path,
    include_nomenclature: bool,
    source: str,
    source_version: str | None = None,
    flow_links: Path | str | None = None,
    flow_terms_of: str | None = None,
    include_located: bool = True,
) -> Installed:
    """Build from an already resolved data root. With `flow_links` (the targets file of
    patch 0010's links) the flows are linked through Brightway Flows and the mapping folder
    is read only for the country a flow names. `flow_terms_of` names the source whose
    elementary flow terms the inventory uses, when that is not the inventory's own source: a
    patched copy of a release has its own name and the release's flows."""
    inventory = load_inventory(root, source=source, source_version=source_version)
    ef_flows = load_ef_flows(root)
    source_flows = load_source_flows(root, flow_terms_of or source)
    methods = load_methods(root)
    countries = load_factors_of_countries(root)
    if flow_links is None:
        bridge = load_bridge(root, include_nomenclature=include_nomenclature)
        return build(inventory, ef_flows, source_flows, bridge, methods, countries, include_located)
    # the mapping does not link the flows here, and it is still read: it is the one place
    # that states which country a flow names
    stated = load_bridge(root)
    links = brightway_flows.link(
        inventory,
        source_flows,
        ef_flows,
        methods,
        brightway_flows.load_targets(flow_links),
        include_without_factor=include_nomenclature,
        locations={
            code: entry.target_location for code, entry in stated.items() if entry.target_location
        },
        in_mapping=frozenset(stated),
        countries=countries,
    )
    return build(
        inventory,
        links.ef_flows,
        source_flows,
        links.bridge,
        links.methods,
        links.countries,
        include_located,
        linking=brightway_flows.LINKING,
        link_lines=links.report.lines(),
    )


def assemble(
    data_root: Path | str | None = None,
    include_nomenclature: bool = True,
    source: str = DEFAULT_SOURCE,
    source_version: str | None = None,
    flow_links: Path | str | None = None,
    flow_terms_of: str | None = None,
    include_located: bool = True,
) -> Installed:
    """Read the Sentier data (a local root, or the pinned files of this repository) and build
    the node dicts. `source` selects the inventory folder and names the databases after it;
    `flow_links` links the elementary flows through Brightway Flows. A flow that names a
    country takes that country's factor unless `include_located` is False."""
    return _assemble_from_root(
        resolve_data_root(data_root),
        include_nomenclature,
        source,
        source_version,
        flow_links,
        flow_terms_of,
        include_located,
    )


def coverage(
    data_root: Path | str | None = None,
    include_nomenclature: bool = True,
    source: str = DEFAULT_SOURCE,
    source_version: str | None = None,
    flow_links: Path | str | None = None,
    flow_terms_of: str | None = None,
    include_located: bool = True,
) -> Coverage:
    """What would be linked, without touching Brightway."""
    return assemble(
        data_root,
        include_nomenclature,
        source,
        source_version,
        flow_links,
        flow_terms_of,
        include_located,
    ).coverage


def import_db(
    project: str,
    overwrite: bool = False,
    data_root: Path | str | None = None,
    include_nomenclature: bool = True,
    source: str = DEFAULT_SOURCE,
    source_version: str | None = None,
    flow_links: Path | str | None = None,
    flow_terms_of: str | None = None,
    include_located: bool = True,
) -> Coverage:
    """Install one inventory `source`, the EF 3.1 flows and the EF 3.1 methods into the
    Brightway project `project`, with the installer's own writer."""
    from sentier_brightway.writer import write  # bw2data import stays lazy

    result = assemble(
        data_root,
        include_nomenclature,
        source,
        source_version,
        flow_links,
        flow_terms_of,
        include_located,
    )
    write(result.built, project=project, overwrite=overwrite)
    return result.coverage


def import_files(
    out_dir: Path | str,
    data_root: Path | str | None = None,
    include_nomenclature: bool = True,
    datapackages: bool = True,
    overwrite: bool = False,
    source: str = DEFAULT_SOURCE,
    source_version: str | None = None,
    flow_links: Path | str | None = None,
    flow_terms_of: str | None = None,
    include_located: bool = True,
) -> Coverage:
    """Write one inventory `source` and EF 3.1 as plain files instead of a Brightway project:
    the installer's files export, with what this package adds said in its manifest and, for
    the second linking, the links file and its notice kept in place of the mapping folder."""
    from .files import write_files

    root = resolve_data_root(data_root)
    result = _assemble_from_root(
        root,
        include_nomenclature,
        source,
        source_version,
        flow_links,
        flow_terms_of,
        include_located,
    )
    write_files(
        result,
        data_root=root,
        out_dir=Path(out_dir),
        datapackages=datapackages,
        overwrite=overwrite,
        include_nomenclature=include_nomenclature,
        flow_links=None if flow_links is None else Path(flow_links),
        include_located=include_located,
    )
    return result.coverage
