from policyengine_uk.model_api import *


class west_northamptonshire_council_tax_reduction_uc_relevant_period_pensioner(
    Variable
):
    value_type = bool
    entity = Person
    label = "Whether a West Northamptonshire UC claimant remains in the pensioner scheme during the source relevant period"
    documentation = "Covers the source transitional protection for pension-age tax-credit-to-Universal-Credit cases where the UC award is disregarded for pensioner-status classification."
    definition_period = YEAR
    reference = "https://cms.westnorthants.gov.uk/media/2065/download"
    default_value = False
