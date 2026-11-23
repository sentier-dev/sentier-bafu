"""The files export: the installer's, with what this package adds.

`sentier_brightway.files.write_files` writes the registry, the mapping folder, the
datapackages and a manifest. Three things it does not know are put right afterwards:

* a build of the second linking was not linked through the mapping folder: the links file
  and its notice are kept in its place, and the manifest says so;
* the manifest names the data the export was made from as this repository pins it, or, for
  a data root that was supplied, the files that root holds (`pins.describe_sources`);
* the manifest carries this package's counts: the flows that name a country, and how the
  flows were linked.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING

from sentier_brightway.constants import BRIDGE_FOLDER
from sentier_brightway.files import MAPPINGS_DIR
from sentier_brightway.files import write_files as write_installer_files

from .pins import describe_sources

if TYPE_CHECKING:  # pragma: no cover - typing only
    from . import Installed

NOTICE_SUFFIX = ".NOTICE.md"
LINKS_DIR = "brightway-flows"


def notice_of(path: Path) -> Path:
    """Where the notice of a file is kept: beside it, as ``<name>.NOTICE.md``."""
    return path.with_name(path.name + NOTICE_SUFFIX)


def write_files(
    result: Installed,
    data_root: Path,
    out_dir: Path,
    datapackages: bool = True,
    overwrite: bool = False,
    include_nomenclature: bool = True,
    flow_links: Path | None = None,
    include_located: bool = True,
) -> Path:
    """Write the output folder. `include_nomenclature` and `include_located` must match the
    values `result` was built with. With `flow_links` (the file `result` was linked through)
    that file is kept in place of the mapping folder, with the notice kept beside it
    (`<name>.NOTICE.md`: the terms the file is under), and no mapping package was applied."""
    out_dir = write_installer_files(
        result.built,
        data_root=data_root,
        out_dir=Path(out_dir),
        datapackages=datapackages,
        overwrite=overwrite,
        include_nomenclature=include_nomenclature,
    )
    path = out_dir / "manifest.json"
    manifest = json.loads(path.read_text())
    if flow_links:
        shutil.rmtree(out_dir / MAPPINGS_DIR / BRIDGE_FOLDER, ignore_errors=True)
        kept = out_dir / MAPPINGS_DIR / LINKS_DIR
        kept.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(flow_links, kept / Path(flow_links).name)
        notice = notice_of(Path(flow_links))
        if notice.is_file():
            shutil.copyfile(notice, kept / notice.name)
        manifest["bridge_folder"], manifest["bridge_packages"] = None, []
    manifest["linking"] = result.coverage.linking
    # whether a flow that names a country was given that country's factor
    manifest["include_located"] = include_located
    # per data source: the pinned commit where the root holds the pinned files, and otherwise
    # the files it holds, with their SHA-256
    manifest["sources"] = describe_sources(data_root)
    manifest["coverage"] = asdict(result.coverage)
    path.write_text(json.dumps(manifest, indent=2, default=list))
    return out_dir
