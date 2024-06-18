from policyengine_uk.model_api import *

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
        avg_yearly_private_school_cost = parameters(
            period
        ).calibration.programs.private_school_vat.private_school_fees
        # num_children =  How do we count children? num_children is a benunit var

        # The below is incorrect
        num_people: int = household("household_count_people", period)

        return (
            attends_private_school
            * num_people
            * avg_yearly_private_school_cost
            * private_school_vat_rate
        )
