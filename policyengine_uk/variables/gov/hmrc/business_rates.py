from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.hmrc.baseline_business_rates import (
    baseline_business_rates,
)


class business_rates(Variable):
    label = "Business rates incidence"
    documentation = "Total incidence from exposure to business rates via corporate shareholdings"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    formula = baseline_business_rates.formula
