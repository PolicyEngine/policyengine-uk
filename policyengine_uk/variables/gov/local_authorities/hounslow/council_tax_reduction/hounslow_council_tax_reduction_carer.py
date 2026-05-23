from policyengine_uk.model_api import *


class hounslow_council_tax_reduction_carer(Variable):
    value_type = bool
    entity = BenUnit
    label = "Hounslow CTS carer household"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        claimant_or_partner = person("is_adult", period) & ~child_or_young_person
        carers_allowance = benunit.any(
            claimant_or_partner & (person("carers_allowance", period) > 0)
        )
        uc_carer = benunit("uc_carer_element", period) > 0
        return carers_allowance | uc_carer
