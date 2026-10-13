# Migration inventory and conflict decisions

The user selected community-fixes as authoritative on conflicts. Preserve its
executable behavior first, then add capabilities in separately reviewed changes.
The machine-readable [inventory](source-inventory.json) hashes all **64 + 52**
tracked source files. Only `.gitignore`, `LICENSE` and `README.md` overlap;
the two MIT licence files are already byte-identical.

## Move every category deliberately

| Existing material | Destination and treatment | Acceptance |
|---|---|---|
| Community package, strict models, XML reader/writer, registry, download/cache | Keep the original package tree and Python ≥3.14 requirement at the consolidated root | Every original file accounted for; public interfaces unchanged |
| 14 ordered import fixes | Preserve IDs, order, rules, placeholders, provenance and conventions | Same fixture outputs; missing-data handling remains disclosed |
| Patches 0001–0010 | Preserve IDs, decorators, rationale, attribution, selection and fail-fast expectations | Existing tests pass; no renamed or silently rewritten patch |
| 53 Brightway corrections, 26 exclusions, crosswalk, rebuild script | Keep pinned source identities, checksums, aliases and permission notice together | Same data hashes; exclusions remain visible; scoped permission portability confirmed before publication |
| Report, embedded font/logo, TUI and styles | Keep the existing offline report and terminal workflow | CLI/TUI smoke tests; failure/cancellation report still works |
| XSDs and bundled licences | Keep unchanged alongside package resources | Package installation includes schemas and notices |
| Community lockfile, packaging and CI | Preserve package environment; retain site CI as a separate job | Locked package test job and public-only Pages job both pass |
| Findings F1–F11, including withdrawals and aggregation list | Retain IDs, source evidence and old interpretations; add dated reconciliation | No lost finding; 37 structural candidates not conflated with 22 rebuilt datasets |
| C001 copied-process/forecast contribution | Keep the separate scenario and its original validation gaps | Never promoted to an ordinary source correction by this migration |
| C002 mapping/method work and receipts | Preserve historical file checks and method-specific gaps | Crosswalk identity links are not described as tested LCIA integration |
| Existing scripts, tests and CI examples | Keep until a named replacement passes equivalent external checks | Delete only with a documented successor and parity evidence |
| Issue discussions, attachments, branches, tags and releases | Snapshot an inventory at execution; preserve links and authors; transfer issues only with source-repo authority | No invented authorship or recreated comments pretending to be originals |
| Site routes, evidence index, recommendations tracker | Retain content and stable page filenames while introducing the new navigation | Link check; historical links and delivery states remain intelligible |

## Resolve semantic conflicts

| Conflict | Decision |
|---|---|
| Old F1/F3/F11 wording says open; patches 0001–0003 record BAFU confirmation on 12 October | Use the community metadata as the current source, cite that record and preserve the earlier text as history. Confirmation is not proof of provider adoption. No private email is republished. |
| Old entry point starts directly with Sentier importers | Document provider source → community preparation and selected patches → Sentier import. Keep a separately identified raw baseline and stop duplicate corrections. |
| Old layer classes suggest import normalisation is purely mechanical | Preserve each community import fix's own `Rule.schema` flag and rationale; placeholder, truncation and CAS conventions remain visible. Do not reclassify solely by stage. |
| Existing approval model vs `authorised_by`/`confirmed_by` | Keep distinct status dimensions and original evidence. Do not backfill a synthetic reviewer approval. |
| Brightway Flows proposes immutable changes; community patches mutate validated models | Preserve the community patch interface. Transfer audit concepts, not a replacement execution engine. |
| Pipeline links to a flow vs downstream quantity conversion | Preserve original name/context/unit and the corrected alias; link strength does not supply a conversion factor. No implicit factor one for unknown conversions. |
| Community report shows samples; reference site has a complete change log | Label sampled coverage. A complete per-dataset history needs a complete change export before the UI may promise one. |
| Site DDS/Nunito styling vs report Sentier/Rubik styling | Keep the community report intact during parity migration. Design a shared navigation and semantic status language; retain established marks and credits. Review any later token unification as a visible change. |

## Execution procedure

1. Refresh both heads and enumerate all refs, open PRs, releases and issues.
   At the planning baseline, community-fixes has two commits, only `main`, no
   PRs, and two open issues assigned to Laurenz. Recheck this before merging.
2. Record the cutover SHA with the community maintainers. Fetch both histories
   into an isolated integration branch; merge with unrelated histories allowed.
   Preserve the community commit as an ancestor; do not squash it into an
   unattributed file copy. Keep upstream remote names unambiguous.
3. Merge the ignore rules, retain the identical MIT licence, and compose the
   README with the community usage guide as authoritative. Preserve the original
   community README verbatim under migration history with its source SHA.
4. Verify every inventoried source file. Any changed file gets a reason and a
   parity result. Keep both existing suites and separate Python environments for
   the package and current site until CI is deliberately unified.
5. Compare fixture XML semantically and byte-for-byte where deterministic;
   compare patch order, change counts, extension fields and report content after
   excluding timestamps, output paths and source-revision differences. Run a
   licensed full-release comparison locally before any release adoption.
6. Reconcile F1/F3/F11, C001/C002 and existing issue links with dated evidence.
   Have the source maintainer transfer or cross-link the two existing issues.
   Do not close them merely because a planning issue was created here.
7. Land only after parity review. Keep the old repo available until active work,
   issue custody and contributor guidance have moved. Archival is a later
   maintainer decision; this plan does not create an empty archive or delete it.

Rollback: leave published provider and consumer releases untouched until a
candidate is accepted. Revert the integration merge or select the previous
package/source pin; preserve run receipts and migration issue links. Repository
renaming and pipeline adoption are independently reversible actions.
