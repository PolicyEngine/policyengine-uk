from policyengine_uk.model_api import *


class is_housing_benefit_benefit_cap_exempt_working_tax_credit(Variable):
    value_type = bool
    entity = BenUnit
    label = "Exempt from the Housing Benefit benefit cap through working tax credit"
    documentation = (
        "Whether the claimant is, or the claimant and partner are jointly, "
        "entitled to working tax credit (HB Regs 2006 reg. 75E(2)). The "
        "39-week grace period after work ends (reg. 75E(3)-(5)) is not "
        "modelled."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2006/213/regulation/75E"

    def formula(benunit, period, parameters):
        return benunit("working_tax_credit", period) > 0
