from policyengine_uk.model_api import *


class buckinghamshire_council_tax_reduction_disability_income_disregard(Variable):
    value_type = bool
    entity = BenUnit
    label = "Buckinghamshire CTR disability income disregard applies"
    definition_period = YEAR
    reference = "https://buckinghamshire.moderngov.co.uk/documents/s115727/Appendix%204%20Council%20Tax%20Reduction%20Scheme%20Policy.pdf"

    def formula(benunit, period, parameters):
        person = benunit.members
        modeled_disability_benefit = benunit.max(
            person.household.any(
                (person("pip", period) > 0)
                | (person("dla", period) > 0)
                | (person("armed_forces_independence_payment", period) > 0)
            )
        )
        esa_support_component = benunit.max(
            person.household.any(
                person.benunit(
                    "buckinghamshire_council_tax_reduction_esa_support_component",
                    period,
                )
                > 0
            )
        )
        source_disability = benunit.max(
            person.household.any(
                person.benunit(
                    "buckinghamshire_council_tax_reduction_source_disability_income_disregard",
                    period,
                )
            )
        )
        return (
            (modeled_disability_benefit > 0)
            | (esa_support_component > 0)
            | (source_disability > 0)
        )
