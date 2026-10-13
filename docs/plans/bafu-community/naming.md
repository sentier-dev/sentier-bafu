# Naming and URL cutover

**Decision owner: Chris and Laurenz. No name selected yet.** The repository
remains `sentier-dev/sentier-bafu`.

Recommended display name: **BAFU Community**. Recommended repository:
`sentier-dev/bafu-community`.

| Option | Assessment |
|---|---|
| BAFU Community | Source-specific and broad enough for import, patches, evidence, models and review; recommended. |
| BAFU Community Fixes | Existing package remains a good name; project scope also includes findings and proposals not yet accepted as fixes. |
| BAFU Workbench | Suggests an interactive analysis product and overlaps with the existing LCI Workbench. |
| Sentier BAFU | Existing links are familiar, but the project purpose is less clear. |

Availability and admin access were checked on 13 October 2026. The rename must
retain the existing repository and issue IDs, rather than create a replacement.

## Cutover checklist

- Rename the repository only after Chris/Laurenz select and record the name; keep a receipt of the
  repository ID and old/new URLs.
- Update its description, homepage, current README, site config and local origin.
  Preserve historical evidence links where rewriting would change a pinned record.
- If renamed, deploy Pages under the selected repository name (for example,
  `https://sentier-dev.github.io/bafu-community/`); verify home,
  import, findings and the already-shared `mapping-review.html` path there.
- Check the old repository and issue redirects. Never recreate `sentier-bafu`.
- GitHub [does not redirect project Pages URLs on rename](https://docs.github.com/en/repositories/creating-and-managing-repositories/renaming-a-repository).
  Announce the new site URL and update controlled incoming links. An old Pages
  URL may stop working; do not promise a redirect that has not been installed.
- Inventory incoming links in Sentier's main site, AGRIBALYSE, community-fixes,
  importer documentation and Element messages. Update repositories through their
  maintainers; old Element posts receive a short follow-up, not silent editing.
- A custom domain is a possible later durability improvement, requiring domain
  owner participation. It is not a prerequisite for starting Laurenz's tasks.
- Preserve distribution/import/CLI names and the XML extension namespace.
- On failure, restore the old repository name and homepage, rerun Pages and
  verify the previous site. Do not delete either repository as cleanup.

The source community-fixes repository is not renamed or archived by this
cutover. Its maintainers own that transition after implementation parity.
