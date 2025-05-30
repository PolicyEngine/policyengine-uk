from policyengine_uk.model_api import *


class nhs_budget_change(Variable):
    label = "NHS budget change"
    entity = Household
    definition_period = YEAR
    value_type = float

    def formula(household, period, parameters):
        budget_increase = (
            parameters(period).gov.contrib.policyengine.budget.nhs * 1e9
        )
        if budget_increase == 0:
            return 0
        decile = household(
            "pre_budget_change_ons_household_income_decile", period
        )
        weight = household("household_weight", period)
        DECILE_INCIDENCE = {
            1: 0.095,
            2: 0.118,
            3: 0.126,
            4: 0.117,
            5: 0.104,
            6: 0.104,
            7: 0.092,
            8: 0.089,
            9: 0.085,
            10: 0.07,
        }

        decile = pd.Series(decile)

        budget_increase_per_decile = {
            i: budget_increase * DECILE_INCIDENCE[i] for i in range(1, 11)
        }
        if household.simulation.dataset is not None:
            households_per_decile = (
                pd.Series(weight).groupby(decile).sum().to_dict()
            )
        else:
            households_per_decile = {i: 28e5 for i in range(1, 11)}

        average_per_decile = {
            i: budget_increase_per_decile[i] / households_per_decile[i]
            for i in range(1, 11)
        }

        return decile.map(average_per_decile).replace({np.nan: 0})
