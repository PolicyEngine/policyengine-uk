from policyengine_uk.model_api import *


class braintree_council_tax_reduction_uc_relevant_period_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = (
        "Whether Braintree's Universal Credit relevant-period pensioner exception"
        " applies"
    )
    documentation = "Braintree paragraph 3(2)(a) disregards a pension-age applicant's Universal Credit award during the prescribed relevant period, keeping the applicant on the prescribed pensioner scheme rather than the local working-age banded scheme."
    definition_period = YEAR
    reference = "https://www.braintree.gov.uk/downloads/file/4374/council-tax-reduction-scheme-2026-27"
    default_value = False
