from policyengine_uk.model_api import *
from policyengine_uk.utils.state_pension_age import months_since_attaining


class has_attained_state_pension_credit_qualifying_age(Variable):
    value_type = bool
    entity = Person
    label = "has attained the qualifying age for State Pension Credit"
    documentation = (
        "Whether the person has reached the qualifying age for State Pension "
        "Credit by the middle of the fiscal year (6 October), so is over it for "
        "most of the year. Men born before 6 December 1953 reach it before "
        "their own State Pension age of 65, so in 2018-19 and earlier this can "
        "hold where is_SP_age does not; under the statutory timetable, from "
        "2019-20 the two agree for everyone."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/2002/16/section/1",
        "https://www.legislation.gov.uk/ukpga/2012/5/section/4",
    )

    def formula(person, period, parameters):
        months_since = months_since_attaining(
            person("age", period),
            person("months_since_last_birthday", period),
            person("state_pension_credit_qualifying_age", period),
        )
        return months_since >= 0
