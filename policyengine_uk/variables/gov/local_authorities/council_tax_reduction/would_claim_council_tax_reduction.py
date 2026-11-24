from policyengine_uk.model_api import *
from policyengine_uk.utils.data_source import built_from_data


class would_claim_council_tax_reduction(Variable):
    value_type = bool
    entity = BenUnit
    label = "Would claim Council Tax Reduction"
    documentation = (
        "Whether this benefit unit would claim Council Tax Reduction if eligible. "
        "Data-built simulations default to reporting families only; hand-entered "
        "situations also claim when claims_all_entitled_benefits is true. "
        "Datasets and situations can override this directly. An override "
        "changes the award only where the model simulates the local scheme "
        "(English pensioners, Scotland, Wales, and working-age claimants in "
        "the supported local authorities); elsewhere council_tax_benefit keeps "
        "the reported amount, subject to its joint-liability and "
        "non-claimant rules."
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        reported_ctr = benunit("council_tax_benefit_reported", period) > 0
        # Survey take-up is reporters-only under d1390 until calibrated inputs
        # land: https://github.com/PolicyEngine/policyengine-uk/issues/2948
        # Calculator households retain main's rule (Vahid's PR 1831 review).
        if built_from_data(benunit.simulation):
            return reported_ctr
        return benunit("claims_all_entitled_benefits", period) | reported_ctr
