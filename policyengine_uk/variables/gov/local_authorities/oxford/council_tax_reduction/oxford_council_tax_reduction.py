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
        local_authority = benunit.household("local_authority", period)
        country = benunit.household("country", period)
        has_pensioner = benunit.household(
            "council_tax_reduction_household_has_pensioner", period
        )
        working_age = is_oxford_working_age(local_authority, country, has_pensioner)
        is_household_head_benunit = benunit("benunit_contains_household_head", period)
        would_claim = benunit("would_claim_council_tax_reduction", period)
        capital_eligible = (
            benunit.household("savings", period) <= ctr.means_test.capital_limit
        )
        weekly_income = benunit("council_tax_reduction_applicable_income", period) / 52
        capital = benunit.household("savings", period)
        has_uc = benunit("universal_credit", period) > 0
        weekly_tariff_income = np.ceil(
            max_(0, capital - ctr.means_test.tariff_income_threshold)
            / ctr.means_test.tariff_income_step
        )
        weekly_income += where(has_uc, 0, weekly_tariff_income)
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit",
            period,
        )
        weekly_income = where(relevant_income_based_benefit, 0, weekly_income)
        support_rate = ctr.income_band.maximum_support_rate.calc(weekly_income)
        liability = benunit.household("council_tax", period)
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
