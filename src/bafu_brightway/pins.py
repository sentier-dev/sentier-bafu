"""The data this repository builds from, and what a data root holds.

The installer (``sentier_brightway``) comes with pins of its own, which move with it. The
build of this repository is measured on the pins in ``sources.toml`` beside this file, so it
reads those, through the installer's own download and check."""

from __future__ import annotations

import hashlib
import os
from importlib import resources
from pathlib import Path

from sentier_brightway.fetch import (
    Source,
    default_cache_dir,
    manifest_key,
    materialize,
    parse_manifest,
)

ENV_VAR = "SENTIER_DATA_ROOT"


def load_pins() -> tuple[Source, ...]:
    """The pinned data files of this repository, by source."""
    text = resources.files("bafu_brightway").joinpath("sources.toml").read_text(encoding="utf-8")
    return parse_manifest(text)


def pinned_data_root() -> Path:
    """The pinned files, downloaded once and checked by SHA-256."""
    manifest = load_pins()
    return materialize(manifest, cache_dir=default_cache_dir() / manifest_key(manifest))


def resolve_data_root(data_root: Path | str | None) -> Path:
    """The folder given, then ``$SENTIER_DATA_ROOT``, then the pinned files of this
    repository. A folder that is given must exist; it is read as it is."""
    for given, said in ((data_root, "data_root argument"), (os.environ.get(ENV_VAR), ENV_VAR)):
        if given:
            path = Path(given).expanduser()
            if not path.is_dir():
                raise FileNotFoundError(f"{said} does not exist: {path}")
            return path
    return pinned_data_root()


def describe_sources(data_root: Path, manifest: tuple[Source, ...] | None = None) -> list[dict]:
    """What ``data_root`` holds, per pinned source, for the record of an export.

    A source whose folder holds the pinned files, with their pinned SHA-256, and no other
    file is named with its repository and commit (``as_pinned`` true). Any other source was
    supplied: it is named with the files its folder holds and their SHA-256, and with no
    commit, because none is known. A source whose folder is not there is left out.

    This says what the root holds, not what was read from it: the installer does not record
    its reads. A root that holds the pinned files beside others (a patched copy's inventory
    beside the release's) is therefore never named as pinned."""
    manifest = load_pins() if manifest is None else manifest
    described = []
    for source in manifest:
        folder = Path(data_root) / source.name
        if not folder.is_dir():
            continue
        held = {
            path.relative_to(folder).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(folder.rglob("*"))
            if path.is_file()
        }
        if held == dict(source.files):
            described.append(
                {"name": source.name, "repo": source.repo, "ref": source.ref, "as_pinned": True}
            )
        else:
            described.append({"name": source.name, "as_pinned": False, "files": held})
    return described
