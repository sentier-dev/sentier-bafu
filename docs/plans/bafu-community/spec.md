# BAFU Community specification

## Problem statement

Partner findings and discussion live in one repository while the working BAFU
correction pipeline lives in another. Users cannot readily connect a dataset,
a correction, its measured result and the review that justifies using it.
Consolidation must preserve prior work and give contributors a clear path.

## Solution

One source-specific project combines the authoritative community pipeline with
the retained findings and a review site inspired by Consensus Flows. Users can
reproduce a run, inspect corrections, contribute evidence and trace decisions
back to their original sources and forward to upstream adoption.

## User stories

1. As a data user, I can choose a named provider release and see its fingerprint.
2. As a data user, I can distinguish raw, prepared and community-patched output.
3. As a data user, I can continue using the existing CLI and terminal app.
4. As a data user, I can select patches and see precisely which selection ran.
5. As a data user, I can inspect failed and cancelled runs without mistaking them for releases.
6. As a contributor, I can find an existing issue by dataset, finding or patch ID.
7. As a contributor, I can follow an observation to the patch and its evidence.
8. As a contributor, I can see earlier rejected or withdrawn interpretations.
9. As a reviewer, I can distinguish schema compliance from scientific validation.
10. As a reviewer, I can identify sampled detail and missing evidence.
11. As a reviewer, I can record objections and decisions against a precise revision.
12. As a reviewer, I can distinguish community authorisation from BAFU confirmation.
13. As a provider, I can receive a concise recommendation with a reproducible case.
14. As a provider, I can respond without that response being mistaken for a shipped correction.
15. As a flow curator, I can reuse source-qualified upstream flow decisions.
16. As a flow curator, I can submit a reusable correction to the owning upstream module.
17. As an importer maintainer, I can consume a pinned patched output without applying changes twice.
18. As an importer maintainer, I can preserve quantities, uncertainty, source identity and extension provenance.
19. As a maintainer, I can account for every migrated file, commit and discussion.
20. As a maintainer, I can revert to the previous accepted release and its evidence.
21. As a reader on a phone or keyboard, I can complete the same evidence journey.
22. As a returning contributor, I can find the renamed project and understand old links.

## Implementation decisions

Preserve the community execution interfaces and package identifiers. Consolidate
with both Git histories. Add a versioned public review-snapshot interface and a
static presentation layer. Preserve one source observation alongside corrected
aliases. Model execution, validation, authorisation, review, confirmation and
adoption as independent states. Keep upstream elementary-flow decisions central.
The static publication architecture is proposed for maintainer review; it does
not gate a fixture-based UX prototype.

## Testing decisions

Test externally observable behavior at the pipeline-to-output and
snapshot-to-pages interfaces. Existing community fixture, report, XML/XSD and
TUI tests provide the baseline; existing site and contribution checks remain.
Migration compares the same input on both revisions, retaining intentional
metadata differences. Add failures for missing/invalid provenance, stale
approvals, unknown factors, duplicate patch application and accidental public
payload exposure. Verify the first user journeys on desktop, narrow screens and
keyboard. A full locally licensed release comparison is required for adoption;
fixture success cannot stand in for it.

## Out of scope

No new matching engine, blanket acceptance of historical hypotheses, public
raw-data mirror, new provider endorsement, full LCIA migration, or completed
reconstruction of the 37 aggregated candidates. The wider LCI Workbench
Consensus Flows rollout continues separately; its private 53-entry review is
an intake source, not a public dataset to copy wholesale.

## Further notes

Repository rename is separate from package and namespace compatibility.
Existing community-fixes issues #1 and #2 remain authoritative assignments.
Tomorrow's checkpoint assesses progress and blockers, not completion of this
entire specification.
