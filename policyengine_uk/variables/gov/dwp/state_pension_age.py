from policyengine_uk.model_api import *
from policyengine_uk.utils.dates import (
    exact_age_in_months,
    grid_month,
    yyyymmdd_to_grid_months,
)


class state_pension_age(Variable):
    value_type = float
    entity = Person
    label = "State Pension age for this person"
    documentation = (
        "The age at which this person attains State Pension age (pensionable "
        "age), set by their date of birth. Where the statute sets the day on "
        "which it is attained, this is the person's age on that day. The date "
        "of birth comes from age and months_since_last_birthday."
    )
    definition_period = YEAR
    unit = "year"
    reference = (
        "https://www.legislation.gov.uk/ukpga/1995/26/schedule/4",
        "https://www.legislation.gov.uk/ukpga/2014/19/section/26",
    )

    def formula(person, period, parameters):
        # Dates are in months on a grid whose months start on the 6th, so the
        # middle of the fiscal year (6 October) is a whole month.
        age_in_months = exact_age_in_months(
            person("age", period), person("months_since_last_birthday", period)
        )
        birth = grid_month(period.start.year, 10) - age_in_months
        attained = yyyymmdd_to_grid_months(person("state_pension_age_date", period))
        return (attained - birth) / 12
