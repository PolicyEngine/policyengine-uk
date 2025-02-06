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
        weekly_hours = benunit("extended_childcare_entitlement_hours", period)

        # Get expense rate from parameters
        p = parameters(period).gov.dwp.extended_childcare_entitlement

        # Define constants
        weeks_per_year = 52

        # Calculate annual expenses
        return weekly_hours * p.expense_rate * weeks_per_year
