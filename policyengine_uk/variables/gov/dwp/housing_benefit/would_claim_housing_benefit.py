from policyengine_uk.model_api import *
from policyengine_uk.utils.data_source import built_from_data


class would_claim_housing_benefit(Variable):
    value_type = bool
    entity = BenUnit
    label = "Would claim the Housing Benefit"
    documentation = (
        "Whether this family would claim Housing Benefit if eligible. "
        "Data-built simulations default to reporting families only; hand-entered "
        "situations also claim when claims_all_entitled_benefits is true. "
        "Datasets and situations can override this directly."
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        reported_hb = add(benunit, period, ["housing_benefit_reported"]) > 0
        # d1455 applies d1390's survey reporters-only rule to HB. Hand-entered
        # situations retain main's per-family take-up rule (PR 1831 review).
        if built_from_data(benunit.simulation):
            return reported_hb
        return benunit("claims_all_entitled_benefits", period) | reported_hb
