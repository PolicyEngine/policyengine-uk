from policyengine_uk.model_api import *
from policyengine_uk.utils.dates import (
    birth_instant_from_age,
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
        "moves with the period. It can be set directly for a year, with age "
        "set to the person's age on 6 October of it (anything else raises an "
        "error); like age, an input applies only to the year it is given for. "
        "A situation that sets it for some people gives the others 0, which "
        "the rules read as not given."
    )
    definition_period = YEAR
    unit = "date"

    def formula(person, period, parameters):
        # On a grid whose months start on the 6th: age years and
        # months_since_last_birthday months before 6 October.
        birth = birth_instant_from_age(
            period.start.year,
            person("age", period),
            person("months_since_last_birthday", period),
        )
        return grid_months_to_yyyymmdd(birth)
