from policyengine_uk.model_api import *
from sys import stderr

AVG_YEARLY_PRIVATE_SCHOOL_COST = 15_700


class private_school_vat(Variable):
    label = "Private school VAT"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):
        private_school_vat_rate: float = parameters(
            period
        ).gov.contrib.labour.private_school_vat
        print(private_school_vat_rate, stderr)
        household_income_decile: int = household(
            "household_income_decile", period
        )
        print(household_income_decile, stderr)
        attends_private_school: bool = (
            random(household)
            < parameters(
                period
            ).calibration.programs.private_school_vat.private_school_attendance_rate[
                household_income_decile
            ]
        )
        # num_children =  How do we count children? num_children is a benunit var

        # The below is incorrect
        num_people: int = household("household_count_people", period)

        return (
            attends_private_school
            * num_people
            * AVG_YEARLY_PRIVATE_SCHOOL_COST
            * private_school_vat_rate
        )
