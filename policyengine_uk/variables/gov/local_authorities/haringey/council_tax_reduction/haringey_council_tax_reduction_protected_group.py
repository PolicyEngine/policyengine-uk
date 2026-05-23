from policyengine_uk.model_api import *


class haringey_council_tax_reduction_protected_group(Variable):
    value_type = bool
    entity = BenUnit
    label = "Haringey CTR working-age protected group"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        has_child_or_young_person = benunit.any(child_or_young_person)
        claimant_or_partner = person("is_adult", period) & ~child_or_young_person
        disability_benefit = (
            (person("pip", period) > 0)
            | (person("dla", period) > 0)
            | (person("attendance_allowance", period) > 0)
            | (person("armed_forces_independence_payment", period) > 0)
            | (person("incapacity_benefit", period) > 0)
        )
        protected_adult = benunit.any(claimant_or_partner & disability_benefit)
        protected_adult = (
            protected_adult
            | (benunit.sum(claimant_or_partner * person("esa_contrib", period)) > 0)
            | (benunit("WTC_disabled_element", period) > 0)
            | (benunit("WTC_severely_disabled_element", period) > 0)
        )
        disabled_child = benunit.any(
            child_or_young_person & person("is_disabled_for_benefits", period)
        )
        disabled_child_premium = disabled_child & (
            benunit("benefits_premiums", period) > 0
        )
        return has_child_or_young_person | protected_adult | disabled_child_premium
