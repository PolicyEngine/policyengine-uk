from policyengine_uk.model_api import *


class extended_childcare_entitlement_hours(Variable):
    value_type = float
    entity = Person
    label = "Hours of extended childcare entitlement"
    documentation = "Number of hours of extended childcare for this child entitlement based on eligibility conditions"
    definition_period = YEAR
    defined_for = "extended_childcare_entitlement_meets_work_condition"

    def formula(person, period, parameters):
        # Get parameters
        p = parameters(period).gov.dfe.extended_childcare_entitlement

        hours_per_child = p.hours.calc(person("age", period))

        return hours_per_child
