from policyengine_uk.model_api import *
from policyengine_uk.utils.state_pension_age import months_since_attaining


class months_since_state_pension_age(Variable):
    value_type = float
    entity = Person
    label = "months since reaching State Pension age"
    documentation = (
        "Months between the day this person attains State Pension age and the "
        "middle of the fiscal year (6 October); negative if they attain it "
        "later. A whole age adds months_since_last_birthday; a fractional age "
        "is the exact age and overrides those months."
    )
    definition_period = YEAR
    unit = "month"

    def formula(person, period, parameters):
        return months_since_attaining(
            person("age", period),
            person("months_since_last_birthday", period),
            person("state_pension_age", period),
        )
