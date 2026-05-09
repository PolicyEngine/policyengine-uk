from policyengine_uk.model_api import *


class ashford_council_tax_reduction_disability_or_carer_income_disregard(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether Ashford CTR applies the disability or carer income disregard"
    definition_period = YEAR
    reference = (
        "https://www.ashford.gov.uk/media/0n4nud13/ashford-ctr-scheme-2026-final.pdf"
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        claimant_or_partner = person("is_adult", period) & ~child_or_young_person
        receives_disability_or_carer_benefit = (
            (person("dla", period) > 0)
            | (person("pip", period) > 0)
            | (person("carers_allowance", period) > 0)
        )
        return benunit.any(
            (claimant_or_partner | child_or_young_person)
            & receives_disability_or_carer_benefit
        )
