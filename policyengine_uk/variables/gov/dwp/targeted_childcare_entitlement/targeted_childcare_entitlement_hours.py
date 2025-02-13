from policyengine_uk.model_api import *


class targeted_childcare_entitlement_hours(Variable):
    value_type = float
    entity = Person
    label = "Targeted childcare entitlement hours per year"
    definition_period = YEAR
    unit = "hour"

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.targeted_childcare_entitlement

        # 1) Does the person's benefit unit meet targeted childcare entitlement criteria?
        targeted_eligible = person.benunit("targeted_childcare_entitlement_combine_benefits", period)

        # 2) Calculate hours based on age using your bracket structure
        age = person("age", period)
        hours_by_age = p.hours_by_age.calc(age)  # rename as needed if your YAML's param is different

        # 3) If the benefit unit is eligible, return hours_by_age; otherwise 0
        return where(targeted_eligible, hours_by_age, 0)
