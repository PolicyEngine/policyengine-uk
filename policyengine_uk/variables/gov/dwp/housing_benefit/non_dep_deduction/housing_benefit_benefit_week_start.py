from policyengine_uk.model_api import *


class housing_benefit_benefit_week_start(Variable):
    value_type = int
    entity = BenUnit
    definition_period = YEAR
    label = "housing benefit benefit week start"
    documentation = "Weekday on which this claimant's benefit week begins, Monday=0 through Sunday=6. Defaults to Monday; affects only rounding the statutory 26-week postponement."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/74",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/55",
        "https://www.legislation.gov.uk/nisr/2006/405/regulation/72",
        "https://www.legislation.gov.uk/nisr/2006/406/regulation/53",
    )
