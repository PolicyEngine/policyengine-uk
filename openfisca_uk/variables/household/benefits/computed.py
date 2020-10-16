from openfisca_core.model_api import *
from openfisca_uk.entities import *


class winter_fuel_allowance(Variable):
    value_type = float
    entity = Household
    label = u"label"
    definition_period = ETERNITY

    def formula(household, period, parameters):
        max_age_in_household = household.max(household.members("age", period))
        reporting_claim = household("household_WFA_reported", period) > 0
        weeks_in_year = 365.25 / 7
        return reporting_claim * (
            max_age_in_household
            >= parameters(
                period
            ).benefits.winter_fuel_allowance.basic_age_threshold
        ) * parameters(
            period
        ).benefits.winter_fuel_allowance.basic_amount / weeks_in_year + (
            max_age_in_household
            >= parameters(
                period
            ).benefits.winter_fuel_allowance.higher_age_threshold
        ) * parameters(
            period
        ).benefits.winter_fuel_allowance.higher_amount / weeks_in_year
