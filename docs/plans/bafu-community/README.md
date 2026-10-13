# Consolidate BAFU Community

Planning baseline: **13 October 2026**. Project names are proposals for Chris
and Laurenz; the repository remains `sentier-dev/sentier-bafu`. This is the implementation plan; it does
not claim that the repositories, datasets or review workflows have already
been merged.

Track implementation in [the parent issue #18](https://github.com/sentier-dev/sentier-bafu/issues/18).
The implementation issues include [pipeline preservation #19](https://github.com/sentier-dev/sentier-bafu/issues/19)
and [the strawberry review prototype #20](https://github.com/sentier-dev/sentier-bafu/issues/20).
Chris and Laurenz can record the naming decision in [#25](https://github.com/sentier-dev/sentier-bafu/issues/25).

The goal is one place to run community corrections, inspect exactly what they
do, review partner evidence and return useful recommendations to BAFU and
Consensus Flows. Preserve the working community pipeline and bring the existing
Sentier evidence and discussions around it.

## Read in this order

1. [Migration inventory and conflict decisions](migration.md).
2. [UX investigation and proposed user journeys](ux-review.md).
3. [Product and validation specification](spec.md).
4. [Tasks and technical dependencies](tasks.md).
5. [Implementation task briefs](task-briefs.md).
6. [Naming and URL cutover](naming.md).

The [ADRs](../../adr/) record repository ownership, flow identity, publication,
review states and naming. [CONTEXT.md](../../../CONTEXT.md) defines the language.
The [source inventory](source-inventory.json) accounts for every tracked file
in both pinned repositories.

## What the investigation established

| Source | Pinned revision | Verified scope |
|---|---|---|
| [Community fixes](https://github.com/sentier-dev/bafu-community-fixes/tree/15bbfbb66c5e8bd864623d61a1169402838eaed8) | `15bbfbb66c5e8bd864623d61a1169402838eaed8` | 64 tracked files; 14 import fixes, 10 patches; CLI, TUI, report, models, XSD and tests |
| [Existing workspace](https://github.com/sentier-dev/sentier-bafu/tree/87d14af) | See full commit in source inventory | 52 tracked files; findings F1–F11, C001/C002, evidence, checks and public site |
| [Brightway Flows](https://github.com/brightway-labs/brightway-flows/tree/19d6cc6268e59e18fcbb47bfec0f440fb0f6a353) | `19d6cc6268e59e18fcbb47bfec0f440fb0f6a353` | Current upstream source; live home, queue, changes, flow detail and run pages inspected |

Community baseline: **91 tests passed, 1 skipped** in 11.35 seconds using the
locked environment. The skipped test requires the full provider archive. A
strict CLI run on the public fixture produced valid XML and a report covering
one dataset, three exchanges, fourteen import fixes and ten patches. These
results establish a fixture baseline, not full-release parity or LCIA accuracy.

## Completion means

- Both histories and all source assets are accounted for; community behavior
  is preserved and conflicts have an explicit disposition.
- A user can choose a release, run the existing tools, inspect an identified
  correction and its evidence, and find the relevant discussion.
- Public pages clearly distinguish executed patches, validation scope,
  authorisation, community review and provider adoption.
- Sentier inventory consumes a pinned patched output with demonstrated quantity
  and identity preservation; repeat processing cannot silently apply it twice.
- Knowledge and unresolved cases survive; reusable flow findings have an
  upstream issue/PR and a verified release path.

The issues describe scope, acceptance evidence and technical dependencies.
They carry no priority, deadline or new assignment. Chris decides how to
coordinate work and whether to follow up with Laurenz.
