from policyengine_uk.model_api import *


class cheshire_west_and_chester_council_tax_reduction_uc_relevant_period_pensioner(
    Variable
):
    value_type = bool
    entity = BenUnit
    label = "Whether Cheshire West and Chester disregards UC during the pension-age relevant period"
    definition_period = YEAR
    reference = "https://www.cheshirewestandchester.gov.uk/asset-library/council-tax-reduction-summary-2026-2027-annex-a-part-2.pdf"
    default_value = False
