# sentier-bafu

A public workspace for **BAFU/UVEK import, application, contributor improvements and validation**. Gather partner and hackathon evidence, develop reproducible contributions on top of a pinned canonical import, compare results, build reviewed consensus, and return actionable recommendations to the BAFU project team.

## Canonical import and use

The provider's BAFU/UVEK release is the source of truth. [sentier-importers](https://github.com/sentier-dev/sentier-importers) owns source parsing; [sentier-inventory](https://github.com/sentier-dev/sentier-inventory), [sentier-methods](https://github.com/sentier-dev/sentier-methods) and [sentier-mappings](https://github.com/sentier-dev/sentier-mappings) own the derived public artifacts. [sentier-brightway](https://github.com/sentier-dev/sentier-brightway) builds the pinned application baseline. This workspace connects those components and contribution layers rather than duplicating their importers.

```sh
git clone https://github.com/sentier-dev/sentier-brightway.git
cd sentier-brightway
uv sync
uv run sentier-brightway coverage
uv run sentier-brightway files --out ../bafu-baseline
```

Record manifest pins, source release, inputs and coverage. The resulting Sentier build includes its pinned mappings; it is not an untouched vendor import. Treat improvements as candidate layers with separate builds. Obtain raw source exports under their provider's terms for regeneration.

## Contribute, apply, test, review

Start at [the community workspace](community/README.md), [application and testing](community/application-and-testing.md), [the hackathon assessment](community/hackathon-assessment.md), [public evidence](evidence/index.md), and [contribution records](community/contributions/). No private repository is required to collaborate. Dataset releases are recorded explicitly; the repository spans releases.

```sh
python3 scripts/community.py check
python3 -m unittest discover -s community/tests
```

The first candidate is the BAFU copied-process toolkit from the Brightcon hackathon, pinned to its open PR. It is under review, not an accepted replacement for the canonical representation. Forecasts, lossless compression and upstream inventory corrections need distinct validation and claims.

Consensus and provider responses are tracked alongside contributions. No new partner agreement or sent recommendation is assumed. Original code and documentation: MIT; source datasets retain their own terms and citations. Keep restricted exports and confidential notes local.
