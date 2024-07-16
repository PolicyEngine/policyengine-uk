from policyengine_uk.model_api import *


class pension_credit_guarantee_credit(Variable):
    label = "Guarantee Credit"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2002/16/section/2"
    defined_for = "is_pension_credit_guarantee_credit_eligible"

    def formula(benunit, period, parameters):
        income = benunit("pension_credit_income", period)
        minimum_guarantee = benunit("pension_credit_minimum_guarantee", period)
        return max_(0, minimum_guarantee - income)
