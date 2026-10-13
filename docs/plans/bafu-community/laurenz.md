# Laurenz: first two tasks and 14 October checkpoint

Existing assignment confirmed from Chris's public issues: GitHub user
**[lbougan](https://github.com/lbougan)** owns community-fixes #1 and #2.
The following two bounded tasks are assigned to Laurenz. This does not
promise availability or claim Laurenz has accepted a deadline.

## First: preserve the working pipeline

[Implementation issue #19](https://github.com/sentier-dev/sentier-bafu/issues/19).

Prepare an integration PR from the pinned community implementation, preserving
both histories and the existing package/CLI/namespace. Attach the source-file
disposition and run the public fixture on both sides. The review should show
unchanged patch order, XML and extension behavior, and explain report differences
caused only by run time, path or revision. Keep inventory wiring in the existing
community-fixes #2; do not combine it into this initial move.

## Second: make one correction easy to review

[Prototype issue #20](https://github.com/sentier-dev/sentier-bafu/issues/20).

Build a clickable prototype around **F1 / patch 0001 / dataset 188725** using
public patch metadata and explicitly identified fixture or illustrative content.
Show the observation, the correction, its evidence, the recorded community
authorisation, the recorded provider confirmation and the outstanding official
release status. Link the original issue. Keep the existing report available.
This task can start against the pinned source while the integration PR is open.

## Tomorrow, 14 October 2026

Ask for a branch/PR link, test output, a screenshot or walkthrough of the user
journey, and one clear next step or blocker. Review:

- Did T1 preserve the package and both histories? Which conflicts remain?
- Does T2 let a new user explain what changed, why, who authorised it and what
  has actually been validated? Can they reach the source discussion?
- Does either task need a decision from Chris or Manuel? Record it in the issue.
- What can begin next? Avoid assigning T3/T5 until their real prerequisites hold.

Coordinate the short exchange on Element; retain decisions and evidence in the
linked GitHub issues. The automation may inspect progress and prepare a message,
but it does not send an Element message on behalf of the team.
