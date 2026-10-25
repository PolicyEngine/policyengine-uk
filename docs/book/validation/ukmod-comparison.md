# Comparing PolicyEngine UK and UKMOD

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
modified OECD scale, with an adult couple normalised to one (§4.2, printed
pages 95–96). Footnote 42 gives 0.66 for the first adult, 0.34 for each additional
member aged 14 or over, and 0.20 for each child under 14. Those reported
coefficients differ from PolicyEngine's stored BHC values at the displayed
precision. UKMOD's executable precision and AHC scale were not verified for this
comparison. Check classifications and normalisation as well as the coefficients
before treating results as comparable; the labels “OECD” and “UK” alone do not
describe the distinction.

## Random assignment and imputation

A reproducibility comparison needs a named operation. Values supplied in an
input dataset and assignments made during a simulation can have different
randomness and override rules.

For example, PolicyEngine's [UC-deduction assignment fallback](uc-deductions.md#where-the-assignment-lives)
uses deterministic SplitMix64 draws based on benefit-unit identifiers. Datasets
or situations can override its draw inputs. This describes that fallback, not
every PolicyEngine imputation or the complete dataset-building pipeline.

UKMOD's report describes two benefit take-up extensions (§2.3, printed page 30).
BTA allocates take-up randomly among eligible tax units. BTO prioritises observed
recipients, then allocates randomly among the remainder. BTO defaults on and BTA
off; turning both off implies full take-up. These are take-up settings, rather
than a counterpart to PolicyEngine's UC-deduction assignment. The cited report
sections do not establish a generator or seed comparison between the models.

Record the variable or imputation stage, entity identifiers, seed or stream,
override rules, and take-up switches when comparing reproducibility. The presence
of random allocation alone does not show that either model is less reproducible.

## Comparing outputs

Before comparing estimates, record both model versions, input datasets and
weights, population and geography, policy year, income definition, housing-cost
basis, equivalisation, and take-up or imputation settings. A difference in a
documented convention does not quantify its effect on poverty or reform results.

The [indirect-tax effects plan](../policy/indirect-tax-effects-plan.md) discusses
a separate UKMOD comparison topic; its proposals remain labelled as a plan.
