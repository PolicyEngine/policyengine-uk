from policyengine_uk.model_api import *


class housing_benefit_child_enhanced_disability_payment_or_suspension(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "housing benefit child enhanced disability payment or suspension"
    documentation = "Listed Scottish highest-care/enhanced-daily-living payment is payable, or a listed highest-care/enhanced-daily-living award is suspended solely for hospital treatment. This records the higher statutory benefit rate, not general severe disability."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/3",
        "https://www.legislation.gov.uk/uksi/2015/1857/made",
        "https://www.legislation.gov.uk/nisr/2016/310/made",
    )
