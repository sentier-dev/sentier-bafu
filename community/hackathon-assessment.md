# Brightcon copied-process contribution assessment

Assessed 7 October 2026. Source: [sentier-models PR 2](https://github.com/sentier-dev/sentier-models/pull/2), commit `a8c895d37b1ce5027733306eb95d60bb389cb31e`. The PR remains open. [The original review](https://github.com/sentier-dev/sentier-models/pull/1#issuecomment-5811114747) requested preserving exchange geography and limiting inappropriate mixed-unit constraints.

## Reproduced locally

With inventory commit `c5aee155f0778f02e68a67fc766e23222a11686a`, full_run.py tested **766 families**, reported **zero content-round-trip failures**, and reconstructed **129,687 exchange rows**. The compact representation used **25,732 structure rows** (19.84% of the original exchange-row count) and 129,687 value rows. That ratio measures repeated structure rows, not total file-size compression.

The checker compares flow identity, names, flow types, direction, units and exchange locations exactly as strings. Numeric columns use numpy.allclose with rtol=1e-9 and default atol=1e-8, including NaN equality. The loader excludes 99-obsolete. This supports the revised toolkit's tested structural round-trip claim on this scope, not bit-exact identity for every inventory column.

The contribution description's broader 787-family count is not the scope reproduced by this command. Confirm the classification and release scope with its author before repeating that number.

## Still unverified

- Full reconstructed-export score parity against the same pinned baseline.
- Held-out forecasting performance and applicability of normalization constraints.
- Coverage of columns outside the toolkit's explicit checks and obsolete-sector handling.
- Partner approvals and any agreed recommendation to BAFU.

The result is attached to C001 as partial validation. C001 remains proposed. The next recommendation should distinguish a useful compact representation from a source-dataset correction and from a forecasting extension.
