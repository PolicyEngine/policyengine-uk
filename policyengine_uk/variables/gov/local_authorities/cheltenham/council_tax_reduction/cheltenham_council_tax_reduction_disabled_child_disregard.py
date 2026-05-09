from policyengine_uk.model_api import *


class cheltenham_council_tax_reduction_disabled_child_disregard(Variable):
    value_type = float
    entity = BenUnit
    label = "Cheltenham Council Tax Support disabled child income disregard"
    definition_period = YEAR
    unit = GBP
    reference = "https://democracy.cheltenham.gov.uk/documents/s53359/Appendix%209%20-%20Council%20270226%20Council%20Tax%20Support%20Scheme%20for%20Working%20Age%20Customers%202026-27%20Final.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.cheltenham.council_tax_reduction
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        disabled_child = child_or_young_person & (
            person("is_disabled_for_benefits", period)
            | person("cheltenham_council_tax_reduction_source_disabled_child", period)
        )
        return (
            benunit.sum(disabled_child)
            * ctr.disabled_child_disregard.weekly_amount
            * WEEKS_IN_YEAR
        )
