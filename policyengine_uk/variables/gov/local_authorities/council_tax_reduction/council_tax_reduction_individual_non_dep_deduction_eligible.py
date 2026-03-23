from policyengine_uk.model_api import *


class council_tax_reduction_individual_non_dep_deduction_eligible(Variable):
    value_type = bool
    entity = Person
    label = "eligible person for CTR non-dependent deduction"
    definition_period = YEAR

    def formula(person, period, parameters):
        return (person("age", period) >= 18) & ~person.benunit(
            "benunit_contains_household_head", period
        )
