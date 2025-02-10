from policyengine_uk.model_api import *


class extended_childcare_entitlement_hours(Variable):
    value_type = float
    entity = Person
    label = "Hours of extended childcare entitlement"
    documentation = "Number of hours of extended childcare for this child entitlement based on eligibility conditions"
    definition_period = YEAR

    def formula(person, period, parameters):
        benunit = person.benunit
        # Get parameters
        p = parameters(
            period
        ).gov.dfe.extended_childcare_entitlement.childcare_entitlement_hours

        # Check income condition - must be true for all family members (except children)
        meets_income_condition = benunit.all(
            benunit.members(
                "extended_childcare_entitlement_meets_income_requirements",
                period,
            )
            | benunit.members("is_child", period)
        )

        # Check work condition
        work_eligible = (
            benunit("extended_childcare_entitlement_work_condition", period)
            > 0
        )

        hours_per_child = p.calc(person("age", period))

        return hours_per_child * meets_income_condition * work_eligible
