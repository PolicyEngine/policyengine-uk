from policyengine_uk.model_api import *


class housing_benefit_qualifying_childcare_charges(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    unit = GBP
    default_value = 0
    label = "pre-assessed qualifying Housing Benefit childcare charges"
    documentation = (
        "Annual qualifying charges for this child, before the family cap and "
        "earnings limit. The supplied amount must already satisfy the relevant "
        "provider, paid-care, age, work, leave, incapacity and continuation rules "
        "(GB working-age regulation 28, pension-age regulation 31; NI 26/29). "
        "It is not generic childcare expenditure. Missing values give no "
        "deduction and may understate awards; zero does not establish that no "
        "qualifying charges exist. No dataset source has been verified."
    )
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/28",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/31",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/26",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/29",
    )
