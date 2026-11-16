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
        "in_specified_or_temporary_accommodation doesn't change take-up. "
        "Universal Credit pays nothing towards the rent of that accommodation "
        "(UC Regs 2013 Sch 1 paras 3(h) and (i)), so a family gets help with "
        "it only through Housing Benefit; a hand-entered family that reports "
        "another of the seven means-tested benefits and no Housing Benefit "
        "claims only what it reports, and gets none. To model the claim, set "
        "housing_benefit_reported or would_claim_housing_benefit. Datasets "
        "and situations can override this directly."
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        reported_hb = add(benunit, period, ["housing_benefit_reported"]) > 0
        # A data-built simulation claims only for families that report
        # Housing Benefit. A hand-entered family also claims under the
        # per-family take-up rule.
        if built_from_data(benunit.simulation):
            return reported_hb
        return benunit("claims_all_entitled_benefits", period) | reported_hb
