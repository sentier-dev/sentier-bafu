---
status: proposed
---
# Preserve independent authorisation and evidence states

Display patch execution, schema validation, community authorisation, review
decision, provider confirmation and provider adoption independently. The
community pipeline deliberately runs unauthorised patches while prominently
warning about them; retain that behavior through the initial migration.

The older contribution lifecycle cannot turn an existing `authorised_by`
statement into new reviewer consensus, or erase that authorisation because
C001/C002 have no approvals. Retain both records with their scope. The public
patch metadata records BAFU confirmation for patches 0001–0003; this updates
the older open wording without claiming a new official BAFU release.

Preserve rejected, withdrawn, superseded and unresolved findings. Change an
interpretation with a dated evidence link and explanation rather than replacing
the historical statement silently.

Review status is already recorded three ways: `Provenance` in community-fixes,
`contribution.json` here and the review records of Brightway Flows. For the
review snapshot in [#21](https://github.com/sentier-dev/sentier-bafu/issues/21),
reuse the W3C PROV record shapes Brightway Flows uses (each status an activity
with an agent and a date) rather than adding a fourth format; reuse the shape,
not the code. Existing records keep their interfaces. The schema choice is
part of #21.

Laurenz Bougan agreed with the content on 14 October 2026. It stands as
accepted once Chris Mutel confirms it in
[#18](https://github.com/sentier-dev/sentier-bafu/issues/18).
