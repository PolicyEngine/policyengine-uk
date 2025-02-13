from policyengine_uk.model_api import *


class extended_childcare_entitlement(Variable):
    value_type = float
    entity = BenUnit
    label = "Annual extended childcare entitlement expenses"
    documentation = (
        "Annual expenses for extended childcare entitlement calculated as "
        "hours per week * hourly rate * weeks per year"
    )
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        # Get weekly hours
        weekly_hours_per_child = benunit.members(
            "extended_childcare_entitlement_hours", period
        )

        # Get expense rate from parameters
        p = parameters(period).gov.dfe.extended_childcare_entitlement
        age = benunit.members("age", period)

        # Compute subsidy per child
        subsidy_per_child = weekly_hours_per_child * p.expense_rate.calc(age)

        # Compute total annual expenses
        return benunit.sum(subsidy_per_child) * p.weeks_per_year
