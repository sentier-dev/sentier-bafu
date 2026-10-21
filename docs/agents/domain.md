# Domain docs

The glossary is `CONTEXT.md`; decisions are in `docs/adr/`.

## Use the glossary's vocabulary

When your output names a domain concept (in an issue title, a proposal, a
hypothesis, a test name), use the term as defined in `CONTEXT.md`. Don't drift
to synonyms the glossary explicitly avoids. If the concept you need isn't in the
glossary yet, either the language is new to the project (reconsider) or there is
a real gap (add the term in the same change).

## Flag ADR conflicts

If your output contradicts an existing ADR, say so explicitly rather than
silently overriding it:

> _Contradicts ADR-0002 (elementary-flow decisions in Brightway Flows), but
> worth reopening because…_
