from policyengine_uk.model_api import *


class havering_council_tax_reduction_disabled(Variable):
    value_type = bool
    entity = BenUnit
    label = "Havering CTS disabled working-age group"
    definition_period = YEAR
    reference = "https://democracy.havering.gov.uk/documents/s83106/12%20-%20Appendix%20I%20%20Summary%20of%20the%20Council%20Tax%20Support%20Scheme%202026-27.pdf"

    def formula(benunit, period, parameters):
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        disabled_child = benunit.any(
            child_or_young_person & person("is_disabled_for_benefits", period)
        )
        return (benunit("benefits_premiums", period) > 0) | disabled_child
