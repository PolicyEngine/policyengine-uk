from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.universal_credit.deductions._deduction_amounts import (
    estimated_advance_repayment_amount,
)


class uc_advance_repayment_amount(Variable):
    label = "UC advance repayment cash demand"
    documentation = (
        "Annual cash instalments before the deductions cap, abolition and penny floor. "
        "An explicit nonnegative amount, including zero, overrides the legacy "
        "estimate. Negative values, including the default -1, mean no amount "
        "was supplied; the deduction rate then uses the fallback for that unit. The "
        "fallback splits the supplied annual latent rate by the published type means "
        "and converts its advance share using that year's unreformed allowance. "
        "It is an annual cross-sectional estimate, not a longitudinal debt schedule."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    default_value = -1
    unit = GBP
    reference = "https://www.legislation.gov.uk/uksi/2013/383/regulation/10"

    def formula(benunit, period, parameters):
        return estimated_advance_repayment_amount(benunit, period, parameters)
