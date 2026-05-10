from policyengine_uk.model_api import *


class hertsmere_council_tax_reduction_protected_group(Variable):
    value_type = bool
    entity = BenUnit
    label = "Hertsmere Council Tax Reduction protected group"
    definition_period = YEAR
    reference = "https://www.hertsmere.gov.uk/asset-library/cts-scheme-2026-27.pdf"

    def formula(benunit, period, parameters):
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        child_under_5 = child_or_young_person & (person("age", period) < 5)
        lone_parent_with_child_under_5 = benunit(
            "is_lone_parent", period
        ) & benunit.any(child_under_5)
        claimant_partner_or_dependant = (
            person("is_adult", period) | child_or_young_person
        )
        disability_benefit = (person("dla", period) > 0) | (person("pip", period) > 0)
        esa_support_component = benunit(
            "hertsmere_council_tax_reduction_esa_support_component", period
        )
        return (
            lone_parent_with_child_under_5
            | benunit.any(claimant_partner_or_dependant & disability_benefit)
            | (esa_support_component > 0)
        )
