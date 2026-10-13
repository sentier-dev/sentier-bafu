# Implementation task briefs

These two independently scoped issues make the migration and UX work concrete.
They have no assigned priority, deadline or owner. Chris decides how to involve
Laurenz and whether to follow up. Existing assignments in community-fixes
remain unchanged.

## Preserve the working pipeline

[Implementation issue #19](https://github.com/sentier-dev/sentier-bafu/issues/19).

Prepare an integration PR from the pinned community implementation, preserving
both histories and the existing package/CLI/namespace. Attach the source-file
disposition and run the public fixture on both sides. The review should show
unchanged patch order, XML and extension behavior, and explain report differences
caused only by run time, path or revision. Keep inventory wiring in the existing
community-fixes #2; do not combine it into this initial move.

## Make one correction easy to review

[Prototype issue #20](https://github.com/sentier-dev/sentier-bafu/issues/20).

Build a clickable prototype around **F1 / patch 0001 / dataset 188725** using
public patch metadata and explicitly identified fixture or illustrative content.
Show the observation, the correction, its evidence, the recorded community
authorisation, the recorded provider confirmation and the outstanding official
release status. Link the original issue. Keep the existing report available.
This task can start against the pinned source while the integration PR is open.

Implementation PRs should carry the branch, relevant checks and a walkthrough
where useful. Element can point contributors to the issues; durable decisions
and evidence belong in those issues and PRs.
