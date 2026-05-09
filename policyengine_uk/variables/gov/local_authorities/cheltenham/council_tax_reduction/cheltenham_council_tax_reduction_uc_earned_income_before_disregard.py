from policyengine_uk.model_api import *


class cheltenham_council_tax_reduction_uc_earned_income_before_disregard(Variable):
    value_type = float
    entity = BenUnit
    label = "Cheltenham Council Tax Support Universal Credit assessed earned income before earnings disregard"
    documentation = "Source input for earned income from the Universal Credit calculation before UC earnings disregards or work allowances."
    definition_period = YEAR
    unit = GBP
    reference = "https://democracy.cheltenham.gov.uk/documents/s53359/Appendix%209%20-%20Council%20270226%20Council%20Tax%20Support%20Scheme%20for%20Working%20Age%20Customers%202026-27%20Final.pdf"

    def formula(benunit, period, parameters):
        uc_gross_earned_income = add(
            benunit, period, ["uc_mif_capped_earned_income"]
        )
        deductions = add(benunit, period, ["benunit_tax", "pension_contributions"])
        return max_(0, uc_gross_earned_income - deductions)
