"""What this package adds around the installer: the flow terms of another source, the report
file, the record of the data an export was made from, and the message when the extra is
missing."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest
from conftest import B3, INVENTORY_FOLDER, inventory_metadata
from sentier_brightway import fetch
from sentier_brightway.constants import DEFAULT_SOURCE

import bafu_brightway
from bafu_brightway import cli, pins

OTHER = "other-1"
OTHER_VERSION = "2025"


@pytest.fixture
def copy_root(data_root):
    """The fixture inventory under another name, as a patched copy of a release is: its rows
    and metadata carry the new name, and the flow terms are still the release's."""
    old = data_root / INVENTORY_FOLDER
    folder = old.with_name(f"{OTHER}-{OTHER_VERSION}")
    old.rename(folder)
    path = folder / "processes.parquet"
    proc = pd.read_parquet(path)
    proc["source"] = OTHER
    proc["source_version"] = OTHER_VERSION
    proc.to_parquet(path, index=False)
    (folder / "metadata.json").write_text(json.dumps(inventory_metadata(OTHER, OTHER_VERSION)))
    return data_root


def test_a_copy_uses_the_flow_terms_of_the_source_it_names(copy_root):
    # the copy has no flow terms of its own name
    with pytest.raises(ValueError, match="no elementary flows with source"):
        bafu_brightway.assemble(copy_root, include_nomenclature=False, source=OTHER)
    result = bafu_brightway.assemble(
        copy_root, include_nomenclature=False, source=OTHER, flow_terms_of=DEFAULT_SOURCE
    )
    # the databases are the copy's, and the flow left unlinked has the release's name for it
    assert (result.inventory_db, result.residual_db) == (OTHER, f"{OTHER}-residual")
    node = result.residual[(f"{OTHER}-residual", B3)]
    assert node["name"] == "Heat, waste"
    assert node["categories"] == ("emissions to air", "unspecified")


def test_the_command_line_takes_the_source_of_the_flow_terms(copy_root, tmp_path, capsys):
    report = tmp_path / "report.json"
    arguments = ["coverage", "--data-root", str(copy_root), "--source", OTHER]
    assert cli.main(arguments) == 2
    assert "no elementary flows with source" in capsys.readouterr().err
    assert cli.main([*arguments, "--flow-terms-of", DEFAULT_SOURCE, "--report", str(report)]) == 0
    printed = capsys.readouterr().out
    assert f"Installed {OTHER}: 2 processes" in printed
    # the report file holds the same lines, without the empty ones, and the counts
    written = json.loads(report.read_text())
    assert written["lines"] == [line for line in printed.splitlines() if line.strip()]
    assert written["linking"] == "sentier-mappings"
    assert written["coverage"]["flows_used"] == 3
    assert written["coverage"]["inventory_db"] == OTHER


def test_the_package_says_which_extra_is_missing():
    """Where the patch tool alone is installed, importing this package names the extra."""
    code = (
        "import importlib.util as u\n"
        "real = u.find_spec\n"
        "u.find_spec = lambda name, *rest: "
        "None if name == 'sentier_brightway' else real(name, *rest)\n"
        "import bafu_brightway\n"
    )
    done = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert done.returncode != 0
    assert "needs the `brightway` extra of bafu-community-fixes" in done.stderr
    assert "uv sync --extra brightway" in done.stderr


def test_the_command_is_this_packages_and_the_installer_is_the_one_that_is_installed():
    """No copy of the installer is shipped: `sentier_brightway` comes from the environment,
    and what this repository adds is under its own name."""
    import sentier_brightway

    assert "site-packages" in Path(sentier_brightway.__file__).parts
    repository = Path(__file__).resolve().parents[1]
    assert not (repository / "src" / "sentier_brightway").exists()
    assert Path(bafu_brightway.__file__).is_relative_to(repository / "src" / "bafu_brightway")
    assert cli._parser().prog == "bafu-brightway"


def _manifest(vocab_ref: str, digest: str) -> tuple[fetch.Source, ...]:
    """Two sources, both pointing at one file with ``digest``."""
    return (
        fetch.Source(
            name="sentier-inventory",
            repo="sentier-dev/sentier-inventory",
            ref="a" * 40,
            files={"data/f.parquet": digest},
        ),
        fetch.Source(
            name="sentier-vocab",
            repo="sentier-dev/sentier-vocab",
            ref=vocab_ref,
            files={"data/g.parquet": digest},
        ),
    )


