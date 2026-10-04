from policyengine_uk.model_api import *


class partners_care_for_same_severely_disabled_person(Variable):
    value_type = bool
    entity = BenUnit
    label = "Claimant and partner care for the same severely disabled person"
    documentation = (
        "Whether the claimant and partner who both care are caring for the "
        "same severely disabled person. In law only one of them can then be "
        "entitled to Carer's Allowance (SSCBA 1992 s.70(7ZA)) or Carer "
        "Support Payment (SSI 2023/302 reg 5(3)), so only one satisfies the "
        "legacy carer premium condition, and Scottish working-age council tax "
        "reduction pays one premium (SSI 2021/249 Sch 1 para 5(3)-(4)). "
        "Unless supplied, it is true unless at least two of the claimant and "
        "partner are entitled to a carer benefit (is_entitled_to_carer_benefit, "
        "the condition the premium counts) and have an award: a reported "
        "Carer's Allowance or Carer Support Payment award "
        "(carers_allowance_reported, the model's reported-receipt input for "
        "both), or an entitlement that caring hours do not explain (fewer "
        "than the qualifying hours, or no claim), which must have been "
        "supplied directly (for example as carers_allowance, "
        "carers_allowance_pre_overlap or is_entitled_to_carer_benefit). The "
        "qualifying hours are Carer Support Payment's in Scotland from 2025 "
        "and Carer's Allowance's otherwise. Two awards mean two different "
        "people cared for, while caring hours cannot show who is cared for, "
        "so the entitlement of someone who cares the qualifying hours and "
        "would claim is not read as an award. "
        "With more than two members supplied as claimant or partner, "
        "two awards make the default false for all of them. The model's "
        "Carer's Allowance and Carer Support Payment entitlements follow "
        "caring hours or a reported award, and do not read this variable."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/4/section/70",
        "https://www.legislation.gov.uk/ssi/2023/302/regulation/5",
        "https://www.legislation.gov.uk/ssi/2021/249/schedule/1/paragraph/5",
    )

    def formula(benunit, period, parameters):
        claimant_or_partner = benunit.members("is_claimant_or_partner", period)
        entitled = benunit.members("is_entitled_to_carer_benefit", period)
        reported_award = benunit.members("carers_allowance_reported", period) > 0
        # The model makes someone entitled to a carer benefit only on a
        # reported award or the qualifying hours, each for someone who would
        # claim, so an entitlement the hours do not explain comes from a
        # reported award or was supplied directly (an amount in payment, a
        # pre-overlap amount or the entitlement itself). The hours are those
        # of the benefit that applies, as in carers_allowance_pre_overlap.
        gov = parameters(period).gov
        in_scotland = (
            benunit.members.household("country", period).decode_to_str() == "SCOTLAND"
        )
        csp_replaces_ca = in_scotland & (period.start.year >= 2025)
        min_hours = where(
            csp_replaces_ca,
            gov.social_security_scotland.carer_support_payment.min_hours,
            gov.dwp.carers_allowance.min_hours,
        )
        hours = benunit.members("care_hours", period)
        would_claim = benunit.members("would_claim_carers_allowance", period)
        explained_by_hours = (hours >= min_hours) & would_claim
        award = reported_award | ~explained_by_hours
        return benunit.sum(claimant_or_partner & entitled & award) < 2
