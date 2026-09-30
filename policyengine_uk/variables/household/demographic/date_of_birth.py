from policyengine_uk.model_api import *
from policyengine_uk.utils.dates import (
    exact_age_in_months,
    grid_month,
    grid_months_to_yyyymmdd,
)


class date_of_birth(Variable):
    value_type = int
    entity = Person
    label = "date of birth"
    documentation = (
        "The person's date of birth, written as a YYYYMMDD number, as date "
        "parameters are. The person was born age years and "
        "months_since_last_birthday months before the middle of the fiscal "
        "year (6 October); the day of birth is the one starting at or after "
        "that instant, so the person's legal age on 6 October is age (Family "
        "Law Reform Act 1969 s.9(1)). Rules that turn on a date of birth, "
        "such as State Pension age and the 6 April 2017 cutoffs in Universal "
        "Credit, Child Tax Credit and Pension Credit, compare it with a date. "
        "A person's age is held fixed across years, so their date of birth "
        "moves with the period."
    )
    definition_period = YEAR
    unit = "date"

    def formula(person, period, parameters):
        # Dates are in months on a grid whose months start on the 6th, so the
        # middle of the fiscal year (6 October) is a whole month.
        mid_year = grid_month(period.start.year, 10)
        age_in_months = exact_age_in_months(
            person("age", period), person("months_since_last_birthday", period)
        )
        return grid_months_to_yyyymmdd(mid_year - age_in_months)
