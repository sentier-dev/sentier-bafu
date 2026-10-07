# Optional GitHub Actions checks

The executable checks run locally with `python3 scripts/community.py check` and `python3 -m unittest discover -s community/tests`.

The supplied github-actions.yml is a template, not an enabled workflow. A maintainer with workflow write permissions can copy it to .github/workflows/community.yml to run the same checks on pushes and pull requests. Enabling it is one step for a maintainer: copy the file to `.github/workflows/community.yml` in the GitHub UI (a push from a token without the `workflow` scope is refused).
