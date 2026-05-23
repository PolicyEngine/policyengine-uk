from policyengine_uk.model_api import *


class colchester_council_tax_reduction_assessable_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "Colchester CTR assessable applicant and partner capital"
    documentation = "Colchester tests applicant and partner capital. For single-benefit-unit households, this uses household liquid savings as the available proxy; where non-dependants are present, supply the source-reported applicant/partner amount."
    definition_period = YEAR
    unit = GBP
    reference = "https://cbccrmdata.blob.core.windows.net/noteattachment/CBC-null-Local-council-tax-support-policy-updated-01-04-26-Local%20Council%20Tax%20support%20policy.pdf"

    def formula(benunit, period, parameters):
        source_capital = benunit(
            "colchester_council_tax_reduction_applicant_partner_capital", period
        )
        single_benunit_household = (
            benunit.household("household_num_benunits", period) == 1
        )
        return where(
            (source_capital > 0) | ~single_benunit_household,
            source_capital,
            benunit.household("savings", period),
        )
