from policyengine_uk.model_api import *


class would_claim_council_tax_reduction(Variable):
    value_type = bool
    entity = BenUnit
    label = "Would claim Council Tax Reduction"
    documentation = (
        "Whether this benefit unit would claim Council Tax Reduction if eligible. "
        "By default only families reporting it claim; datasets and situations "
        "can override this directly."
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        reported_ctr = benunit("council_tax_benefit_reported", period) > 0
        # Reporters only under Max's d1390 ruling, until calibrated take-up
        # inputs land: https://github.com/PolicyEngine/policyengine-uk-data/issues/448
        return reported_ctr
