from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.hmrc.private_school_vat import (
    private_school_vat_liability,
)


class baseline_private_school_vat(Variable):
    label = "baseline private school VAT"
    documentation = "private_school_vat under baseline parameters."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):
        return private_school_vat_liability(
            household, period, parameters(period).baseline.gov
        )
