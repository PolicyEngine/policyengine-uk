from policyengine_uk.model_api import *


class is_uc_benefit_cap_exempt(Variable):
    value_type = bool
    entity = BenUnit
    label = "Exempt from the Universal Credit benefit cap"
    documentation = (
        "Whether regulation 82 (earnings) or 83 (entitlement to or receipt of "
        "certain benefits) of the UC Regs 2013 lifts the benefit cap "
        "(reg. 79(1)), or SI 2014/1230 reg. 60C disapplies it because every "
        "claimant has reached the qualifying age for State Pension Credit. "
        "That is the cap's only age exception: a mixed-age couple's joint "
        "award is capped like any other."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/79",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/82",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/83",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/60C",
    )

    def formula(benunit, period, parameters):
        return (
            benunit("is_uc_benefit_cap_exempt_earnings", period)
            | benunit("is_uc_benefit_cap_exempt_specified_benefit", period)
            | benunit("is_uc_benefit_cap_exempt_qualifying_age", period)
        )
