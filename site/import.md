# Import and use BAFU / UVEK

Start with a reproducible Sentier baseline, then apply proposed improvements in a separate candidate. This project coordinates the import, evidence and review; the established Sentier components own parsing and artifacts.

## The import path

| Component | Responsibility |
|---|---|
| [sentier-importers](https://github.com/sentier-dev/sentier-importers) | Parse the provider release and preserve source identities |
| [sentier-inventory](https://github.com/sentier-dev/sentier-inventory) | Inventory artifacts and schema |
| [sentier-methods](https://github.com/sentier-dev/sentier-methods) | Method factor tables |
| [sentier-mappings](https://github.com/sentier-dev/sentier-mappings) | Traceable linking and mapping packages |
| [sentier-brightway](https://github.com/sentier-dev/sentier-brightway) | Build and export the pinned application baseline |

```sh
git clone https://github.com/sentier-dev/sentier-brightway.git
cd sentier-brightway
uv sync
uv run sentier-brightway coverage
uv run sentier-brightway files --out ../bafu-baseline
```

The build includes the pinned mapping packages. Record its manifest, release, input hashes and residual coverage. It is a Sentier-derived build, not an untouched provider release. For regeneration, obtain source files through BAFU under their terms.

## Before sharing a build

The basis for redistribution of the published full inventory is still an [open question](https://github.com/sentier-dev/sentier-bafu/issues/1). Check [data and attribution](../docs/terms-of-use.md) before distributing any package. This documentation site contains coordination material and findings, not inventory downloads.

## Apply an improvement

Create isolated baseline and candidate builds. Record the layer revision, changed exchanges, expected effects and validation requirements. Start with [application and testing](../community/application-and-testing.md) and [build validation](../community/build-validation.md). A rebuild of an aggregated process has its own identity and cannot inherit a canonical-equivalence claim.
