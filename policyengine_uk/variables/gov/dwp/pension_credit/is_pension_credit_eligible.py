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
        # State Pension Credit Act 2002 s.1(2)(b): the claimant must have
        # attained the qualifying age; s.4(1A), in force from 15 May 2019,
        # requires any partner to have attained it too. The model applies
        # s.4(1A) in every year.
        qualifying_age = benunit.members(
            "has_attained_state_pension_credit_qualifying_age", period
        )
        all_adults_have_qualifying_age = (
            benunit.sum(adult & qualifying_age) == adult_count
        )
        is_gc_eligible = benunit("is_guarantee_credit_eligible", period)
        is_sc_eligible = benunit("is_savings_credit_eligible", period)
        return (
            (adult_count > 0)
            & all_adults_have_qualifying_age
            & (is_gc_eligible | is_sc_eligible)
        )
