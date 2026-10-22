# Working on sentier-bafu

Read `CONTEXT.md` before changing domain language, and flag any conflict with
an ADR explicitly. For consolidation or review
features, read `docs/plans/bafu-community/README.md` and the relevant `docs/adr/`.

## Migration invariants

These follow ADR 0001, which is still proposed. The pinned community-fixes implementation wins conflicting implementation
choices. Preserve its history, interfaces, patch IDs, provenance and tests.
Record disagreements and superseded interpretations; preserve C001/C002 and
the original finding identifiers. Public site inputs are reviewed metadata.
Full XML, private correspondence and local run reports stay outside Pages.

Use `uv`. Keep package tests and the documentation build independently runnable.
Recheck the source revisions before beginning a migration ticket.
