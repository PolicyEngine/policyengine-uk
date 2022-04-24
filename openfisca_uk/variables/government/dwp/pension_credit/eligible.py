from openfisca_uk.model_api import *


class pension_credit_eligible(Variable):
    label = "Eligible for Pension Credit"
    entity = BenUnit
    definition_period = YEAR
    value_type = bool
    unit = "currency-GBP"
    reference = "https://www.legislation.gov.uk/ukpga/2002/16/section/1"

    def formula_2002(benunit, period, parameters):
        has_sp_age_member = benunit.any(benunit.members("is_SP_age", period))
        is_gc_eligible = benunit("guarantee_credit_eligible", period)
        is_sc_eligible = benunit("savings_credit_eligible", period)
        return has_sp_age_member & (is_gc_eligible | is_sc_eligible)
