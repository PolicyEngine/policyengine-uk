from policyengine_uk.model_api import *


class north_yorkshire_council_tax_reduction_uc_relevant_period_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether a North Yorkshire UC claimant remains in the pensioner scheme during the source relevant period"
    documentation = "Covers the source transitional protection for pension-age tax-credit-to-Universal-Credit cases where the UC award is disregarded for pensioner-status classification."
    definition_period = YEAR
    reference = "https://www.northyorks.gov.uk/sites/default/files/2026-03/North%20Yorkshire%20Council%27s%20Council%20Tax%20Reduction%20Scheme%202026%20to%202027.pdf"
    default_value = False
