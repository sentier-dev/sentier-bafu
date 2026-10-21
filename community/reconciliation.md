# Reconciliation receipt: findings and community patches, 21 October 2026

This receipt accounts for every finding (F1–F16) and contribution (C001, C002)
against the public metadata of the
[bafu-community-fixes](https://github.com/sentier-dev/bafu-community-fixes)
patches at revision `053c799`. The records themselves are in
[reconciliation.json](reconciliation.json); `scripts/community.py check` keeps them
consistent with the [findings ledger](findings.md). It delivers
[#22](https://github.com/sentier-dev/sentier-bafu/issues/22).

Provider responses are cited as the patches record them ("Marine Manche, BAFU
(email, 12 October 2026)"); no correspondence is reproduced. A provider
confirmation is not a provider adoption: no finding is `upstream-fixed`,
because no official BAFU release containing a correction has been verified.

## Updated

| Finding | Before | After | Why |
|---|---|---|---|
| F1 strawberries | open | handled-in-layer | Patch 0001 applies the amounts BAFU gave; BAFU confirmed and announced a correction for its next release. |
| F3 supplier locations | open | handled-in-layer | Patch 0002 uses the suppliers' locations for the 25 exchanges; BAFU confirmed and announced a correction. |
| F8 aggregated datasets | informational | handled-in-layer | Patch 0011 flags 40 datasets type 2; all 37 structural candidates are among them (UUID membership checked). Changed in PR #33. |
| F11 retired datasets | open | handled-in-layer | Patch 0003 flags the 1,289 prefixed datasets; BAFU explained the convention and announced a "not maintained" category. The 57 unprefixed obsolete datasets are not flagged. |

## Preserved unchanged

- **Open, awaiting BAFU:** F2 (R134a, ×10), F7 (LCIA workbook totals),
  F9 (CEM II lorry transport), F10 (straw bale without flows; not covered by
  patch 0011 because it is already type 2), F13–F16 (re-measured on
  21 October 2026; see #28–#31).
- **Informational:** F5 (chloride sub-compartments), F6 (concrete effluent),
  F12 (elementary flows in two units).
- **Withdrawn:** F4, kept so nobody re-finds it.
- **Contributions:** C001 and C002 stay `proposed` with their recorded gaps.
  C001 is a separate scenario; C002's passed checks are file checks only, and
  flow correspondence does not demonstrate LCIA integration.
- **Counts kept distinct:** the 37 structural aggregated candidates (F8) and
  the 22 the hackathon reports rebuilt describe different stages.

## Still unresolved

Every record that is not withdrawn names a next action, a review role and an
evidence link in [reconciliation.json](reconciliation.json). In short:

| Next action | Role | Records |
|---|---|---|
| Verify the correction in the next BAFU release, then retire the patch | maintainer | F1, F3, F11 |
| Send to BAFU with the next batch | maintainer | F2, F6, F8, F9, F10, F13, F14, F15, F16 |
| Recompute from an independent score run | reviewer | F7 |
| Check the flow crosswalk | flow curator | F5 |
| Importer parity or pinned LCIA package | importer maintainer | F12, C002 |
| Run the missing checks | reviewer | C001 |

## Patches without a finding

Patches 0004–0010 carry Brightway Flows corrections and links. No
sentier-bafu finding corresponds to them, and they are listed as such, so all
eleven patches are accounted for.

## What this does not establish

It does not verify that any patch reproduces BAFU's intended values, that a
pipeline run applied them (no run record is pinned here), or that reviewers
reached consensus: those fields stay empty until evidence exists.
