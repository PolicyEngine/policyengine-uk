from policyengine_uk.model_api import *


class bath_and_north_east_somerset_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Bath and North East Somerset Council Tax Reduction"
    definition_period = YEAR
    unit = GBP
    reference = [
        "https://www.bathnes.gov.uk/apply-council-tax-support",
        "https://www.bathnes.gov.uk/sites/default/files/2026-01/Council_Tax_reduction_scheme_April_1_2026_to_March_31_2027.pdf",
    ]

    def formula(benunit, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.bath_and_north_east_somerset.council_tax_reduction
        local_scheme = benunit(
            "bath_and_north_east_somerset_council_tax_reduction_is_local_scheme",
            period,
        )
        has_uc_award = (
            max_(
                benunit("universal_credit_pre_benefit_cap", period),
                benunit("universal_credit", period),
            )
            > 0
        )
        support_rate = benunit(
            "bath_and_north_east_somerset_council_tax_reduction_support_rate",
            period,
        )
        liability = where(
            has_uc_award,
            benunit.household("council_tax", period),
            benunit.household(
                "bath_and_north_east_somerset_council_tax_reduction_maximum_eligible_liability",
                period,
            ),
        )
        non_uc_award = liability * support_rate - benunit(
            "bath_and_north_east_somerset_council_tax_reduction_excess_income_reduction",
            period,
        )
        uc_award = liability * support_rate
        award = max_(0, where(has_uc_award, uc_award, non_uc_award))
        ordinary_capital_limit = ctr.means_test.capital_limit
        protected_capital_limit = ctr.means_test.protected_capital_limit
        protected = benunit(
            "bath_and_north_east_somerset_council_tax_reduction_protected_group",
            period,
        )
        non_uc_capital_limit = where(
            protected, protected_capital_limit, ordinary_capital_limit
        )
        non_uc_capital_eligible = (
            benunit.household("savings", period) <= non_uc_capital_limit
        )
        uc_capital_eligible = (
            benunit("uc_assessable_capital", period) <= ctr.means_test.uc_capital_limit
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
