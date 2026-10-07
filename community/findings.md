# Findings about the BAFU/UVEK data — the open ledger

A **finding** is a measured observation about a BAFU dataset or release: an amount
that cannot be right, a supplier declared with a location that is not registered,
a flow the published flow list does not carry, a dataset flagged as cumulative
that carries no flows. It is not a contribution layer (those are
[contribution records](contributions/)); a finding may *lead* to a layer, or to a
recommendation, or to nothing but a note that saves the next person a day.

Every row below was re-measured on BAFU's own release files (the ecoSpold v1
archive, the LCIA results workbook, the change log) before it was written up;
two earlier write-ups elsewhere were wrong because they measured a local
import instead. The derivations, scripts and discussion threads live on the
linked issues. Dataset values and names are quoted freely; text from the LCI
*reports* is never pasted (Terms of Use clause 4, author copyright).

## Status vocabulary

| Status | Meaning |
|---|---|
| **open** | observed and measured; not yet sent to BAFU |
| **upstream-reported** | sent to lca@bafu.admin.ch (date on the issue) |
| **upstream-fixed** | BAFU corrected it in a named release |
| **informational** | a method or scope difference, not a defect; recorded so nobody re-derives it |
| **handled-in-layer** | a contribution layer applies it in a candidate build; the upstream question stays open |
| **withdrawn** | did not survive re-measurement against BAFU's own files; kept so nobody re-finds it |

## Ledger (seeded 2026-10-07 from the lci-bafu-catalog ledger, BAFU:2025 v2 and BAFU:2026 v1)

| # | Dataset(s) | Observation | Release | Status | Derivation |
|---|---|---|---|---|---|
| F1 | 188725 (ES), 178351 (CH), 242090 (CH) strawberries, plastic tunnel | 126.22 / 18.085 / 18.079 kg `Disposal, polyethylene, 0.4% water, to municipal incineration` per kg fruit, against 0.0096 / 0.042 / 0.036 kg of polyethylene granulate entering; the tunnel film is already disposed of in the tunnel dataset (per m²·a). The LCIA workbook scores them at 383 / 55 / 55 kg CO₂-eq per kg; the heated greenhouse in the same group scores 2.6. Identical in both releases; not in the 2026 change log. | 2025 v2, 2026 v1 | open | [lci-bafu-catalog #1](https://gitlab.com/eos-lci/lci-bafu-catalog/-/issues/1) |
| F2 | 191385 Refrigerant R134a, at plant (RER) | HFC-134a 0.019, HCFC-124 0.010, CFC-113 0.010 kg per kg — each exactly 10× the corresponding ecoinvent 3.6 dataset (0.0019 / 0.001 / 0.001); GWP100 108.6 against roughly 19. A documented process difference or a unit slip? | 2025 v2, 2026 v1 | open | [#2](https://gitlab.com/eos-lci/lci-bafu-catalog/-/issues/2) |
| F3 | hard-coal supply chains + 2 others | 23 exchanges declare the supplier location `ENTSO`; no dataset is registered as ENTSO, 25 as ENTSO-E, and every one of the 23 suppliers exists as ENTSO-E. Two more exchanges declare `CH` for suppliers that exist only as GLO / RER (`Disposal, concrete, 5% water, to inert material landfill`; `Direct air capture system, sorbent-based, 100ktCO2`). An importer linking by name + location drops all 25 silently; one linking by dataset number does not. | 2026 v1 | open | [#3](https://gitlab.com/eos-lci/lci-bafu-catalog/-/issues/3) |
| F4 | whole release | **Withdrawn.** The claim that ~7.6 % of elementary exchanges were absent from the flow list was an artefact of an earlier donor-seeded import; re-measured, one flow name is absent. | — | withdrawn | [#4](https://gitlab.com/eos-lci/lci-bafu-catalog/-/issues/4) |
| F5 | flow list, all releases | The XML declares chloride to water with seven sub-compartments (ocean, river, groundwater …); the published flow list carries one `Chloride` without sub-compartment. A structure question, not a value defect. | 2026 v1 | informational | [#5](https://gitlab.com/eos-lci/lci-bafu-catalog/-/issues/5) |
| F6 | CH concrete family | `Treatment, concrete production effluent` (0.0143 m³/m³) is carried by 4 of the 63 CH concrete datasets and by none of the civil-engineering concretes. Inconsistent modelling or a scope choice? | 2026 v1 | informational | [#6](https://gitlab.com/eos-lci/lci-bafu-catalog/-/issues/6) |
| F7 | published LCIA workbook 2026 v1 | 33 rows where the ecotoxicity total differs from inorganics + organics by more than 5 % (worst 23.4 %); 110 datasets score zero in every category. | 2026 v1 | open | [#7](https://gitlab.com/eos-lci/lci-bafu-catalog/-/issues/7) |
| F8 | 138 aggregated datasets | 102 datasets are cumulative LCIs flagged ecoSpold `dataSetInformation@type=2` (no supplier links); 37 more PlasticsEurope-era eco-profiles are aggregated by structure (no supply input, > 50 elementary flows) but not flagged. Matters for every disaggregation or copied-process layer. | 2026 v1 | informational | [#11](https://gitlab.com/eos-lci/lci-bafu-catalog/-/issues/11) |
| F9 | 286952 CEM II, B-LL cement, at plant (CH) | lorry transport 4.345E-4 tkm/kg in the dataset; the cited 2020 cement/concrete report's table prints 2.00E-2 tkm for CEM II/B-LL (rail 1.50E-4 in both). Found by comparing the dataset with its report. | 2026 v1 | open | [#12](https://gitlab.com/eos-lci/lci-bafu-catalog/-/issues/12) |
| F10 | 196588 Disposal, rectangular straw bale | flagged type=2 but carries only its production exchange — a cumulative LCI with no flows; the two straw-bale siblings carry 1,656 flows each. | 2026 v1 | open | [#11](https://gitlab.com/eos-lci/lci-bafu-catalog/-/issues/11) |
| F11 | 1,289 datasets named `xx …` / `xxx …` | retired by name prefix and/or category words (`obsolete`: 803, `notMaintained`: 441, current category: 45; 57 `obsolete` datasets carry no prefix). The convention is undocumented; consumers that match by name anchor on retired datasets unknowingly. | 2026 v1 | open | [#15](https://gitlab.com/eos-lci/lci-bafu-catalog/-/issues/15) |

## How a finding moves

1. **Open an issue** with the *BAFU data finding* template: dataset code, release,
   what you measured and how, why it cannot be right, exposure if known. It gets
   `bafu-finding` + `needs-triage`.
2. **A second person re-measures** on the release files (never on an import) and
   drops `needs-triage`, or sets `withdrawn` with the reason — a withdrawn finding
   stays in the table.
3. **A row is added here** with the status and the issue link.
4. **Batches go to BAFU** (lca@bafu.admin.ch) through the recommendations tracker;
   the issue gets `upstream-reported` and the date, then `upstream-fixed` with the
   release that fixed it.

A finding that a contribution layer works around gets `handled-in-layer`; the
upstream question stays open until BAFU answers it.
