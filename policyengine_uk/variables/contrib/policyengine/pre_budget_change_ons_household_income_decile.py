from policyengine_uk.model_api import *


class pre_budget_change_ons_household_income_decile(Variable):
    label = "pre-budget change household income decile (ONS matched)"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        income = household("pre_budget_change_household_net_income", period)
        equivalisation = household("household_equivalisation_bhc", period)
        if household.simulation.dataset is not None:
            household_weight = household("household_weight", period)
            weighted_income = MicroSeries(
                income / equivalisation, weights=household_weight
            )
            decile = weighted_income.decile_rank().values
        else:
            upper_bounds = [
                16000.0,
                20700.0,
                24100.0,
                27200.0,
                31800.0,
                37200.0,
                45200.0,
                53300.0,
                68500.0,
                np.inf,
            ]

            equivalised_income = income / equivalisation
            decile = np.select(
                [equivalised_income <= upper_bounds[i] for i in range(10)],
                list(range(1, 11)),
            )
        # Set negatives to -1.
        # This avoids the bottom decile summing to a negative number,
        # which would flip the % change in the interface.
        return where(income < 0, -1, decile)
