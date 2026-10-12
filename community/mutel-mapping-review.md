# Review of Chris Mutel's BAFU → openLCA mapping

Reviewed 12 October 2026. Chris Mutel's mapping version **1.0.0** targets
**BAFU 2026 v1 → openLCA LCIA Methods 2.8.2**. This is a candidate contribution
[C002](contributions/C002.json). The review establishes consistency between its
two file formats. Independent inventory and LCIA reproduction, reviewer approval
and provider approval remain open.

## Sources and what was checked

Chris's three reports were reviewed through the links he supplied. Their titles and subjects are:

- BAFU Flow Matching 2026: flow matching and coverage.
- BAFU Scores with openLCA Factors: LCIA score comparison.
- Elementary-flow-list proposal: staged source corrections and adoption.

The JSON supplied for review declares Chris as author and **CC BY 4.0**.
The accompanying workbook also names him as author; it has no separate licence
declaration. Their names and SHA-256 hashes are recorded in the
[aggregate audit](runs/mutel-mapping-audit.json). Original attachments,
correspondence, workbook factor values and full report copies are kept outside
this public repository. Public implementation findings are cited below. A stable public download and scoring-run manifest are
still needed for independent reproduction.

The read-only [audit script](../scripts/audit_flow_mapping.py) checked all source
keys, target UUIDs/names/contexts/units, comments, matching rules, conversion
factors and ordered fallback UUIDs between the two formats. It also checks the
stated unit multipliers. It never edits the workbook or runs an LCA.

| Independently checked file property | Result |
|---|---:|
| Workbook source identities: name, category, subcategory, unit | 2,679 unique |
| JSON mappings / mapped workbook rows | 2,434 / 2,434 |
| Unmatched workbook rows | 245 |
| Target, rule, conversion, comment and ordered-fallback disagreements | 0 |
| Workbook elementary-exchange counts, mapped / total | 272,666 / 293,747 |
| Exchange-weighted coverage calculated from those counts | 92.8234% |
| Explicit conversion multipliers | 161 |
| JSON rows with factor fallbacks | 134 |
| Workbook category-specific fallback rows | 536, all EF 3.1 Method (adapted) |

The exchange counts come from the workbook; this review has **not** re-counted
the source XML. A high mapping coverage does not establish CF coverage or score
parity. This candidate's openLCA target differs from Sentier's existing EF 3.1
crosswalk, so their coverage percentages cannot rank mapping quality.

## Findings and review actions

| ID | Finding / evidence | Action before application |
|---|---|---|
| M1 | Unit conversion is part of the mapping contract. The attachment contains 158 Bq→kBq multipliers of 0.001, two km→m multipliers of 1,000 and one kWh→MJ multiplier of 3.6. Public [Brightway Flows #382](https://github.com/brightway-labs/brightway-flows/issues/382) reports lookup paths that omit multipliers. | Test amounts through the actual consumer. Keep conversion of inventory amounts separate from CF denominator conversion and functional-unit conversion. The Nm3→m3 alias assumes normal conditions, as stated by the workbook. |
| M2 | The workbook specifies 536 EF-specific fallback applications. The 134 JSON fallback descriptors preserve order but carry no method/category applicability field. | Consume these with an explicit method/category policy. Prefer a present direct CF, including an explicit zero; use only the first permitted fallback with a factor. Do not sum fallbacks or use a missing factor as zero. |
| M3 | Element→ion and oxidation-state decisions are method-dependent. Public [#379](https://github.com/brightway-labs/brightway-flows/issues/379) limits its factor-equivalence evidence; [#380](https://github.com/brightway-labs/brightway-flows/issues/380) documents name/CAS conflicts. | Preserve chemical identities and label score-fitted decisions. Test Cr/As alternatives and other methods separately. Agreement with EF 3.1 does not establish an equivalence for ReCiPe or USEtox. |
| M4 | CAS notation, omitted CAS values and name preparation affect lookup. Public [#375](https://github.com/brightway-labs/brightway-flows/issues/375), [#376](https://github.com/brightway-labs/brightway-flows/issues/376) and [#377](https://github.com/brightway-labs/brightway-flows/issues/377) give concrete cases. [#381](https://github.com/brightway-labs/brightway-flows/issues/381) shows a source-label/context interaction. | Preserve the raw identity, normalisation rules, conflicting CAS values, lookup flags and Brightway Flows build. Add these cases to consumer regression checks. |
| M5 | Import compatibility, mapping and LCIA reproduction are distinct checks. The supplied repair example predates BAFU 2026 and performs metadata transformations as well as schema repair. | Obtain a release-specific repair revision, a before/after repair ledger and semantic checks for amounts, signs, units, reference exchanges and provider links. Preserve the original archive and hashes. |
| M6 | Water-use, toxicity tails and method-version differences remain unresolved in the author-reported validation. | Retain the exceptions in comparisons and recommendations. Compare equivalent methods and regions, rather than inferring success from a median close to one. |

These are mapping/integration findings. They are recorded separately from the
[source-data ledger](findings.md), whose measured defect rows require a second
measurement against BAFU's release files.

## What the score report establishes, and what it does not

Chris reports comparisons for **11,894 processes** using a matrix containing
**11,947 datasets**. His reported IPCC agreement is 99.07%, and 19 of 25 EF
categories meet the stated threshold of at least 95% of processes agreeing.
However, the workbook's threshold combines a 0.5% relative criterion with an
absolute tolerance of 10⁻⁶ times the category median. It is not a pure relative
tolerance. These are author-reported results, not a new run by Sentier.

The retained exceptions matter: water use reports 28.85% within tolerance and a
median ratio of 1.00964. Freshwater ecotoxicity and non-cancer toxicity have
substantial tails despite near-unity medians. Ecological Scarcity 2021 is not
compared with the pack's 2013 method. These figures are also recorded in the
workbook's `Validation` sheet (A2:G27), identified by its audit hash.

The workbook states that regionalised CFs are excluded and INPUT-directed
categories give output flows a negative sign. Its fallback sheet records raw
pack values before that sign. Independent reproduction needs the exact category,
direction, region, CF units, functional-unit conversion and zero-score policy.
GreenDelta's [2.8.2 release notes](https://www.openlca.org/openlca-lcia-method-package-2-8-2-update-release/)
distinguish water use from adapted spatialisation.

Before accepting score parity, request the source/archive, LCIA package,
reference-workbook and scoring-code hashes; runnable preparation/scoring code;
the selection explaining the 53 unscored datasets; and the exact definitions
behind the exploratory 3,158-flow report versus the final 2,679-row workbook.
Use a held-out validation set for decisions selected by fitting BAFU's scores.

## Provider-facing work to develop through review

Chris's elementary-flow-list proposal suggests a
staged route: correct documented identities at source, publish a versioned
crosswalk, resolve water/accounting/speciation questions, then consider adopting
shared flow identifiers with migrations and legacy synonyms. Each stage can
have its own evidence and review; adoption and an official Brightway release
require provider decisions.

The immediate contribution is to reproduce the pinned candidate, test the
exceptions above and collect independent review in C002. No consensus,
upstream recommendation delivery or official-release approval is recorded here.

## Reproduce the file audit

Obtain the author's exact two files locally, then run:

```sh
uv run --no-project --with openpyxl==3.1.5 scripts/audit_flow_mapping.py \
  /path/to/mapping.randonneur.json /path/to/mapping.xlsx \
  --out /path/to/aggregate-audit.json
```

The output is a file-consistency receipt. The separate requirements for
[build validation](build-validation.md), [candidate application](application-and-testing.md)
and [reviewer approval](workflow.md) still apply.
