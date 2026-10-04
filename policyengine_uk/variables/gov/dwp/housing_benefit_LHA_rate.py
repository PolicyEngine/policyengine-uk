from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.LHA_category import category_maximum
from policyengine_uk.variables.gov.dwp.uncapped_BRMA_LHA_rate import (
    lha_rate_for_category,
)


class housing_benefit_LHA_rate(Variable):
    value_type = float
    entity = BenUnit
    label = "LHA rate (Housing Benefit)"
    documentation = (
        "The Local Housing Allowance for the Housing Benefit category of "
        "dwelling: the Broad Rental Market Area rate, capped at the weekly "
        "national maximum for the category."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/13D",
        "https://www.legislation.gov.uk/uksi/1997/1984/schedule/3B",
    )

    def formula(benunit, period, parameters):
        category = "housing_benefit_LHA_category"
        rate = lha_rate_for_category(benunit, period, category)
        maximum = category_maximum(benunit, period, "maximum", category)
        return min_(rate, maximum * 52)
