from policyengine_uk.model_api import *


class cotswold_council_tax_reduction_uc_earned_income_before_disregard(Variable):
    value_type = float
    entity = BenUnit
    label = "Cotswold Council Tax Support Universal Credit assessed earned income before earnings disregard"
    documentation = "Source input for earned income from the Universal Credit calculation before UC earnings disregards or work allowances."
    definition_period = YEAR
    unit = GBP
    reference = "https://cotswold.gov.uk/media/k04l1hc2/cdc-cts-scheme-2026-27.pdf"

    def formula(benunit, period, parameters):
        return benunit("uc_earned_income", period)
