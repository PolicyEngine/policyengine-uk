from policyengine_uk.model_api import *


class extended_childcare_entitlement(Variable):
    value_type = float
    entity = BenUnit
    label = "Annual extended childcare entitlement expenses"
    documentation = "Annual expenses for extended childcare entitlement calculated as hours per week * hourly rate * weeks per year"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        # Get weekly hours
        weekly_hours_per_child = benunit.members(
            "extended_childcare_entitlement_hours", period
        )

        # Get expense rate from parameters
        p = parameters(period).gov.dfe.extended_childcare_entitlement

        # Define constants
        # information on this link: https://www.childcarechoices.gov.uk/15-and-30-hours-childcare-support/working-families/eligibility
        # DfE considers 38 weeks per year (not whole year).
        weeks_per_year = 38
        age = benunit.members("age", period)
        subsidy_per_hour = p.expense_rate.calc(age)
        subsidy_per_child = weekly_hours_per_child * subsidy_per_hour

        # Calculate annual expenses
        return benunit.sum(subsidy_per_child) * weeks_per_year
