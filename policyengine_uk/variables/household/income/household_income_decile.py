from policyengine_uk.model_api import *
import datetime
import numpy as np


class household_income_decile(Variable):
    label = "household income decile"
    documentation = (
        "Decile of equivalised HBAI household net income before housing costs "
        "(person-weighted). As in HBAI, a negative income is reset to zero "
        "before ranking, so a household with negative income before the reset "
        "falls in the bottom decile."
    )
    entity = Household
    definition_period = YEAR
    value_type = int

    def formula(household, period, parameters):
        income = household("equiv_hbai_household_net_income", period)
        count_people = household("household_count_people", period)
        household_weight = household("household_weight", period)
        weighted_income = MicroSeries(income, weights=household_weight * count_people)
        return weighted_income.decile_rank().values
