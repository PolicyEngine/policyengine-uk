from policyengine_uk.model_api import *


class esa_main_phase(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "ESA main-phase conditions satisfied"
    documentation = "Determined ESA work-related activity/support status after assessment, its statutory exception, or a converted award. Payment alone does not establish this state."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/1A",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/21",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/4",
    )

    def formula(person, period, parameters):
        assessment_complete = person("esa_assessment_phase_ended", period) | person(
            "esa_assessment_phase_exception", period
        )
        claimed_or_credits = person("esa_claim_made", period) | person(
            "receives_limited_capability_for_work_credits", period
        )
        return (
            person("esa_converted_award", period)
            | person("esa_work_related_activity_group", period)
            | (
                claimed_or_credits
                & person("esa_support_group", period)
                & assessment_complete
            )
        )
