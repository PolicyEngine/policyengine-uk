from policyengine_uk.model_api import *

class private_school_vat(Variable):
    label = "private school VAT"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):
        ADJUSTMENT_FACTOR = 1

        private_school_vat_rate: float = parameters(
            period
        ).gov.contrib.labour.private_school_vat

        avg_yearly_private_school_cost: float = parameters(
            period
        ).calibration.programs.private_school_vat.private_school_fees

        household_income_decile: int = household(
            "household_income_decile", period
        )

        attends_private_school: bool = (
            random(household)
            < parameters(
                period
            ).calibration.programs.private_school_vat.private_school_attendance_rate[
                household_income_decile
            ]
        )
        num_children = add(household, period, ["is_child"])

        return (
            attends_private_school
            * num_children
            * avg_yearly_private_school_cost
            * private_school_vat_rate
        )


# CODE IN
# 
# percent_in_private_school_by_percentile = [0, 0, 0, ..., 0.45, 0.5]
# ADJUSTMENT_FACTOR = 1
# adjusted_percent_in_private_school_by_percentile *= ADJUSTMENT_FACTOR
# 
# # calculate household income percentile
# # map to percent in private school
# # put kids in private school according to that percentage (mostly done here except percentile not decile)
# ...
# TESTING_CODE
# is_child = [False, False, True, False, ...]
# child_household_weight = [500, 1000, 2000, 700, ...]
# is_in_private_school = [False, False, True, False, ...]
# (is_in_private_school * child_household_weight).sum()
# 
# model_predicted_kids_in_private_school = 800k # should be 600k
# 
# 