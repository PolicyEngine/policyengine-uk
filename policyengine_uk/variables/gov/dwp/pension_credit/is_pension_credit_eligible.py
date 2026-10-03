from policyengine_uk.model_api import *


class is_pension_credit_eligible(Variable):
    label = "Eligible for Pension Credit"
    entity = BenUnit
    definition_period = YEAR
    value_type = bool
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/2002/16/section/1",
        "https://www.legislation.gov.uk/ukpga/2002/16/section/4",
        "https://www.legislation.gov.uk/uksi/2019/37/article/4",
    )

    def formula(benunit, period, parameters):
        is_gc_eligible = benunit("is_guarantee_credit_eligible", period)
        is_sc_eligible = benunit("is_savings_credit_eligible", period)
        return benunit("meets_pension_credit_age_conditions", period) & (
            is_gc_eligible | is_sc_eligible
        )
