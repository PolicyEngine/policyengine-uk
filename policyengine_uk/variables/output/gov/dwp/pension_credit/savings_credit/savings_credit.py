from policyengine_uk.model_api import *


class savings_credit(Variable):
    label = "Savings Credit"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2002/16/section/3"

    def formula(benunit, period, parameters):
        income = benunit("savings_credit_income", period)
        sc = parameters(period).gov.dwp.pension_credit.savings_credit
        relation_type = benunit("relation_type", period)
        threshold = sc.threshold[relation_type] * WEEKS_IN_YEAR
        minimum_guarantee = benunit("minimum_guarantee", period)
        income_over_threshold = max_(income - threshold, 0)
        income_over_mg = max_(income - minimum_guarantee, 0)
        maximum_savings_credit = sc.rate.phase_in * (
            minimum_guarantee - threshold
        )
        phased_in_sc = min_(
            maximum_savings_credit, sc.rate.phase_in * income_over_threshold
        )
        sc_reduction = sc.rate.phase_out * income_over_mg
        eligible = benunit("is_savings_credit_eligible", period)
        return max_(0, phased_in_sc - sc_reduction) * eligible
