from policyengine_uk.model_api import *


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
        # float64, so that exact ages compare cleanly with State Pension age.
        age = np.floor(person("age", period)).astype(np.float64)
        months = person("months_since_last_birthday", period).astype(np.float64)
        age_in_months = 12 * age + months
        spa = person("state_pension_age", period).astype(np.float64)
        months_since = age_in_months - 12 * spa
        # Rounding to a thousandth of a month (under an hour) removes float
        # error, so reaching State Pension age exactly on 6 October counts.
        return np.round(months_since, 3)
