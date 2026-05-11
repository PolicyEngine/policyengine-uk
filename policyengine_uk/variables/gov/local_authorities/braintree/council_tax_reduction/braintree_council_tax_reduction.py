from policyengine_uk.model_api import *


class braintree_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Braintree Council Tax Reduction"
    documentation = "Braintree operates a Banded Discount Scheme with a 77 per cent maximum (paragraph 48.1). Schedule 1 paragraph 1 sets the entitlement percentage from a household-type table varying by Single / Couple x no / one / two-or-more children household composition and weekly income range. Schedule 1 paragraph 5 / paragraph 26.1 exclude applicants whose capital is 10,000 pounds or greater. Schedule 1 paragraph 7 places passported Income Support, income-related ESA or income-based JSA applicants in Band 1 (77 per cent). The working-age scheme has no Band cap and no non-dependant deductions; pension-age applicants follow the prescribed pensioner scheme except where the scheme treats a pension-age Universal Credit or working-age income-related-benefit case as not being a pensioner."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.braintree.gov.uk/downloads/file/4374/council-tax-reduction-scheme-2026-27"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.braintree.council_tax_reduction
        local_scheme = benunit(
            "braintree_council_tax_reduction_is_local_scheme", period
        )
        rate = benunit("braintree_council_tax_reduction_band_rate", period)
        liability = benunit.household("council_tax", period)
        # Section 26.1 / Schedule 1 paragraph 5: "10,000 or greater" strict cutoff,
        # using DWP-assessed UC capital for UC awards (paragraph 12.5).
        has_uc_award = (
            max_(
                benunit("universal_credit_pre_benefit_cap", period),
                benunit("universal_credit", period),
            )
            > 0
        )
        capital = where(
            has_uc_award,
            benunit("uc_assessable_capital", period),
            benunit.household("savings", period),
        )
        capital_eligible = capital < ctr.means_test.capital_limit
        return (
            local_scheme
            * benunit("benunit_contains_household_head", period)
            * benunit("would_claim_council_tax_reduction", period)
            * capital_eligible
            * liability
            * rate
        )
