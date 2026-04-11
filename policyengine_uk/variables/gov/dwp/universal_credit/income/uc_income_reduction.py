from policyengine_uk.model_api import *


class uc_income_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "reduction from income for Universal Credit"
    definition_period = YEAR
    unit = GBP
    defined_for = "is_uc_eligible"

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.universal_credit.means_test
        earned_income = benunit("uc_earned_income", period)
        earned_income_reduction = p.reduction_rate * earned_income
        unearned_income_reduction = benunit("uc_unearned_income", period)
        maximum_credit = benunit("uc_maximum_amount", period)
        total_reduction = earned_income_reduction + unearned_income_reduction
        return min_(
            maximum_credit,
            total_reduction,
        )
