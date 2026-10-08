from datetime import date

from policyengine_uk.model_api import *


class housing_benefit_capital_home_funds_received(Variable):
    value_type = date
    entity = Person
    definition_period = YEAR
    label = "housing benefit capital home funds received"
    documentation = "Receipt date of the retained funds earmarked for a home. Unobserved facts default to zero/false or an unknown future date. Amounts must be included in the capital sources being assessed and must not overlap other category amounts."
    default_value = date(9999, 1, 1)
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/6",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/6",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/7",
        "https://www.legislation.gov.uk/nisr/2006/406/schedule/7",
    )
