from policyengine_uk.model_api import *


class redbridge_council_tax_reduction_disability_class(Variable):
    value_type = bool
    entity = BenUnit
    label = "Redbridge Council Tax Reduction disability benefit class"
    definition_period = YEAR
    reference = "https://www.redbridge.gov.uk/media/frbd0rgm/council-tax-reduction-scheme-2026-2027-full-scheme.pdf"

    def formula(benunit, period, parameters):
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        claimant_or_partner = person("is_adult", period) & ~child_or_young_person
        disability_benefit = (
            (person("dla", period) > 0)
            | (person("pip", period) > 0)
            | (person("armed_forces_independence_payment", period) > 0)
            | (person("attendance_allowance", period) > 0)
        )
        return benunit("benunit_contains_household_head", period) & benunit.any(
            claimant_or_partner & disability_benefit
        )
