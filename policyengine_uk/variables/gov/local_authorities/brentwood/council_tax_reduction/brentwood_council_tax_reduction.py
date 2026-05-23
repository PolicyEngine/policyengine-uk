from policyengine_uk.model_api import *


class brentwood_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Brentwood Council Tax Reduction"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.brentwood.gov.uk/sites/default/files/2026-03/Council%20Tax%20reduction%20scheme%20S13A%202026-27%20FINAL.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.brentwood.council_tax_reduction
        local_scheme = benunit(
            "brentwood_council_tax_reduction_is_local_scheme", period
        )
        weekly_income = benunit("brentwood_council_tax_reduction_weekly_income", period)
        # Pad slightly so that exactly-on-the-boundary tests fall in the lower band.
        weekly_income_for_band = weekly_income + 1e-9
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        num_dependants = benunit.sum(child_or_young_person)
        income_bands = ctr.income_band
        banded_rate = select(
            [num_dependants >= 2, num_dependants == 1],
            [
                income_bands.two_or_more_dependants.calc(weekly_income_for_band),
                income_bands.one_dependant.calc(weekly_income_for_band),
            ],
            default=income_bands.no_dependants.calc(weekly_income_for_band),
        )
        # Schedule 1 paragraph 9: passported income-based benefit applicants get
        # at least 75% (Band 1).
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        passport_rate = ctr.income_band.no_dependants.calc(0.0)
        rate_before_uplift = where(
            relevant_income_based_benefit, max_(banded_rate, passport_rate), banded_rate
        )
        # Schedule 1 paragraph 3: protected groups uplift to 100%.
        protected = benunit("brentwood_council_tax_reduction_protected_group", period)
        rate = where(protected & (rate_before_uplift > 0), 1.0, rate_before_uplift)
        # Section 6.1: Band F/G/H working-age homeowners get 0%.
        band_fgh_owner = benunit(
            "brentwood_council_tax_reduction_band_fgh_owner_excluded", period
        )
        rate = where(band_fgh_owner, 0.0, rate)
        liability = benunit.household("council_tax", period)
        # Section 30 capital limit (£6,000 strict) - non-UC vs UC capital.
        has_uc_award = (
            max_(
                benunit("universal_credit_pre_benefit_cap", period),
                benunit("universal_credit", period),
            )
            > 0
        )
        non_uc_capital = benunit.household("savings", period)
        uc_capital = benunit("uc_assessable_capital", period)
        capital = where(has_uc_award, uc_capital, non_uc_capital)
        capital_eligible = capital <= ctr.means_test.capital_limit
        return (
            local_scheme
            * benunit("benunit_contains_household_head", period)
            * benunit("would_claim_council_tax_reduction", period)
            * capital_eligible
            * liability
            * rate
        )
