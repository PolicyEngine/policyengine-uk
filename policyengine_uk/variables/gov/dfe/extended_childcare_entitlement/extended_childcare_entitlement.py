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

        # Only qualifying children of working parents (SI 2022/1134 reg 13)
        # receive the entitlement's hours.
        qualifying_child = benunit.members(
            "extended_childcare_entitlement_qualifying_child", period
        )
        weekly_hours_per_child = (
            p.extended_childcare_entitlement.hours.calc(age) * qualifying_child
        )

        # Get max hours used per child
        max_hours_used = benunit.members("max_free_entitlement_hours_used", period)

        # Use the appropriate hours based on the condition
        weekly_hours_to_use = min_(max_hours_used, weekly_hours_per_child)

        # Get the maximum hours usage for this benefit unit
        maximum_hours_usage = benunit("maximum_extended_childcare_hours_usage", period)

        # Apply the maximum hours limit
        weekly_hours_to_use = min_(
            weekly_hours_to_use, benunit.project(maximum_hours_usage)
        )

        # Compute weekly subsidy per child
        weekly_subsidy_per_child = weekly_hours_to_use * p.childcare_funding_rate.calc(
            age
        )

        # Compute total annual expenses
        weeks = p.weeks_per_year
        return benunit.sum(weekly_subsidy_per_child) * weeks
