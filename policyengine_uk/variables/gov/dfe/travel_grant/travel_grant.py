from policyengine_uk.model_api import *


class travel_grant(Variable):
    value_type = float
    entity = Person
    label = "Travel Grant"
    documentation = (
        "Student Finance England Travel Grant. "
        "This first-pass model reimburses eligible travel expenses above the published initial contribution, "
        "reduced for household income above the published threshold. Placement status and eligible expenses "
        "must be provided explicitly because they are not recoverable from the survey."
    )
    definition_period = YEAR
    quantity_type = FLOW
    unit = GBP
    defined_for = "travel_grant_eligible"

    def formula(person, period, parameters):
        p = parameters(period).gov.dfe.travel_grant
        expenses = person("travel_grant_eligible_expenses", period)
        household_income = person("travel_grant_household_income", period)
        income_reduction = (
            max_(
                0,
                household_income - p.income_reduction.threshold,
            )
            * p.income_reduction.rate
        )
        return max_(0, expenses - p.initial_contribution - income_reduction)
