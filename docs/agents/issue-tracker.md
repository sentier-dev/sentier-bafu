# Issue tracker: GitHub

Use `gh` against this repository's origin. Issues are the task and spec surface;
pull requests implement them. **PRs as a request surface: no.**

Read an issue and its comments before changing or duplicating its scope. Write
multiline descriptions to a file and pass `--body-file`. Preserve existing
discussions, identifiers and attribution when consolidating another repository.

Use a parent issue with native sub-issues. For blocking edges, use the GitHub
issue-dependencies endpoint with the blocker's numeric database ID; also put
the dependencies in the issue body. If an endpoint is unavailable, record the
limitation and retain the explicit linked dependencies.

The frontier consists of tasks with no open blockers. Assign only authorized
work; assignment does not constitute scientific reviewer approval. Existing
community-fixes issues #1 and #2 retain their ownership until their maintainers
explicitly transfer them. Link them rather than creating competing work queues.
