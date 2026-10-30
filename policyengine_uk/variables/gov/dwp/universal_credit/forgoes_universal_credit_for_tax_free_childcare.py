from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.hmrc.tax_free_childcare._top_up import (
    UNIVERSAL_CREDIT_AWARDS,
)

# Legacy awards a Universal Credit claim ends (SI 2014/1230 regs 8 and 46).
# A family receiving one, until DWP closes it, keeps today's claim: not
# claiming would keep that award as well as Tax-Free Childcare, which this
# comparison does not weigh.
LEGACY_AWARDS = (
    "child_tax_credit_reported",
    "working_tax_credit_reported",
    "housing_benefit_reported",
    "income_support_reported",
    "jsa_income_reported",
    "esa_income_reported",
)


class forgoes_universal_credit_for_tax_free_childcare(Variable):
    value_type = bool
    entity = BenUnit
    label = "Forgoes Universal Credit for Tax-Free Childcare"
    documentation = (
        "Whether a family that would claim Universal Credit takes Tax-Free "
        "Childcare instead, because the top-up it would get "
        "(tax_free_childcare_without_universal_credit) is worth more than "
        "what the claim brings: its award before the benefit cap and "
        "deductions, and in Scotland the Scottish Child Payment the award "
        "qualifies its children for. Universal Credit is paid only on a "
        "claim, and any award ends Tax-Free Childcare, so a family better "
        "off with the top-up does not claim. The award is taken before "
        "deductions, which repay debts the family owes either way, and "
        "before the benefit cap, which spares the earnings the Tax-Free "
        "Childcare work condition requires. A family with a legacy award a "
        "claim would end keeps its claim. A family that forgoes the award "
        "gets none (universal_credit_pre_benefit_cap); "
        "claims_universal_credit, which other rules read, is unchanged."
    )
    definition_period = YEAR
    defined_for = "claims_universal_credit"
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/5/section/1",
        "https://www.legislation.gov.uk/ukpga/2014/28/section/11",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.hmrc.tax_free_childcare
        if not any(
            program in UNIVERSAL_CREDIT_AWARDS for program in p.disqualifying_benefits
        ):
            # Universal Credit no longer ends Tax-Free Childcare.
            return np.zeros(benunit.count, dtype=bool)
        award = benunit("uc_maximum_amount", period) - benunit(
            "uc_income_reduction", period
        )
        # Any award qualifies the family for Scottish Child Payment
        # (is_scp_eligible). A family that could forgo has no other
        # qualifying benefit: the rest are legacy awards, which keep the
        # claim, or Pension Credit, which rules Universal Credit out. So the
        # claim brings the family's whole payment. It is built from the
        # payment's own conditions, since scottish_child_payment reads
        # universal_credit.
        scp = parameters(period).gov.social_security_scotland.scottish_child_payment
        person = benunit.members
        in_scotland = person.household("country", period).decode_to_str() == "SCOTLAND"
        scp_children = benunit.sum(
            in_scotland
            & person("is_scp_eligible_child", period)
            & person("would_claim_scp", period)
        )
        scp_from_claim = (
            scp_children
            * scp.amount
            * WEEKS_IN_YEAR
            * scp.qualifying_benefits.universal_credit
        )
        top_up = add(benunit, period, ["tax_free_childcare_without_universal_credit"])
        legacy = add(benunit, period, LEGACY_AWARDS) > 0
        keeps_no_legacy_award = ~legacy | benunit("legacy_benefits_closed", period)
        return keeps_no_legacy_award & (award > 0) & (top_up > award + scp_from_claim)
