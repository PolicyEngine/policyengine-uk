from policyengine_uk.model_api import *


class housing_benefit_individual_non_dep_deduction_eligible(Variable):
    value_type = bool
    entity = Person
    label = "eligible person for the Housing Benefit non-dependent deduction"
    definition_period = YEAR

    def formula(person, period, parameters):
        rent_liable = person.benunit("benunit_is_rent_liable", period)
        p = parameters(period).gov.dwp.housing_benefit.non_dep_deduction
        age_eligible = person("age", period) >= p.age_threshold
        return age_eligible & ~rent_liable
