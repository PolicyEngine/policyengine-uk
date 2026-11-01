from policyengine_uk.model_api import *


class household_income_decile_ahc(Variable):
    label = "household income decile after housing costs"
    documentation = (
        "Decile of equivalised HBAI household net income after housing costs "
        "(person-weighted). Negative values are reset to zero for ranking only. "
        "Households with equal ranking incomes share the rank at the top of "
        "their group, following the before-housing-costs decile convention."
    )
    reference = "https://www.gov.uk/government/statistics/households-below-average-income-for-financial-years-ending-1995-to-2025/households-below-average-income-background-information-and-methodology-report-fye-2025#deciles-and-quintiles"
    entity = Household
    definition_period = YEAR
    value_type = int

    def formula(household, period, parameters):
        income = max_(household("equiv_hbai_household_net_income_ahc", period), 0)
        count_people = household("household_count_people", period)
        household_weight = household("household_weight", period)
        weighted_income = MicroSeries(income, weights=household_weight * count_people)
        return weighted_income.decile_rank().values
