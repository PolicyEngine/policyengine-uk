from policyengine_uk.model_api import *


class housing_benefit_child_disability_payment_or_suspension(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "housing benefit child disability payment or suspension"
    documentation = "Listed Scottish child/young-person disability payment is payable, or a listed DLA/PIP/Scottish award is suspended solely for hospital treatment while the child remains in the family. This is an actual award fact, not general disability."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/3",
        "https://www.legislation.gov.uk/uksi/2015/1857/made",
        "https://www.legislation.gov.uk/nisr/2016/310/made",
    )
