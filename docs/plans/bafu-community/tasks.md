# Implementation tasks

Each task delivers a reviewable result. Dependencies describe execution gates,
not a reason to stop independent design or evidence work.

| Task | Delivers | Blocked by | Initial owner |
|---|---|---|---|
| T1 Preserve the community pipeline in an integration PR | Both histories, unchanged package interfaces, fixture parity and complete file disposition | None | Laurenz; extends community-fixes #1 |
| T2 Demonstrate the strawberry correction review journey | Clickable fixture-based home → correction → evidence → original issue, with distinct status dimensions | None; use pinned community source while T1 proceeds | Laurenz |
| T3 Publish a versioned safe review snapshot | Pipeline run → validated public metadata → deterministic Pages build, including failure and sampled-coverage states | T1 | Unassigned |
| T4 Reconcile the finding ledger and partner evidence | F1/F3/F11 connected to patches; C001/C002 and dissent retained; queue backed by real records | None; evidence reconciliation can proceed independently | Unassigned |
| T5 Connect patched output to Sentier inventory | Existing assignment: pinned patched XML → import → checked inventory with provenance and no double application | T1; coordinate in existing community-fixes #2 | Laurenz's existing assignment |
| T6 Extend the prototype into correction search and review | Search/filter/detail/run pages driven by the safe snapshot, stable links and accessible states | T2, T3, T4 | Unassigned |
| T7 Receive reusable findings into Consensus Flows | One public, source-qualified reproduction → upstream module PR → release/adoption tracking; preserve remaining intake | T4; upstream releases may gate adoption separately | Unassigned |
| T8 Verify cutover and retire duplicate entry points | Full local release parity, inventory receiving, site checks, contributor handoff and rollback proof | T3, T4, T5, T6, T9 | Maintainers |
| T9 Choose the project name | Chris/Laurenz select or retain a name and record the URL cutover decision | None; does not block T1/T2 | Chris and Laurenz |

T5 already exists as [community-fixes #2](https://github.com/sentier-dev/bafu-community-fixes/issues/2).
Do not create a second implementation issue for it. T1 adds the concrete parity
contract to the existing [alignment assignment #1](https://github.com/sentier-dev/bafu-community-fixes/issues/1).
Close or transfer those source issues only with their owners, after receiving
the corresponding implementation; this planning package closes neither.

T7 does not block preserving or using already accepted community patches.
Likewise, provider response does not block a separately labelled candidate
experiment. Site availability must never imply acceptance of all candidates.

The parent GitHub issue links the published task IDs and native dependencies.
Laurenz’s initial frontier is **T1 + T2**; T4 can also start independently; [tomorrow's checklist](laurenz.md) defines
the evidence to bring back rather than an assumed completion percentage.
