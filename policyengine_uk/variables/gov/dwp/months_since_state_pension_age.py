from policyengine_uk.model_api import *
from policyengine_uk.utils.dates import birth_instant
from policyengine_uk.utils.state_pension_age import months_since_attaining


class months_since_state_pension_age(Variable):
    value_type = float
    entity = Person
    label = "months since reaching State Pension age"
    documentation = (
        "Months between the day this person attains State Pension age and the "
        "middle of the fiscal year (6 October); negative if they attain it "
        "later. Exact age is measured from the same instant of birth as "
        "state_pension_age: date_of_birth where given, otherwise a whole age "
        "plus months_since_last_birthday, or a fractional age as the exact "
        "age."
    )
    definition_period = YEAR
    unit = "month"

    def formula(person, period, parameters):
        return months_since_attaining(
            birth_instant(person, period),
            period.start.year,
            person("state_pension_age", period),
        )
