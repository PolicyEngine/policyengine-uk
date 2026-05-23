from policyengine_uk.model_api import *


class is_pension_credit_eligible(Variable):
    label = "Eligible for Pension Credit"
    entity = BenUnit
    definition_period = YEAR
    value_type = bool
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2002/16/section/1"

    def formula(benunit, period, parameters):
        adult = benunit.members("is_adult", period)
        adult_count = benunit.sum(adult)
        all_adults_are_sp_age = (
            benunit.sum(adult & benunit.members("is_SP_age", period)) == adult_count
        )
        is_gc_eligible = benunit("is_guarantee_credit_eligible", period)
        is_sc_eligible = benunit("is_savings_credit_eligible", period)
        return (
            (adult_count > 0)
            & all_adults_are_sp_age
            & (is_gc_eligible | is_sc_eligible)
        )
