from datetime import date

from policyengine_uk.model_api import *


class housing_benefit_continuous_award_end(Variable):
    value_type = date
    entity = BenUnit
    definition_period = YEAR
    label = "housing benefit continuous award end"
    documentation = "Last day of that uninterrupted HB award sequence; leave unknown/future for an ongoing award only when its start is supplied. Unobserved facts default to zero/false or an unknown future date. Amounts must be included in the capital sources being assessed and must not overlap other category amounts."
    default_value = date(9999, 1, 1)
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/6",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/6",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/7",
        "https://www.legislation.gov.uk/nisr/2006/406/schedule/7",
    )
