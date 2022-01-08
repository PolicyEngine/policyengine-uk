from openfisca_uk.model_api import *


class in_poverty_bhc(Variable):
    value_type = bool
    entity = Household
    label = (
        "Whether the household is in absolute poverty, before housing costs"
    )
    definition_period = YEAR

    def formula(household, period, parameters):
        income = household("equiv_hbai_household_net_income", period)
        threshold = parameters(period).poverty.absolute_poverty_threshold_bhc
        return income < (threshold * WEEKS_IN_YEAR)


class in_poverty_ahc(Variable):
    value_type = bool
    entity = Household
    label = "Whether the household is in absolute poverty, after housing costs"
    definition_period = YEAR

    def formula(household, period, parameters):
        income = household("equiv_hbai_household_net_income_ahc", period)
        threshold = parameters(period).poverty.absolute_poverty_threshold_ahc
        return income < (threshold * WEEKS_IN_YEAR)


class in_deep_poverty_bhc(Variable):
    value_type = bool
    entity = Household
    label = "Whether the household is in deep absolute poverty (below half the poverty line), before housing costs"
    definition_period = YEAR

    def formula(household, period, parameters):
        income = household("equiv_hbai_household_net_income", period)
        threshold = parameters(period).poverty.absolute_poverty_threshold_bhc
        return income < (threshold * WEEKS_IN_YEAR / 2)


class in_deep_poverty_ahc(Variable):
    value_type = bool
    entity = Household
    label = "Whether the household is in deep absolute poverty (below half the poverty line), after housing costs"
    definition_period = YEAR

    def formula(household, period, parameters):
        income = household("equiv_hbai_household_net_income_ahc", period)
        threshold = parameters(period).poverty.absolute_poverty_threshold_ahc
        return income < (threshold * WEEKS_IN_YEAR / 2)


class poverty_line_bhc(Variable):
    value_type = float
    entity = Household
    label = "The poverty line for the household, before housing costs"
    definition_period = YEAR

    def formula(household, period, parameters):
        threshold = parameters(period).poverty.absolute_poverty_threshold_bhc
        equivalisation = household("household_equivalisation_bhc", period)
        return threshold * equivalisation * WEEKS_IN_YEAR


class poverty_line_ahc(Variable):
    value_type = float
    entity = Household
    label = "The poverty line for the household, after housing costs"
    definition_period = YEAR

    def formula(household, period, parameters):
        threshold = parameters(period).poverty.absolute_poverty_threshold_ahc
        equivalisation = household("household_equivalisation_ahc", period)
        return threshold * equivalisation * WEEKS_IN_YEAR


class poverty_gap_bhc(Variable):
    value_type = float
    entity = Household
    label = "Positive financial gap between net household income and the poverty line"
    definition_period = YEAR

    def formula(household, period, parameters):
        net_income = household("hbai_household_net_income", period)
        return max_(0, household("poverty_line_bhc", period) - net_income)


class poverty_gap_ahc(Variable):
    value_type = float
    entity = Household
    label = "Positive financial gap between net household income and the poverty line, after housing costs"
    definition_period = YEAR

    def formula(household, period, parameters):
        net_income = household("hbai_household_net_income_ahc", period)
        return max_(0, household("poverty_line_ahc", period) - net_income)
