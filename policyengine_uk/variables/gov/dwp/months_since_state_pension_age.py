from policyengine_uk.model_api import *
from policyengine_uk.utils.dates import birth_instant, grid_month


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
        age_in_months = grid_month(period.start.year, 10) - birth_instant(
            person, period
        )
        spa = person("state_pension_age", period).astype(np.float64)
        months_since = age_in_months - 12 * spa
        # Rounding to a thousandth of a month (under an hour) removes float
        # error, so reaching State Pension age exactly on 6 October counts.
        return np.round(months_since, 3)
