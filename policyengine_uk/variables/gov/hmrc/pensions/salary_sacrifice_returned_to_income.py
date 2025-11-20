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
    reference = "https://docs.google.com/document/d/1Rhrfrg7A_oZHudmA775otAn1EE4-YthgeyS9nL-PrE8/edit?tab=t.0"

    def formula(person, period, parameters):
        intended_ss = person(
            "pension_contributions_via_salary_sacrifice", period
        )
        adjusted_ss = person(
            "pension_contributions_via_salary_sacrifice_adjusted", period
        )

        # The difference is returned to employment income (cannot be negative)
        return max_(intended_ss - adjusted_ss, 0)
