# Apply and test BAFU/UVEK contribution layers

## Pin and retain the baseline

Use a named provider release and pin the public importer, inventory, methods and mappings. Save the sentier-brightway manifest and input hashes. Keep the baseline export and data root immutable. A baseline using Sentier mappings already contains those mappings; a candidate tests an additional change against that precise build.

## Existing hackathon candidate

The copied-process toolkit is in [sentier-models PR 2](https://github.com/sentier-dev/sentier-models/pull/2). Its implementation remains there; this repository retains the evidence, reproducible experiment and review. Pin the reviewed commit rather than treating an open PR as an accepted release:

```sh
mkdir -p .local
git clone https://github.com/sentier-dev/sentier-models.git .local/hackathon
git -C .local/hackathon fetch origin pull/2/head
git -C .local/hackathon checkout --detach a8c895d37b1ce5027733306eb95d60bb389cb31e
uv venv .local/toolkit-env
uv pip install --python .local/toolkit-env/bin/python -r .local/hackathon/hackathon/bafu-copied-processes/requirements.txt
.local/toolkit-env/bin/python .local/hackathon/hackathon/bafu-copied-processes/src/full_run.py --data-root ../sentier-inventory
```

Pin the inventory checkout to the contribution's baseline revision. The script reports failure counts but can still exit zero; inspect the content-round-trip failure count explicitly. This check covers the toolkit's selected families and columns with its stated numeric tolerance. It is not a full-inventory or LCIA parity claim.

For application testing, follow the toolkit's validate/rebuild_inventory.py and compare_multi.py instructions using a **copy** of the baseline data root. Export baseline and reconstructed candidate to separate paths with sentier-brightway; compare stock bw2calc scores across agreed products and methods. Never rebuild the canonical data root in place. Keep the baseline inventory pin aligned with the exported baseline; the installer's pinned cache can differ from the current inventory checkout.

Forecasting is a different layer from lossless representation: test held-out products and locations, unit compatibility and physically meaningful share constraints; do not claim forecast outputs are source observations or mass-balanced merely because all inputs share a unit.

## Other contributions

Use existing importer plugins and ordered mapping packages. Pin their precedence, unit conversions, chemical identity and context, retain unresolved flows, and record intentional output changes. Keep source-inventory corrections distinct from representation, importer and mapping changes.

Record run summaries using community/templates/run-summary.json, compare equivalent summaries with scripts/community.py, then attach checks and public evidence to the contribution record. Numerical differences alone do not establish improvement.
