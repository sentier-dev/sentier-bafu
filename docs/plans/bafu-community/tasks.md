# Implementation tasks

Each task delivers a reviewable result. Dependencies describe technical prerequisites. Task IDs do not imply
priority or a schedule; Chris decides work allocation and follow-up.

| Task | Delivers | Blocked by |
|---|---|---|
| [T1 Preserve the community pipeline in an integration PR (#19)](https://github.com/sentier-dev/sentier-bafu/issues/19) | Both histories, unchanged package interfaces, fixture parity and complete file disposition | None |
| [T2 Demonstrate the strawberry correction review journey (#20)](https://github.com/sentier-dev/sentier-bafu/issues/20) | Clickable fixture-based home → correction → evidence → original issue, with distinct status dimensions | None; use pinned community source while T1 proceeds |
| [T3 Publish a versioned safe review snapshot (#21)](https://github.com/sentier-dev/sentier-bafu/issues/21) | Pipeline run → validated public metadata → deterministic Pages build, including failure and sampled-coverage states | T1 |
| [T4 Reconcile the finding ledger and partner evidence (#22)](https://github.com/sentier-dev/sentier-bafu/issues/22) | F1/F3/F11 connected to patches; C001/C002 and dissent retained; queue backed by real records | None; evidence reconciliation can proceed independently |
| [T5 Connect patched output to Sentier inventory (existing community #2)](https://github.com/sentier-dev/bafu-community-fixes/issues/2) | Existing assignment: pinned patched XML → import → checked inventory with provenance and no double application | T1; coordinate in existing community-fixes #2 |
| [T6 Extend the prototype into correction search and review (#23)](https://github.com/sentier-dev/sentier-bafu/issues/23) | Search/filter/detail/run pages driven by the safe snapshot, stable links and accessible states | T2, T3, T4 |
| [T7 Receive reusable findings into Consensus Flows (#24)](https://github.com/sentier-dev/sentier-bafu/issues/24) | One public, source-qualified reproduction → upstream module PR → release/adoption tracking; preserve remaining intake | T4; upstream releases may gate adoption separately |
| [T8 Verify cutover and retire duplicate entry points (#26)](https://github.com/sentier-dev/sentier-bafu/issues/26) | Full local release parity, inventory receiving, site checks, contributor handoff and rollback proof | T3, T4, T5, T6, T9 |
| [T9 Choose the project name (#25)](https://github.com/sentier-dev/sentier-bafu/issues/25) | Chris/Laurenz select or retain a name and record the URL cutover decision | None; does not block T1/T2 |

T5 already exists as [community-fixes #2](https://github.com/sentier-dev/bafu-community-fixes/issues/2).
Do not create a second implementation issue for it. T1 adds the concrete parity
contract to the existing [alignment assignment #1](https://github.com/sentier-dev/bafu-community-fixes/issues/1).
Close or transfer those source issues only with their owners, after receiving
the corresponding implementation; this planning package closes neither.

T7 does not block preserving or using already accepted community patches.
Likewise, provider response does not block a separately labelled candidate
experiment. Site availability must never imply acceptance of all candidates.

The [parent issue #18](https://github.com/sentier-dev/sentier-bafu/issues/18)
links these tasks with native sub-issues and dependencies. T5 stays in its source
repository; its T1 prerequisite is recorded here, while the cutover issue
depends directly on that existing source issue.
The [task briefs](task-briefs.md) explain two independently scoped deliverables.
New issues are unassigned and have no priority labels or dates; existing
source-repository assignments are unchanged.
