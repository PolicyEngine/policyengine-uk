from policyengine_uk.model_api import *


class housing_benefit_capital_injury_payment_retained(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "housing benefit capital injury payment retained"
    documentation = "Personal-injury payment remaining in possession as money, excluding trust distributions and amounts used to purchase another asset. Unobserved facts default to zero/false or an unknown future date. Amounts must be included in the capital sources being assessed and must not overlap other category amounts."
    unit = GBP
    quantity_type = STOCK
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/6",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/6",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/7",
        "https://www.legislation.gov.uk/nisr/2006/406/schedule/7",
    )
