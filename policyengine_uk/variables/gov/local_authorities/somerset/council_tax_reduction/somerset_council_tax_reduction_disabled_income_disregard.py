from policyengine_uk.model_api import *


class somerset_council_tax_reduction_disabled_income_disregard(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether Somerset CTR applies the disabled household income disregard"
    definition_period = YEAR
    reference = "https://somerset.moderngov.co.uk/documents/s59784/05a%20APPENDIX%203%20Somerset%20S13A%20202627%20Scheme%20DRAFT.pdf"

    def formula(benunit, period, parameters):
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        claimant_or_partner = person("is_adult", period) & ~child_or_young_person
        disabled = (
            (person("attendance_allowance", period) > 0)
            | (person("dla", period) > 0)
            | (person("pip", period) > 0)
            | (person("armed_forces_independence_payment", period) > 0)
            | person("is_disabled_for_benefits", period)
            | person("is_blind", period)
        )
        return benunit.any((claimant_or_partner | child_or_young_person) & disabled)
