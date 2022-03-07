from numpy import positive
from openfisca_uk.model_api import *


class maximum_housing_benefit(Variable):
    label = "Maximum Housing Benefit"
    documentation = (
        "The maximum amount of Housing Benefit that can be claimed."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/70/made"
    )

    def formula(benunit, period, parameters):
        eligible_rent = benunit("hb_eligible_rent", period)
        non_dep_deductions = benunit("hb_non_dep_deductions", period)
        return max_(eligible_rent - non_dep_deductions, 0)
