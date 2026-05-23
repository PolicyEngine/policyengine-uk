from policyengine_uk.model_api import *


class harrow_council_tax_reduction_disabled_band_reduction(Variable):
    value_type = bool
    entity = Household
    label = "Harrow CTS household has a disabled band reduction"
    definition_period = YEAR
    reference = "https://www.harrow.gov.uk/downloads/file/33606/council-tax-support-scheme-2026-27"
