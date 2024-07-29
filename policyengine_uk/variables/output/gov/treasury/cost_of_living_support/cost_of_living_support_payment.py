from policyengine_uk.model_api import *


class cost_of_living_support_payment(Variable):
    label = "Cost-of-living support payment"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        col = parameters(period).gov.treasury.cost_of_living_support
        on_means_tested_benefits = (
            add(
                household,
                period,
                col.means_tested_households.qualifying_benefits,
            )
            > 0
        )
        means_test_bonus = (
            col.means_tested_households.amount * on_means_tested_benefits
        )

        on_pensioner_benefits = (
            add(household, period, col.pensioners.qualifying_benefits) > 0
        )
        pensioner_bonus = col.pensioners.amount * on_pensioner_benefits

        on_disability_benefits = (
            add(household, period, col.disabled.qualifying_benefits) > 0
        )
        disabled_bonus = col.disabled.amount * on_disability_benefits

        return means_test_bonus + pensioner_bonus + disabled_bonus
