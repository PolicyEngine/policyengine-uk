from policyengine_uk.model_api import *


class islington_council_tax_reduction_non_working_protected(Variable):
    value_type = bool
    entity = BenUnit
    label = "Islington CTR non-working protected group"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        claimant_or_partner = person("is_adult", period) & ~child_or_young_person
        has_uc = person.benunit("universal_credit", period) > 0
        disability_or_lcw = (person("pip", period) > 0) | (person("dla", period) > 0)
        disability_or_lcw |= has_uc & person("uc_limited_capability_for_WRA", period)
        protected_adult = benunit.any(claimant_or_partner & disability_or_lcw)
        lone_parent_under_five = benunit("is_lone_parent", period) & (
            benunit("youngest_child_age", period) < 5
        )
        return protected_adult | lone_parent_under_five
