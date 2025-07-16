from policyengine_uk.model_api import *


class cost_of_living_support_payment(Variable):
    label = "Cost-of-living support payment"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        p = parameters(period).gov.treasury.cost_of_living_support
        on_means_tested_benefits = (
            add(
                household,
                period,
                p.means_tested_households.qualifying_benefits,
            )
            > 0
        )
        means_test_bonus = (
            p.means_tested_households.amount * on_means_tested_benefits
        )

        on_pensioner_benefits = (
            add(household, period, p.pensioners.qualifying_benefits) > 0
        )
        pensioner_bonus = p.pensioners.amount * on_pensioner_benefits

        on_disability_benefits = (
            add(household, period, p.disabled.qualifying_benefits) > 0
        )
        disabled_bonus = p.disabled.amount * on_disability_benefits

        return means_test_bonus + pensioner_bonus + disabled_bonus
