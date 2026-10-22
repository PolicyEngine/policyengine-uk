from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.universal_credit.deductions._deduction_amounts import (
    deduction_type_shares,
    reference_standard_allowance,
)


class uc_advance_repayment_amount(Variable):
    label = "UC advance repayment cash demand"
    documentation = (
        "Annual cash instalments before the deductions cap, abolition and penny floor. "
        "An explicit amount, including zero, overrides the legacy estimate. The "
        "fallback splits the supplied annual latent rate by the published type means "
        "and converts its advance share using that year's unreformed allowance. "
        "It is an annual cross-sectional estimate, not a longitudinal debt schedule."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/uksi/2013/383/regulation/10"

    def formula(benunit, period, parameters):
        p = parameters(period).gov.simulation.uc_deductions
        advance_share, _, _ = deduction_type_shares(benunit, period, parameters)
        latent = max_(benunit("uc_latent_deduction_rate", period), 0)
        return (
            min_(latent, p.calibration_cap)
            * advance_share
            * reference_standard_allowance(benunit, period, parameters)
        )
