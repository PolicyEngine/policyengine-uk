from policyengine_uk.model_api import *


class housing_benefit_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "eligible for the Housing Benefit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        social = benunit.any(benunit.members("in_social_housing", period))
        already_claiming = add(benunit, period, ["housing_benefit_reported"]) > 0
        claiming_uc = benunit("would_claim_uc", period)
        lha_eligible = benunit("LHA_eligible", period)
        any_over_SP_age = benunit.any(benunit.members("is_SP_age", period))
        capital = benunit("housing_benefit_assessable_capital", period)
        hb_capital = parameters(period).gov.dwp.housing_benefit.means_test.capital
        limit = where(
            any_over_SP_age,
            hb_capital.pension_age.limit,
            hb_capital.working_age.limit,
        )
        return (
            already_claiming
            & (social | lha_eligible)
            & ~claiming_uc
            & (capital <= limit)
        )
