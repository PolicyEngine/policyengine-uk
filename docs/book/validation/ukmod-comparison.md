# Comparing PolicyEngine UK and UKMOD

UKMOD is a UK tax-benefit model that uses the EUROMOD platform.
This page compares documented methods in PolicyEngine UK 2.158.1
([source revision](https://github.com/PolicyEngine/policyengine-uk/tree/eb0b8087d821b92d4faa75cf51a92d15aa2a3c45))
and the January 2025 [UKMOD country report, CeMPA WP 2/25](https://www.iser.essex.ac.uk/wp-content/uploads/files/working-papers/cempa/cempa2-25.pdf),
which describes UKMOD B2024.21. It does not report a matched numerical comparison.

## Equivalisation and housing costs

PolicyEngine uses HBAI modified OECD equivalisation for both before-housing-costs
(BHC) and after-housing-costs (AHC) income. Its stored coefficients are:

| Household member | BHC | AHC |
| --- | ---: | ---: |
| First adult | 0.67 | 0.58 |
| Each other adult | 0.33 | 0.42 |
| Each dependent child aged 14 or over | 0.33 | 0.42 |
| Each dependent child under 14 | 0.20 | 0.20 |

These values come from the
[equivalence-scale parameters](https://github.com/PolicyEngine/policyengine-uk/tree/eb0b8087d821b92d4faa75cf51a92d15aa2a3c45/policyengine_uk/parameters/household/demographic/equiv).
The formulas use HBAI adult and dependent-child classifications. See
[HBAI income concepts](hbai.md) for the income and housing-cost components.

The UKMOD report's distributional analysis also uses HBAI BHC income and a
modified OECD scale, with an adult couple normalised to one
([section 4.2, printed pages 95-96](https://www.iser.essex.ac.uk/wp-content/uploads/files/working-papers/cempa/cempa2-25.pdf#page=96)).
Footnote 42 gives 0.66 for the first adult, 0.34 for each additional member
aged 14 or over, and 0.20 for each child under 14. Both descriptions use the
modified OECD scale family and couple normalisation. For example, dividing
weights (1, 0.5, 0.3) by a couple's total of 1.5 gives (2/3, 1/3, 0.2),
which round to (0.67, 0.33, 0.20). The report instead prints (0.66, 0.34, 0.20);
its first two values also sum to one, but they are not those nearest-two-decimal
roundings. This does not establish equality of the models' executable coefficients.
UKMOD's stored values have not been checked. The cited BHC sections give no AHC
coefficients, and a UKMOD AHC scale has not been checked for this comparison.

Additional adults and children aged 14 or over have equal weights within each
displayed BHC scale: 0.33 in PolicyEngine and 0.34 in the UKMOD report. They
also share PolicyEngine's AHC weight of 0.42. Those labels do not explain the
printed BHC difference; the age bands and housing-cost basis still need to
match in an output comparison.

## Benefit take-up and policy transitions

PolicyEngine's `would_claim_uc`, `would_claim_pc` and
`would_claim_child_benefit` are benefit-unit inputs that default to true when
not supplied. Its [take-up documentation at the pinned revision](https://github.com/PolicyEngine/policyengine-uk/blob/eb0b8087d821b92d4faa75cf51a92d15aa2a3c45/docs/book/assumptions/takeup-analysis-plan.md)
describes draws made in the data build, with reported recipients anchored as
claimants. Eligibility and the claim flag are separate conditions for payment.
This comparison has not audited those data-build stages, their generators,
seeds, stream ordering or exported flags.

Other take-up flags have default formulas in the country model.
`would_claim_CTC`, `would_claim_WTC`, `would_claim_IS`,
`would_claim_housing_benefit` and `would_claim_council_tax_reduction` follow
reported receipt on data-built simulations. Income Support counts the claimant's
or partner's report. Hand-entered situations also consult the per-benefit-unit
`claims_all_entitled_benefits` flag. The pinned take-up documentation describes
these runtime rules separately from the stochastic input flags.

UKMOD's report describes Benefit Take-up Adjustment (BTA) and Benefit Take-up
Adjustment Observed (BTO)
([section 2.3, printed page 30](https://www.iser.essex.ac.uk/wp-content/uploads/files/working-papers/cempa/cempa2-25.pdf#page=31)).
BTA allocates take-up randomly among eligible tax units. BTO prioritises observed
recipients, then allocates randomly among the remainder. BTO defaults on and BTA
off; turning both off implies full take-up. Section 3.2.3
([printed page 77](https://www.iser.essex.ac.uk/wp-content/uploads/files/working-papers/cempa/cempa2-25.pdf#page=78))
says that each benefit's take-up probabilities are applied at household level,
so entitled people within a household share take-up behaviour. These two unit
descriptions need to be reconciled before mapping UKMOD take-up to PolicyEngine
benefit units. Reported-receipt anchoring provides a closer comparison topic than
PolicyEngine's separate UC-deduction assignment.

For the UC roll-out, the report describes random allocation between Universal
Credit and legacy benefits using DWP estimates and OBR forecasts
([section 2.5, printed page 63](https://www.iser.essex.ac.uk/wp-content/uploads/files/working-papers/cempa/cempa2-25.pdf#page=64)).
Table 2.3 names `random_uk` for policy transitions
([printed page 26](https://www.iser.essex.ac.uk/wp-content/uploads/files/working-papers/cempa/cempa2-25.pdf#page=27)).
A related PolicyEngine input is `would_claim_uc_at_legacy_closure`.
The model combines it with `legacy_benefits_closed` to determine
`claims_uc_at_legacy_closure`, then combines that result with `would_claim_uc`
for the UC claim. The pinned take-up documentation describes a Microcosm draw
by legacy-benefit combination and says the Enhanced FRS leaves this input at its
true default. A claim at legacy closure and a random UC roll-out allocation
cover related stages; this comparison does not establish identical transition
rules or random streams.

## Other random assignment and reproducibility

PolicyEngine's [UC-deduction assignment fallback](uc-deductions.md#where-the-assignment-lives)
uses deterministic SplitMix64 draws based on benefit-unit identifiers. Datasets
or situations can override its draw inputs. This describes that fallback, not
every PolicyEngine imputation or the complete dataset-building pipeline.

A reproducibility comparison needs the named stage, model and dataset versions,
entity identifiers, seed or stream, override rules and take-up switches. The cited
report sections and pinned country-model documentation do not establish a
generator or seed comparison between the models. Random allocation alone does
not show that either model is less reproducible.

## Comparing outputs

Before comparing estimates, record both model versions, input datasets and
weights, population and geography, policy year, income definition, housing-cost
basis, equivalisation, and take-up or imputation settings. A difference in a
documented convention does not quantify its effect on poverty or reform results.

The [indirect-tax effects plan](../policy/indirect-tax-effects-plan.md) discusses
a separate UKMOD comparison topic; its proposals remain labelled as a plan.
