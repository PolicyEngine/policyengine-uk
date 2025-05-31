from policyengine_uk.model_api import *


class attendance_allowance(Variable):
    value_type = float
    entity = Person
    label = "Attendance Allowance"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        aa = parameters(period).gov.dwp.attendance_allowance
        category = person("aa_category", period)
        categories = category.possible_values
        return (
            select(
                [
                    category == categories.HIGHER,
                    category == categories.LOWER,
                ],
                [aa.higher, aa.lower],
                default=0,
            )
            * WEEKS_IN_YEAR
        )
