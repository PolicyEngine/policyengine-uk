from policyengine_uk.model_api import *


class salary_sacrifice_returned_to_income(Variable):
    label = "Amount of salary sacrifice returned to employment income"
    documentation = (
        "The amount of salary sacrifice that is returned to regular employment income "
        "when employees reduce their salary sacrifice in response to the pension cap. "
        "This amount becomes subject to regular income tax and NI as employment income."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = (
        "https://www.ft.com/content/11602ac1-44fc-4b58-8b17-af5e851f5c95"
    )

    def formula(person, period, parameters):
        intended_ss = person(
            "pension_contributions_via_salary_sacrifice", period
        )
        adjusted_ss = person(
            "pension_contributions_via_salary_sacrifice_adjusted", period
        )

        # The difference is returned to employment income
        return intended_ss - adjusted_ss
