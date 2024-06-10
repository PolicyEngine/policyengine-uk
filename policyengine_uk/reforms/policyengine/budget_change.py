from policyengine_uk.model_api import *


class pre_budget_change_household_net_income(Variable):
    label = "household net income"
    documentation = "household net income"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    adds = ["household_market_income", "household_benefits"]
    subtracts = ["household_tax"]


class pre_budget_change_ons_household_income_decile(Variable):
    label = "pre-budget change household income decile (ONS matched)"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        income = household("pre_budget_change_household_net_income", period)
        equivalisation = household("household_equivalisation_bhc", period)
        household_weight = household("household_weight", period)
        weighted_income = MicroSeries(
            income / equivalisation, weights=household_weight
        )
        decile = weighted_income.decile_rank().values
        # Set negatives to -1.
        # This avoids the bottom decile summing to a negative number,
        # which would flip the % change in the interface.
        return where(income < 0, -1, decile)


class nhs_budget_change(Variable):
    label = "NHS budget change"
    entity = Household
    definition_period = YEAR
    value_type = float

    def formula(household, period, parameters):
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

        budget_increase = (
            parameters(period).gov.contrib.policyengine.nhs
            * 1e9
        )
        budget_increase_per_decile = {
            i: budget_increase * DECILE_INCIDENCE[i]
            for i in range(1, 11)
        }
        households_per_decile = (
            pd.Series(weight).groupby(decile).sum().to_dict()
        )

        average_per_decile = {
            i: budget_increase_per_decile[i] / households_per_decile[i]
            for i in range(1, 11)
        }

        return decile.map(average_per_decile).replace({np.nan: 0})
    


class education_budget_change(Variable):
    label = "education budget change"
    entity = Household
    definition_period = YEAR
    value_type = float

    def formula(household, period, parameters):
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

        budget_increase = (
            parameters(period).gov.contrib.policyengine.nhs
            * 1e9
        )
        budget_increase_per_decile = {
            i: budget_increase * DECILE_INCIDENCE[i]
            for i in range(1, 11)
        }
        households_per_decile = (
            pd.Series(weight).groupby(decile).sum().to_dict()
        )

        average_per_decile = {
            i: budget_increase_per_decile[i] / households_per_decile[i]
            for i in range(1, 11)
        }

        return decile.map(average_per_decile).replace({np.nan: 0})




class other_public_spending_budget_change(Variable):
    label = "non- budget change"
    entity = Household
    definition_period = YEAR
    value_type = float

    def formula(household, period, parameters):
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

        budget_increase = (
            parameters(period).gov.contrib.policyengine.nhs
            * 1e9
        )
        budget_increase_per_decile = {
            i: budget_increase * DECILE_INCIDENCE[i]
            for i in range(1, 11)
        }
        households_per_decile = (
            pd.Series(weight).groupby(decile).sum().to_dict()
        )

        average_per_decile = {
            i: budget_increase_per_decile[i] / households_per_decile[i]
            for i in range(1, 11)
        }

        return decile.map(average_per_decile).replace({np.nan: 0})


class household_net_income(Variable):
    label = "household net income"
    documentation = "household net income"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    adds = [
        "household_market_income",
        "household_benefits",
    ]
    subtracts = ["household_tax", "direct_tax_budget_change"]


class hbai_household_net_income(Variable):
    value_type = float
    entity = Household
    label = "Household net income (HBAI definition)"
    documentation = "Disposable income for the household, following the definition used for official poverty statistics"
    unit = GBP
    definition_period = YEAR

    adds = ["household_gross_income"]
    subtracts = ["household_tax", "baseline_hbai_excluded_income", "direct_tax_budget_change"]


class budget_change_reform(Reform):
    def apply(self):
        self.add_variables(
            pre_budget_change_ons_household_income_decile,
            pre_budget_change_household_net_income,
            direct_tax_budget_change,
        )
        self.update_variable(household_net_income)
        self.update_variable(hbai_household_net_income)


def create_budget_change_reform(parameters, period):
    if parameters(period).gov.contrib.ons.etb.direct_tax_budget_change == 0:
        return

    return budget_change_reform
