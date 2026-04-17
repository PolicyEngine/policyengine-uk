from policyengine_uk.model_api import *


class carer_support_payment(Variable):
    value_type = float
    entity = Person
    label = "Carer Support Payment"
    documentation = (
        "Carer Support Payment replaces Carer's Allowance for "
        "eligible carers living in Scotland."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        "https://www.mygov.scot/carer-support-payment",
        "https://www.legislation.gov.uk/asp/2018/9/part/4",
    ]

    def formula(person, period, parameters):
        in_scotland = person.household("country", period).decode_to_str() == "SCOTLAND"
        csp_in_effect = period.start.year >= 2025
        csp = parameters(period).gov.social_security_scotland.carer_support_payment
        weekly_care_hours = person("care_hours", period)
        meets_hours = weekly_care_hours >= csp.min_hours
        receives_ca = person("carers_allowance_reported", period) > 0
        eligible = in_scotland & csp_in_effect & (meets_hours | receives_ca)
        weekly_amount = csp.rate + csp.supplement
        return eligible * weekly_amount * WEEKS_IN_YEAR
