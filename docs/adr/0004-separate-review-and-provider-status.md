---
status: accepted
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
