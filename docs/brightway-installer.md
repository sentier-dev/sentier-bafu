# The Brightway installer, and what this repository adds to it

The installer is [sentier-brightway](https://github.com/sentier-dev/sentier-brightway). It
reads a Sentier data root (an inventory, the EF 3.1 flow terms, the EF 3.1 methods, and the
mapping from the inventory's flows to EF 3.1) and writes three Brightway databases and 25
methods, into a Brightway project or as files. Its own repository documents it.

This repository does not ship a copy of it. The `brightway` extra of this project names it
as a dependency, pinned by commit (`pyproject.toml`), and `uv.lock` holds that commit. A
change to the installer is a pull request there; here the pin moves.

## What `src/bafu_brightway` adds

| Module | What it does |
|---|---|
| `located.py` | A flow that names a country (`Water, CH`) takes that country's factor, on a flow node of its own. The mapping states the country; the methods hold the factor. |
| `countries.py` | Reads the factors of single countries from sentier-methods. The installer's reader of the methods leaves them out. |
| `brightway_flows.py` | The second linking: every elementary flow linked through Brightway Flows, with the links of patch 0010, in place of the mapping. |
| `pins.py`, `sources.toml` | The data the build is measured on, pinned by commit and SHA-256. The installer has pins of its own, which move with it; the build reads these. Also says, for the record of an export, what a data root holds. |
| `files.py` | The installer's files export, with the links file and its notice for the second linking, and this package's counts in the manifest. |
| `report.py` | The installer's counts, and beside them the flows that name a country and how the flows were linked. |
| `__init__.py`, `cli.py` | The driver that calls the installer's parts in order, and the command. |

The driver calls the installer's own functions: it loads the tables, applies the two steps
above, hands the result to the installer's `build()`, and writes with the installer's
writers. It changes nothing inside the installer.

## The command

```sh
uv sync --extra brightway
uv run --no-sync bafu-brightway coverage            # what would be linked, no Brightway
uv run --no-sync bafu-brightway db --project NAME   # into a Brightway project
uv run --no-sync bafu-brightway files --out FOLDER  # as files
```

Options beside the installer's own:

- `--skip-located`: every flow on the factor without a location.
- `--flow-links FILE`: link through Brightway Flows, with a targets file
  (`scripts/release_build/brightway-flows-targets-bafu-2026-v1.csv`).
- `--flow-terms-of SOURCE`: the flow terms of another source. A patched copy has its own
  name and the flows of the release it was made from.
- `--report FILE`: the report as JSON (its lines and its counts), which the build reads.

Without `--data-root` and without `$SENTIER_DATA_ROOT` the command downloads the files that
`src/bafu_brightway/sources.toml` pins, once, and checks them.

## What is still the installer's and missing there

- **The spelling of a location in a patched copy.** The import fixes write
  `EURwoCH` where BAFU's results workbook says `Europe without Switzerland`. The join of
  our scores with the published results is inside the installer, so until it knows that
  spelling, the datasets of that location are not compared when a patched copy is compared
  with BAFU's published results. A pull request to sentier-brightway is prepared.
- **Five unit spellings** of Brightway Flows (`m2.a`, `m3.a`, `t.km`, `p.km`, `sm3`).
  `brightway_flows.py` spells them itself; they would be better placed in the installer.
- **Which data files were read.** The installer does not record its reads, so the manifest
  of a files export says what the data root holds: the pinned commit where a folder holds
  exactly the pinned files, and otherwise the files it holds with their SHA-256.

## Tests

`installer-tests/` holds the tests of this package, on a made-up data root:

```sh
uv run --frozen --extra brightway pytest installer-tests
```

The installer's own tests are in its repository.
