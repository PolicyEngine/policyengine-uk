from policyengine_uk.model_api import *


class extended_childcare_entitlement(Variable):
    value_type = float
    entity = BenUnit
    label = "annual extended childcare entitlement expenses"
    definition_period = YEAR
    unit = GBP
    defined_for = "extended_childcare_entitlement_eligible"

    def formula(benunit, period, parameters):
        # Get parameters
        p = parameters(period).gov.dfe
        age = benunit.members("age", period)

        # Compute weekly hours directly inside this function
        weekly_hours_per_child = p.extended_childcare_entitlement.hours.calc(
            age
        )

        # Compute weekly subsidy per child
        weekly_subsidy_per_child = (
            weekly_hours_per_child * p.childcare_funding_rate.calc(age)
        )

        # Compute total annual expenses
        return (
            benunit.sum(weekly_subsidy_per_child)
            * p.extended_childcare_entitlement.weeks_per_year
        )
