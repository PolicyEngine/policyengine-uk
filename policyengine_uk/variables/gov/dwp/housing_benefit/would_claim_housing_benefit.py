from policyengine_uk.model_api import *
from policyengine_uk.utils.data_source import built_from_data


class would_claim_housing_benefit(Variable):
    value_type = bool
    entity = BenUnit
    label = "Would claim the Housing Benefit"
    documentation = (
        "Whether this family would claim Housing Benefit if eligible. "
        "Data-built simulations default to reporting families only; hand-entered "
        "situations also claim when claims_all_entitled_benefits is true, "
        "and when the family has in_specified_or_temporary_accommodation: "
        "the Secretary of State excludes that rent from Universal Credit's "
        "housing costs element (UC Regs 2013 Sch 1 paras 3(h) and (i)), so "
        "only Housing Benefit helps with it, and a family's report of another "
        "benefit doesn't show whether it claims Housing Benefit. Datasets "
        "and situations can override this directly."
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        reported_hb = add(benunit, period, ["housing_benefit_reported"]) > 0
        # A data-built simulation claims only for families that report
        # Housing Benefit. A hand-entered family also claims under the
        # per-family take-up rule, or when it has the accommodation status,
        # since Universal Credit then pays nothing towards that rent.
        if built_from_data(benunit.simulation):
            return reported_hb
        accommodation = benunit("in_specified_or_temporary_accommodation", period)
        return (
            benunit("claims_all_entitled_benefits", period)
            | reported_hb
            | accommodation
        )
