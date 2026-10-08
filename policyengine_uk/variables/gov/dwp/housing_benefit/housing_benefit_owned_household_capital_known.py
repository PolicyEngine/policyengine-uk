from policyengine_uk.model_api import *


class housing_benefit_owned_household_capital_known(Variable):
    value_type = bool
    entity = BenUnit
    definition_period = YEAR
    label = "housing benefit owned household capital known"
    documentation = "Whether the combined claimant/partner beneficial interest in the configured household capital sources is known, including a known zero. Unobserved facts default to zero/false or an unknown future date. Amounts must be included in the capital sources being assessed and must not overlap other category amounts."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/6",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/6",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/7",
        "https://www.legislation.gov.uk/nisr/2006/406/schedule/7",
    )
