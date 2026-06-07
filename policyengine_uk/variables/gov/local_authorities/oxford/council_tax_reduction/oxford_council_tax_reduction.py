from policyengine_uk.model_api import *
import numpy as np
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_oxford_working_age,
)


class oxford_council_tax_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Oxford Council Tax Reduction"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.oxford.council_tax_reduction
        household = benunit.household
        working_age = is_oxford_working_age(
            household("local_authority", period),
            household("country", period),
            household("council_tax_reduction_household_has_pensioner", period),
        )
        is_household_head_benunit = benunit("benunit_contains_household_head", period)
        would_claim = benunit("would_claim_council_tax_reduction", period)
        universal_credit = benunit("universal_credit", period)
        has_uc_award = universal_credit > 0

        capital = household("savings", period)
        capital_eligible = capital <= ctr.means_test.capital_limit
        weekly_tariff_income = np.ceil(
            max_(0, capital - ctr.means_test.tariff_income_threshold)
            / ctr.means_test.tariff_income_step
        )

        annual_income = benunit("council_tax_reduction_applicable_income", period)
        child_benefit = benunit("child_benefit", period)
        weekly_income = max_(0, annual_income - child_benefit) / WEEKS_IN_YEAR
        weekly_income += where(has_uc_award, 0, weekly_tariff_income)
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit",
            period,
        )
        weekly_income = where(
            relevant_income_based_benefit & ~has_uc_award, 0, weekly_income
        )

        support_rate = ctr.income_band.maximum_support_rate.calc(weekly_income)
        liability = household(
            "council_tax_reduction_maximum_eligible_liability", period
        )
        non_dep_deductions = benunit(
            "oxford_council_tax_reduction_non_dep_deductions", period
        )
        award = max_(0, liability * support_rate - non_dep_deductions)
        return (
            working_age
            * is_household_head_benunit
            * would_claim
            * capital_eligible
            * award
        )
