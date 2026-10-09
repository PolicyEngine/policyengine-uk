from policyengine_uk.model_api import *


class is_guarantee_credit_eligible(Variable):
    label = "Guarantee Credit eligible"
    entity = BenUnit
    definition_period = YEAR
    value_type = bool
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/2002/16/section/2",
        "https://www.legislation.gov.uk/nia/2002/14/section/2",
    )

    def formula(benunit, period, parameters):
        income = benunit("pension_credit_income", period)
        minimum_guarantee = benunit("minimum_guarantee", period)
        return income <= minimum_guarantee
