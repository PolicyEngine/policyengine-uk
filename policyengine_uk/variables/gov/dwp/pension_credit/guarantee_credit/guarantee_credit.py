from policyengine_uk.model_api import *


class guarantee_credit(Variable):
    label = "Guarantee Credit"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2002/16/section/2"

    def formula(benunit, period, parameters):
        income = benunit("pension_credit_income", period)
        minimum_guarantee = benunit("minimum_guarantee", period)
        eligible = benunit("is_guarantee_credit_eligible", period)
        return max_(0, minimum_guarantee - income) * eligible