def test_a_source_that_holds_the_pinned_files_is_named_with_its_commit(tmp_path):
    data = b"pinned bytes"
    manifest = _manifest("b" * 40, hashlib.sha256(data).hexdigest())
    for source in manifest:
        for path in source.files:
            target = tmp_path / source.name / path
            target.parent.mkdir(parents=True)
            target.write_bytes(data)
    assert pins.describe_sources(tmp_path, manifest) == [
        {
            "name": "sentier-inventory",
            "repo": "sentier-dev/sentier-inventory",
            "ref": "a" * 40,
            "as_pinned": True,
        },
        {
            "name": "sentier-vocab",
            "repo": "sentier-dev/sentier-vocab",
            "ref": "b" * 40,
            "as_pinned": True,
        },
    ]


def test_a_source_that_was_supplied_is_named_with_its_files_and_no_commit(tmp_path):
    data = b"pinned bytes"
    digest = hashlib.sha256(data).hexdigest()
    manifest = _manifest("b" * 40, digest)
    pinned = tmp_path / "sentier-vocab/data/g.parquet"
    release = tmp_path / "sentier-inventory/data/f.parquet"
    other = tmp_path / "sentier-inventory/data/patched/f.parquet"  # a file no pin names
    for target in (pinned, release, other):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    # the pinned file beside one no pin names, as a patched copy's inventory beside the
    # release's: the source is not the pinned one, though the pinned bytes are there
    inventory, vocab = pins.describe_sources(tmp_path, manifest)
    assert inventory == {
        "name": "sentier-inventory",
        "as_pinned": False,
        "files": {"data/f.parquet": digest, "data/patched/f.parquet": digest},
    }
    assert vocab["as_pinned"] is True and vocab["ref"] == "b" * 40
    # a pinned path with other bytes
    other.unlink()
    release.write_bytes(b"other bytes")
    inventory, _ = pins.describe_sources(tmp_path, manifest)
    assert inventory["as_pinned"] is False and "ref" not in inventory
    assert inventory["files"] == {"data/f.parquet": hashlib.sha256(b"other bytes").hexdigest()}
    # a source whose folder is not there is left out, not named as pinned
    assert pins.describe_sources(tmp_path / "nowhere", manifest) == []


def test_the_manifest_names_what_the_data_root_holds_and_no_pin_it_does_not_hold(
    data_root, tmp_path
):
    """A data root that is given is read without a check. The manifest of the export then
    lists the files the root holds with their SHA-256, and names no commit: the made-up
    files are not the pinned ones."""
    out = tmp_path / "out"
    bafu_brightway.import_files(out, data_root=data_root)
    manifest = json.loads((out / "manifest.json").read_text())
    sources = manifest["sources"]
    assert [source["name"] for source in sources] == [
        "sentier-inventory",
        "sentier-vocab",
        "sentier-methods",
        "sentier-mappings",
    ]
    for source in sources:
        assert set(source) == {"name", "as_pinned", "files"} and source["as_pinned"] is False
        for path, digest in source["files"].items():
            file = data_root / source["name"] / path
            assert digest == hashlib.sha256(file.read_bytes()).hexdigest()
    inventory, _, methods, mappings = (set(source["files"]) for source in sources)
    assert {
        "data/bafu-2026-v1/metadata.json",
        "data/bafu-2026-v1/processes.parquet",
        "data/bafu-2026-v1/exchanges.parquet",
    } <= inventory
    assert {
        "data/01-ef-3.1/methods.parquet",
        "data/01-ef-3.1/characterization-factors.parquet",
    } <= methods
    assert {"metadata.json", "biosphere-1-curated.json", "biosphere-4-nomenclature.json"} <= {
        Path(path).name for path in mappings
    }
    # what this package adds to the installer's manifest
    assert (manifest["linking"], manifest["include_located"]) == ("sentier-mappings", True)
    assert manifest["coverage"]["flows_named_without"] == 0
