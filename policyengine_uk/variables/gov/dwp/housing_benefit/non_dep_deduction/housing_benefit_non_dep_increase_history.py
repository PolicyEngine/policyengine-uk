from policyengine_uk.model_api import *


class housing_benefit_non_dep_increase_history(Variable):
    value_type = str
    entity = BenUnit
    definition_period = YEAR
    label = "housing benefit non dep increase history"
    documentation = "JSON array of claimant-specific pending non-dependant increases. Each record identifies person_id, previous_weekly_deduction (before rent-share allocation), last_effective_date and increases [{date, kind}], where kind is arrival, circumstances or uprating. Include every pending increase since the current continuous award began or the last effective change, whichever is later. previous_weekly_deduction is the amount actually applied immediately before these increases, including ordinary uprating and immediate reductions. Empty history means no evidenced postponement; it does not assert that every resident recently arrived. See docs/engineering/housing-benefit-assessment.md."
    default_value = "[]"
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/74",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/55",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/72",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/53",
    )
