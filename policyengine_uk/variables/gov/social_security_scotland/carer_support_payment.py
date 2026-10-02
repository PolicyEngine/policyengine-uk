from policyengine_uk.model_api import *


class carer_support_payment(Variable):
    value_type = float
    entity = Person
    label = "Carer Support Payment"
    documentation = (
        "The Carer Support Payment component of Carer Support, which replaces "
        "Carer's Allowance for eligible carers living in Scotland. The "
        "Scottish Carer Supplement paid with it from 15 March 2026 is a "
        "separate component: see scottish_carer_supplement."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        "https://www.mygov.scot/carer-support-payment",
        "https://www.legislation.gov.uk/asp/2018/9/part/4",
        "https://www.legislation.gov.uk/ssi/2023/302/regulation/3",
    ]

    def formula(person, period, parameters):
        in_scotland = person.household("country", period).decode_to_str() == "SCOTLAND"
        csp_in_effect = period.start.year >= 2025
        csp = parameters(period).gov.social_security_scotland.carer_support_payment
        weekly_care_hours = person("care_hours", period)
        meets_hours = weekly_care_hours >= csp.min_hours
        receives_ca = person("carers_allowance_reported", period) > 0
        would_claim = person("would_claim_carers_allowance", period)
        eligible = (
            in_scotland & csp_in_effect & (meets_hours | receives_ca) & would_claim
        )
        return eligible * csp.rate * WEEKS_IN_YEAR
