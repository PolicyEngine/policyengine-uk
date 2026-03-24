from policyengine_uk.model_api import *


class benunit_contains_household_head(Variable):
    value_type = bool
    entity = BenUnit
    label = "Benefit unit contains the oldest adult in the household"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        person = benunit.members
        household = person.household
        benunit_max_age = benunit.max(person("age", period))
        household_max_age = benunit.max(household.max(person("age", period)))
        return benunit_max_age == household_max_age
