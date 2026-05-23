from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_barnet_working_age,
)


class barnet_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Barnet Council Tax Support"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.barnet.council_tax_reduction
        local_authority = benunit.household("local_authority", period)
        country = benunit.household("country", period)
        has_pensioner = benunit.household(
            "council_tax_reduction_household_has_pensioner", period
        )
        working_age = is_barnet_working_age(local_authority, country, has_pensioner)
        monthly_earnings = benunit(
            "barnet_council_tax_reduction_monthly_earnings", period
        )
        support_rate = ctr.income_band.maximum_support_rate.calc(monthly_earnings)
        liability = benunit.household(
            "barnet_council_tax_reduction_maximum_eligible_liability", period
        )
        non_dep_deductions = benunit(
            "barnet_council_tax_reduction_non_dep_deductions", period
        )
        ordinary_award = max_(0, liability * support_rate - non_dep_deductions)
        protected = benunit("barnet_council_tax_reduction_protected_group", period)
        protected_liability = benunit.household("council_tax", period)
        pensioners_ctr = parameters(
            period
        ).gov.local_authorities.england.council_tax_reduction.pensioners
        applicable_amount = benunit("council_tax_reduction_applicable_amount", period)
        applicable_income = benunit("council_tax_reduction_applicable_income", period)
        protected_award = max_(
            0,
            protected_liability
            - max_(0, applicable_income - applicable_amount)
            * pensioners_ctr.means_test.withdrawal_rate
            - non_dep_deductions,
        )
        award = where(protected, protected_award, ordinary_award)
        capital_eligible = (
            benunit.household("savings", period) <= ctr.means_test.capital_limit
        )
        return (
            working_age
            * benunit("benunit_contains_household_head", period)
            * benunit("would_claim_council_tax_reduction", period)
            * capital_eligible
            * award
        )
