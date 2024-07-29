from policyengine_uk.model_api import *


class uc_individual_non_dep_deduction_eligible(Variable):
    value_type = bool
    entity = Person
    label = "Eligible person for the Universal Credit non-dependent deduction"
    definition_period = YEAR

    def formula(person, period, parameters):
        not_rent_liable = ~person.benunit("benunit_is_rent_liable", period)
        p = parameters(
            period
        ).gov.dwp.universal_credit.elements.housing.non_dep_deduction
        age = person("age", period)
        age_eligible = age >= p.age_threshold
        exempt = person("uc_non_dep_deduction_exempt", period)
        return ~exempt & age_eligible & not_rent_liable
