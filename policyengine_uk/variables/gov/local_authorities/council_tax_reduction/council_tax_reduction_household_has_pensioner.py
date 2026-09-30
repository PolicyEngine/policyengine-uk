from policyengine_uk.model_api import *


class council_tax_reduction_household_has_pensioner(Variable):
    value_type = bool
    entity = Household
    label = "CTR claimant benefit unit has a pension-age member"
    definition_period = YEAR

    def formula(household, period, parameters):
        person = household.members
        claimant_benunit = person.benunit("benunit_contains_household_head", period)
        # A "pensioner" has attained the qualifying age for State Pension
        # Credit: SI 2012/2885 reg 3(1)(a) (England), SI 2013/3029 reg 3(1)(a)
        # (Wales), and SSI 2012/319 reg 12(1) (Scotland).
        qualifying_age = person(
            "has_attained_state_pension_credit_qualifying_age", period
        )
        return household.any(claimant_benunit & qualifying_age)
