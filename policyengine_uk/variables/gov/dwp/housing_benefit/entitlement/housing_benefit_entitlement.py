from policyengine_uk.model_api import *


class housing_benefit_entitlement(Variable):
    label = "Housing Benefit entitlement"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(benunit, period, parameters):
        rent = benunit("benunit_rent", period)
        applicable_amount = benunit(
            "housing_benefit_applicable_amount", period
        )
        income = benunit("housing_benefit_applicable_income", period)
        withdrawal_rate = parameters(
            period
        ).gov.dwp.housing_benefit.means_test.withdrawal_rate
        reduced_income = max_(0, income - applicable_amount)
        final_amount = max_(0, rent - reduced_income * withdrawal_rate)
        capped_final_amount = min_(final_amount, benunit("LHA_cap", period))
        lha_eligible = benunit("LHA_eligible", period.this_year)
        amount = where(lha_eligible, capped_final_amount, final_amount)
        return max_(
            0, amount - benunit("housing_benefit_non_dep_deductions", period)
        )
