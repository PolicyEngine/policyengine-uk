from policyengine_uk.model_api import *


class in_relative_poverty_ahc(Variable):
    label = "in relative poverty (AHC)"
    documentation = (
        "Whether the household's equivalised HBAI net income, after housing "
        "costs, is below 60% of the contemporary median. The median is taken "
        "over individuals, as in DWP's Households Below Average Income series, "
        "so each household counts once per member. Negative incomes stay in "
        "the median and count as below the line. The absolute-line twin is "
        "in_poverty_ahc."
    )
    entity = Household
    definition_period = YEAR
    value_type = bool

    def formula(household, period, parameters):
        income = household("equiv_hbai_household_net_income_ahc", period)
        # HBAI's unit of analysis is the individual: weight every household by
        # its members so the median is the median person's income.
        person_weight = household("household_weight", period) * household(
            "household_count_people", period
        )
        median_income = MicroSeries(income, weights=person_weight).median()
        return income < (median_income * 0.6)
