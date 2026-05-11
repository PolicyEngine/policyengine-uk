from policyengine_uk.model_api import *


class forest_of_dean_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Forest of Dean Council Tax Support"
    documentation = "Forest of Dean operates a banded discount scheme with Class A (non-protected) and Class B (protected) maximum percentage tables. Paragraph 57.1 caps the working-age maximum at 90 per cent of the Band E equivalent for Class A and paragraph 57.6 raises that maximum to 95 per cent for Class B. Section 59 reduces the percentage entitlement by income band, with separate Single, Couple, Lone Parent and Couple with Children income tiers. Section 15A uses UC-assessed income and capital for UC claimants. Section 58 applies the prescribed gross-income non-dependant deduction schedule with the one-deduction couple rule. Pension-age applicants without a working-age income-related benefit go to the prescribed pensioner scheme via simulated_council_tax_reduction_benunit."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.fdean.gov.uk/media/r4ff2lok/council-tax-support-scheme-for-working-age-customers-2026-to-2027.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.forest_of_dean.council_tax_reduction
        local_scheme = benunit(
            "forest_of_dean_council_tax_reduction_is_local_scheme", period
        )
        band_rate = benunit("forest_of_dean_council_tax_reduction_band_rate", period)
        liability = benunit(
            "forest_of_dean_council_tax_reduction_maximum_eligible_liability", period
        )
        non_dep_deductions = benunit(
            "forest_of_dean_council_tax_reduction_non_dep_deductions", period
        )
        award = max_(0, liability * band_rate - non_dep_deductions)
        has_uc_award = (
            max_(
                benunit("universal_credit_pre_benefit_cap", period),
                benunit("universal_credit", period),
            )
            > 0
        )
        non_uc_capital_eligible = (
            benunit.household("savings", period) <= ctr.means_test.capital_limit
        )
        uc_capital_eligible = (
            benunit("uc_assessable_capital", period) <= ctr.means_test.capital_limit
        )
        capital_eligible = where(
            has_uc_award, uc_capital_eligible, non_uc_capital_eligible
        )
        return (
            local_scheme
            * benunit("benunit_contains_household_head", period)
            * benunit("would_claim_council_tax_reduction", period)
            * capital_eligible
            * award
        )
