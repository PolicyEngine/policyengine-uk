from policyengine_uk.model_api import *


class employer_cost(Variable):
    label = "employer cost"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        benefits = add(
            person,
            period,
            [
                "statutory_sick_pay",
                "statutory_maternity_pay",
                "statutory_paternity_pay",
            ],
        )
        return (
            person("employment_income", period)
            + person("ni_employer", period)
            + person("employer_pension_contributions", period)
            + benefits
        )
