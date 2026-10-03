from policyengine_uk.model_api import *


class scottish_carer_supplement(Variable):
    value_type = float
    entity = Person
    label = "Scottish Carer Supplement"
    documentation = (
        "Paid for each week in which Carer Support Payment is payable, from 15 "
        "March 2026. Where an overlapping benefit such as State Pension "
        "reduces Carer Support Payment to £0, nothing is payable and no "
        "supplement is paid; where it reduces the payment but leaves some, "
        "the supplement is paid in full. It is a component of Carer Support "
        "separate from the Carer Support Payment component. Pension Credit "
        "and Housing Benefit, "
        "at pension age and working age, do not count it as income; it is "
        "taxable."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        "https://www.legislation.gov.uk/ssi/2023/302/regulation/14A",
        "https://www.legislation.gov.uk/ssi/2023/302/regulation/16",
        "https://www.legislation.gov.uk/uksi/2026/246/article/17/made",
        "https://www.legislation.gov.uk/uksi/2026/246/article/20/made",
        "https://www.legislation.gov.uk/uksi/2026/246/article/21/made",
        "https://www.legislation.gov.uk/uksi/2026/93/made",
    ]

    def formula(person, period, parameters):
        receives_csp = person("carer_support_payment", period) > 0
        csp = parameters(period).gov.social_security_scotland.carer_support_payment
        return receives_csp * csp.supplement * WEEKS_IN_YEAR
