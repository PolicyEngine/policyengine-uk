from policyengine_uk.model_api import *


class uc_unearned_carer_support_payment(Variable):
    value_type = float
    entity = Person
    label = "Carer Support Payment counted as Universal Credit unearned income"
    documentation = (
        "Carer Support Payment counts as unearned income 'but only up to a "
        "maximum of the amount a claimant would receive if they had an "
        "entitlement to carer's allowance' (UC Regs 2013 reg. 66(1)(b)(iiia), "
        "from 19 November 2023), so it is capped at a year of Carer's "
        "Allowance. From 15 March 2026 reg. 2 limits 'carer support payment' "
        "to the carer support payment component of carer support (S.I. "
        "2026/246 art. 25), which excludes the Scottish Carer Supplement. The "
        "component is paid at the Carer's Allowance rate, so for a full year "
        "of Carer Support Payment the cap also removes the supplement that "
        "carer_support_payment currently includes."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/66",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/2",
        "https://www.legislation.gov.uk/uksi/2023/1218/article/23",
        "https://www.legislation.gov.uk/uksi/2026/246/article/25",
    ]

    def formula(person, period, parameters):
        ca = parameters(period).gov.dwp.carers_allowance
        carer_support_payment = person("carer_support_payment", period)
        return min_(carer_support_payment, ca.rate * WEEKS_IN_YEAR)
