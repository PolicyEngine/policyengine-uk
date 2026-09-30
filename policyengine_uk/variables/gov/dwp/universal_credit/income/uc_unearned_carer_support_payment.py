from policyengine_uk.model_api import *


class uc_unearned_carer_support_payment(Variable):
    value_type = float
    entity = Person
    label = "Carer Support Payment counted as Universal Credit unearned income"
    documentation = (
        "Carer Support Payment counts as unearned income 'but only up to a "
        "maximum of the amount a claimant would receive if they had an "
        "entitlement to carer's allowance' (UC Regs 2013 reg. 66(1)(b)(iiia), "
        "from 19 November 2023). Reg. 2 limits 'carer support payment' to the "
        "carer support payment component of carer support, so the Scottish "
        "Carer Supplement that carer_support_payment also includes is left "
        "out: carer_support_payment is scaled by the component's share of "
        "the weekly amount it is built from, then capped at a year of "
        "Carer's Allowance."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/66",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/2",
        "https://www.legislation.gov.uk/uksi/2023/1218/article/23",
    ]

    def formula(person, period, parameters):
        csp = parameters(period).gov.social_security_scotland.carer_support_payment
        ca = parameters(period).gov.dwp.carers_allowance
        component_share = csp.rate / (csp.rate + csp.supplement)
        component = person("carer_support_payment", period) * component_share
        return min_(component, ca.rate * WEEKS_IN_YEAR)
