from policyengine_uk.model_api import *


class is_uc_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Eligible for the Universal Credit"
    documentation = "Whether this family is eligible for Universal Credit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        capital = benunit("uc_assessable_capital", period)
        limit = parameters(period).gov.dwp.universal_credit.means_test.capital.limit
        # Welfare Reform Act 2012 s.4(1)(b) and (4): a claimant must not have
        # reached the qualifying age for State Pension Credit; one member of a
        # couple under it suffices (Universal Credit Regulations 2013 reg
        # 3(2)(a)).
        adult = benunit.members("is_adult", period)
        qualifying_age = benunit.members(
            "has_attained_state_pension_credit_qualifying_age", period
        )
        has_working_age_adult = benunit.any(adult & ~qualifying_age)
        return has_working_age_adult & (capital <= limit)
