from policyengine_uk.model_api import *


class guarantee_credit(Variable):
    label = "Guarantee Credit"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/2002/16/section/1",
        "https://www.legislation.gov.uk/ukpga/2002/16/section/2",
    )
    documentation = (
        "The guarantee credit element of State Pension Credit. It is part of "
        "State Pension Credit, so it is zero unless the benefit unit meets "
        "the Pension Credit entitlement conditions, including the shared "
        "qualifying-age conditions and any preserved mixed-age-couple saving; "
        "other schemes that passport "
        "on Guarantee Credit read this variable."
    )
    defined_for = "is_pension_credit_eligible"

    def formula(benunit, period, parameters):
        income = benunit("pension_credit_income", period)
        minimum_guarantee = benunit("minimum_guarantee", period)
        eligible = benunit("is_guarantee_credit_eligible", period)
        return max_(0, minimum_guarantee - income) * eligible
