from policyengine_uk.model_api import *


class other_public_spending_budget_change(Variable):
    label = "non- budget change"
    entity = Household
    definition_period = YEAR
    value_type = float

    def formula(household, period, parameters):
        budget_increase = (
            parameters(
                period
            ).gov.contrib.policyengine.budget.other_public_spending
            * 1e9
        )
        if budget_increase == 0:
            return 0
        decile = household(
            "pre_budget_change_ons_household_income_decile", period
        )
        weight = household("household_weight", period)
        DECILE_INCIDENCE = {
            1: 0.114,
            2: 0.146,
            3: 0.122,
            4: 0.125,
            5: 0.119,
            6: 0.085,
            7: 0.088,
            8: 0.076,
            9: 0.077,
            10: 0.046,
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
