from policyengine_uk.model_api import *
from policyengine_uk.utils.state_pension_age import months_since_attaining


class months_since_state_pension_age(Variable):
    value_type = float
    entity = Person
    label = "months since reaching State Pension age"
    documentation = (
        "Months between the day this person attains State Pension age and the "
        "middle of the fiscal year (6 October); negative if they attain it "
        "later. Exact age is age plus months_since_last_birthday."
    )
    definition_period = YEAR
    unit = "month"

    def formula(person, period, parameters):
        return months_since_attaining(
            person("age", period),
            person("months_since_last_birthday", period),
            person("state_pension_age", period),
        )
