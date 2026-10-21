# UX investigation and proposed experience

Inspected on 13 October 2026: the live [Brightway Flows home](https://flows.brightway.dev/),
[decision queues](https://flows.brightway.dev/queue/),
[changes](https://flows.brightway.dev/changes),
[flow-object detail](https://flows.brightway.dev/flow-objects/fo-130030e87e592b4c),
[run](https://flows.brightway.dev/run/), the current BAFU site, and a freshly
generated community-fixes report from its public fixture. Source inspection
covered routing, templates, report records and the patch registry at the pinned
revisions. This is a design investigation, not a completed accessibility audit
or evidence from user interviews.

## What to transfer

| Observed reference pattern | BAFU experience | Deliberate adaptation |
|---|---|---|
| Direct lookup and concrete examples on the home page | Search a dataset number, name, finding or patch; start with strawberries, supplier locations and maintenance | Dataset and correction are the primary objects; chemistry stays linked to Brightway Flows |
| Stable detail pages with identity first | Release + dataset number, source/candidate distinction, patch IDs and related findings before technical details | Do not imply a source dataset is a consensus elementary flow |
| Changes filtered by step/field, with before, after and reason | Patch detail shows rationale, scope, bounded before/after examples and linked run | Clearly mark samples; distinguish unavailable from unchanged |
| Decision queues distinguish blocking/review/info | Queue by next action: needs reproduction, patch review, missing evidence, provider response | Execution severity and scientific judgement remain distinct; a warning is not automatically bad data |
| A named run and build metrics | Run page identifies input fingerprint, revision, options, validation scope and omissions | Public summary generated from allowlisted fields; full local reports remain local by default |
| Flow/source correspondence and provenance | Source observation links to upstream flow and correction decision | Display exact/close/broad relationship without inventing conversion certainty |
| Progressive disclosure, documentation and deep links | A readable conclusion first, then evidence, history, XML example and implementation link | Keep all evidence reachable with keyboard and stable anchors |
| Shared shell, plain typography, status text and theme controls | Consistent navigation and semantic states using established Sentier/DDS assets | No Brightway trademark copied; no new Sentier logo; theme switching can follow core usability |

## Gaps in today's BAFU site

The home page explains a process but does not let a user find a dataset or patch.
Findings live in a long Markdown table; contribution cards lead to raw JSON.
Patch execution, provider response and contribution review are not connected in
one journey. Counts of accepted contributions do not describe authorised patches.
The community report already solves much of the before/after explanation, but
is a single-run document rather than a cross-run discussion space.

## Information architecture

Primary navigation: **Use the data · Corrections · Findings · Review · About**.

- **Use the data:** select a named release, understand raw versus patched output,
  run CLI/TUI, inspect a run and find the Sentier importer integration.
- **Corrections:** list import fixes separately from patches; filter by release,
  category and recorded authorisation; open a stable patch detail.
- **Findings:** search/filter existing IDs, dataset numbers and terms; unresolved,
  withdrawn and scenario records remain first-class results.
- **Review:** actionable work queue, required evidence, objections and revision
  history; GitHub is the discussion and contribution destination.
- **About:** scope, roles, provenance, terms, contribution guide and upstream
  relationship. No implied official BAFU endorsement.

Candidate routes: `corrections.html`, `patches/0001-strawberry-polyethylene-disposal.html`,
`findings.html#F1`, `runs/<id>.html`, `review.html`. Keep existing `import.html`,
`testing.html`, `mapping-review.html`, `hackathon.html`, `consensus.html` and
`terms.html` working as routes or documented aliases within the new site base.

## First user journeys

1. **Data user:** home → choose release → CLI/TUI instructions → run summary →
   changed dataset/example → evidence. They can tell whether a result is a
   fixture, a local run, a community candidate or an official provider release.
2. **Partner:** search dataset 188725 or F1 → read the observation and correction
   → see patch 0001's recorded BAFU confirmation → inspect its selected run →
   open the original issue. Confirmation and adoption are separately visible.
3. **Reviewer:** queue → unresolved finding → source and candidate comparison →
   evidence gaps/objections → GitHub review tied to the candidate revision.
   Updating that revision makes old approval visibly stale.
4. **Maintainer:** run fails or is cancelled → report with diagnostic scope →
   affected step → issue. A failed run never appears as an accepted release.
5. **Flow curator:** BAFU observation → pinned Brightway Flows decision → scoped
   reproduction and upstream PR → verified containing release → consumer check.

## Page contract for a correction

Title and one-sentence reason; patch ID and release scope; recorded author,
reporter, authoriser and provider confirmer; expected inputs and changed fields;
before/after example with units and dataset identity; affected count with its
run denominator; schema and scientific check results; related finding and
upstream links; history and next action. Empty data says **not recorded**.
Only show **unchanged** when the selected run actually checked it.

## Interaction and visual acceptance

- Search state is shareable; clear empty/error/stale-snapshot states and reset.
- Core navigation and evidence work without JavaScript. Search can progressively
  enhance a bounded public index; no full inventory is downloaded to the browser.
- Check 360px and desktop layouts, keyboard order, visible focus, semantic
  headings/tables and contrast; status has words as well as colour.
- Keep units beside values, long identifiers copyable, tables horizontally
  contained, and verbose XML/history expandable. Do not collapse the reason.
- Use real fixture facts or explicitly marked illustrative data in previews.
  Record screenshots and one short walkthrough of each first journey.
- The first prototype should demonstrate one complete correction journey. It
  need not reproduce the entire upstream application or its chemical taxonomy.

## Technical structure

Retain the community pipeline's `Database`, patch registry and `RunLog` as the
execution interfaces. Add a publication module with one versioned review-snapshot
interface containing safe run summaries, patch catalogue, finding references
and evidence/review links. Both the static site and integration checks consume
that same interface. The existing report continues consuming RunLog directly.

Validate at snapshot creation, then render deterministic static output from one
snapshot generation. GitHub supplies discussion state through explicit imports
with their retrieval date; a build failure retains the last complete snapshot.
No new backend, login system or second decision engine is needed for the first
release. Full XML and personal/contact fields are outside the public contract.
