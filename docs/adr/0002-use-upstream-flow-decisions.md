---
status: accepted
---
# Keep elementary-flow decisions in Consensus Flows

The community pipeline already consumes pinned Brightway Flows corrections
and a crosswalk. Keep that as the common identity authority and contribute
reusable elementary-flow corrections upstream. BAFU-specific inventory patches
stay here; consumer method policy stays with its consumer. A second local
identity matcher would recreate the disagreements this work is meant to resolve.

Preserve original and corrected source tuples, upstream revision, correspondence
strength and evidence. Quantity conversion, direction and method factors remain
separate claims: patch 0010 adds identity links and does not convert amounts.
The 53 included corrections and 26 exclusions in the pinned community data
remain intact until a reviewed upstream refresh changes them.

Local triangulation knowledge is migrated as evidence and reproductions, then
focused module PRs. It becomes active behavior only through a verified containing
release and consumer validation. Unknown conversions stay unknown.
