from openfisca_uk.tools.general import *
from openfisca_uk.entities import *


class in_poverty_bhc(Variable):
    value_type = bool
    entity = Household
    label = (
        u"Whether the household is in absolute poverty, before housing costs"
    )
    definition_period = YEAR

    def formula(household, period, parameters):
        return (
            household("equiv_household_net_income", period)
            < parameters(period).poverty.absolute_poverty_threshold_bhc
            * WEEKS_IN_YEAR
        )


class in_poverty_ahc(Variable):
    value_type = bool
    entity = Household
    label = (
        u"Whether the household is in absolute poverty, after housing costs"
    )
    definition_period = YEAR

    def formula(household, period, parameters):
        return (
            household("equiv_household_net_income_ahc", period)
            < parameters(period).poverty.absolute_poverty_threshold_ahc
            * WEEKS_IN_YEAR
        )


class in_deep_poverty_bhc(Variable):
    value_type = bool
    entity = Household
    label = u"Whether the household is in deep absolute poverty (below half the poverty line), before housing costs"
    definition_period = YEAR

    def formula(household, period, parameters):
        return household("equiv_household_net_income", period) < (
            parameters(period).poverty.absolute_poverty_threshold_bhc
            * WEEKS_IN_YEAR
            / 2
        )


class in_deep_poverty_ahc(Variable):
    value_type = bool
    entity = Household
    label = u"Whether the household is in deep absolute poverty (below half the poverty line), after housing costs"
    definition_period = YEAR

    def formula(household, period, parameters):
        return household("equiv_household_net_income_ahc", period) < (
            parameters(period).poverty.absolute_poverty_threshold_ahc
            * WEEKS_IN_YEAR
            / 2
        )


class poverty_line_bhc(Variable):
    value_type = float
    entity = Household
    label = u"The poverty line for the household, before housing costs"
    definition_period = YEAR

    def formula(household, period, parameters):
        return (
            parameters(period).poverty.absolute_poverty_threshold_bhc
            * WEEKS_IN_YEAR
            * household("household_equivalisation_bhc", period)
        )


class poverty_line_ahc(Variable):
    value_type = float
    entity = Household
    label = u"The poverty line for the household, after housing costs"
    definition_period = YEAR

    def formula(household, period, parameters):
        return (
            parameters(period).poverty.absolute_poverty_threshold_ahc
            * WEEKS_IN_YEAR
            * household("household_equivalisation_ahc", period)
        )


class poverty_gap_bhc(Variable):
    value_type = float
    entity = Household
    label = u"Positive financial gap between net household income and the poverty line"
    definition_period = YEAR

    def formula(household, period, parameters):
        net_income = household("household_net_income", period)
        return max_(0, household("poverty_line_bhc", period) - net_income)


class poverty_gap_ahc(Variable):
    value_type = float
    entity = Household
    label = u"Positive financial gap between net household income and the poverty line, after housing costs"
    definition_period = YEAR

    def formula(household, period, parameters):
        net_income = household("household_net_income_ahc", period)
        return max_(0, household("poverty_line_ahc", period) - net_income)
