from policyengine_uk.model_api import *


class tewkesbury_council_tax_reduction_uc_relevant_period_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = (
        "Whether Tewkesbury's Universal Credit relevant-period pensioner exception"
        " applies"
    )
    documentation = "Default Scheme paragraph 3(2)(a) keeps a pension-age claimant on the prescribed pensioner scheme during the prescribed relevant period (the period beginning when the applicant and any partner reach State Pension Credit qualifying age and ending with the last day of the last Universal Credit assessment period), which Tewkesbury has adopted unchanged."
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2012/2886/schedule/paragraph/3"
    default_value = False
