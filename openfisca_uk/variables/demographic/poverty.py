from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *

class in_poverty_bhc(Variable):
    value_type = bool
    entity = Household
    label = (
        u"Whether the household is in absolute poverty, before housing costs"
    )
    definition_period = WEEK

    def formula(household, period, parameters):
        return (
            household("equiv_household_net_income", period, options=[DIVIDE])
            < parameters(period).poverty.absolute_poverty_threshold_bhc
        )


class in_poverty_ahc(Variable):
    value_type = bool
    entity = Household
    label = (
        u"Whether the household is in absolute poverty, after housing costs"
    )
    definition_period = WEEK

    def formula(household, period, parameters):
        return (
            household(
                "equiv_household_net_income_ahc", period, options=[DIVIDE]
            )
            < parameters(period).poverty.absolute_poverty_threshold_ahc
        )


class poverty_line_bhc(Variable):
    value_type = float
    entity = Household
    label = u"The poverty line for the household, before housing costs"
    definition_period = WEEK

    def formula(household, period, parameters):
        return parameters(
            period
        ).poverty.absolute_poverty_threshold_bhc * household(
            "household_equivalisation_bhc", period.this_year
        )


class poverty_line_ahc(Variable):
    value_type = float
    entity = Household
    label = u"The poverty line for the household, after housing costs"
    definition_period = WEEK

    def formula(household, period, parameters):
        return parameters(
            period
        ).poverty.absolute_poverty_threshold_ahc * household(
            "household_equivalisation_ahc", period.this_year
        )


class poverty_gap_bhc(Variable):
    value_type = float
    entity = Household
    label = u"Positive financial gap between net household income and the poverty line"
    definition_period = WEEK

    def formula(household, period, parameters):
        net_income = household(
            "household_net_income", period, options=[DIVIDE]
        )
        return max_(0, household("poverty_line_bhc", period) - net_income)


class poverty_gap_ahc(Variable):
    value_type = float
    entity = Household
    label = u"Positive financial gap between net household income and the poverty line, after housing costs"
    definition_period = WEEK

    def formula(household, period, parameters):
        net_income = household(
            "household_net_income_ahc", period, options=[DIVIDE]
        )
        return max_(0, household("poverty_line_ahc", period) - net_income)
