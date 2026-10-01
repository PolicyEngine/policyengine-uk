from policyengine_uk.model_api import *


class is_scp_eligible(Variable):
    label = "Eligible for Scottish Child Payment"
    documentation = (
        "Whether this person is eligible for Scottish Child Payment. "
        "Requires: eligible child, in Scotland, family receives qualifying benefit."
    )
    entity = Person
    definition_period = YEAR
    value_type = bool
    reference = "https://www.legislation.gov.uk/ssi/2020/351/contents"

    def formula(person, period, parameters):
        # Check if household is in Scotland
        in_scotland = person.household("country", period).decode_to_str() == "SCOTLAND"

        # Get SCP parameters
        p = parameters(period).gov.social_security_scotland.scottish_child_payment
        weekly_amount = p.amount

        # SCP only available when amount > 0 (i.e., after Feb 2021)
        scp_available = weekly_amount > 0

        # Check if child is eligible (age requirement)
        is_eligible_child = person("is_scp_eligible_child", period)

        # Check if family receives a qualifying benefit
        qb = p.qualifying_benefits
        benunit = person.benunit

        receives_uc = (benunit("universal_credit", period) > 0) & qb.universal_credit
        receives_ctc = (benunit("child_tax_credit", period) > 0) & qb.child_tax_credit
        receives_wtc = (
            benunit("working_tax_credit", period) > 0
        ) & qb.working_tax_credit
        receives_income_support = (
            benunit("income_support", period) > 0
        ) & qb.income_support
        # SSI 2020/351 reg 18(e)-(f): the individual responsible for the child
        # (through their own or their partner's Child Benefit, Pension Credit or
        # Universal Credit award, regs 9 and 12) has been awarded the benefit.
        # That is the claimant or partner, not another member of the benefit unit.
        receives_jsa_income = (
            benunit("claimant_or_partner_jsa_income", period) > 0
        ) & qb.jsa_income
        receives_esa_income = (
            benunit("claimant_or_partner_esa_income", period) > 0
        ) & qb.esa_income
        receives_pension_credit = (
            benunit("pension_credit", period) > 0
        ) & qb.pension_credit

        receives_qualifying_benefit = (
            receives_uc
            | receives_ctc
            | receives_wtc
            | receives_income_support
            | receives_jsa_income
            | receives_esa_income
            | receives_pension_credit
        )

        return (
            in_scotland
            & scp_available
            & is_eligible_child
            & receives_qualifying_benefit
        )
