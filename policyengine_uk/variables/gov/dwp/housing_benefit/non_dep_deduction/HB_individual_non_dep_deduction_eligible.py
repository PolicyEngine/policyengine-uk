from policyengine_uk.model_api import *


class HB_individual_non_dep_deduction_eligible(Variable):
    value_type = bool
    entity = Person
    label = "Eligible person for the Housing Benefit non-dependent deduction"
    definition_period = YEAR

    def formula(person, period, parameters):
        not_rent_liable = person.benunit("benunit_rent", period) == 0
        p = parameters(
            period
        ).gov.dwp.housing_benefit.non_dep_deduction
        age_eligible = person("age", period) >= p.age_threshold
        return age_eligible * not_rent_liable
