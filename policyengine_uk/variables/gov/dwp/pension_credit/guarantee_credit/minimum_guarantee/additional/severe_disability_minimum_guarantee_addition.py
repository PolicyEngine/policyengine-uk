from policyengine_uk.model_api import *


class severe_disability_minimum_guarantee_addition(Variable):
    label = "Severe disability-related increase"
    documentation = (
        "The additional amount for a claimant treated as severely disabled "
        "under SPC Regs 2002 Sch. I para. 1, at the reg. 6(5)(a) rate, or "
        "twice it under reg. 6(5)(b) for a couple who both qualify without "
        "relying on a para. 1(2)(b) hospital deeming and for neither of whom "
        "anyone receives a carer benefit. A single claimant must receive a "
        "qualifying benefit (head (a)); a couple must both receive one (head "
        "(b)), or one must receive one while the other is certified blind "
        "(head (c)). An adult residing with them bars every head unless Sch. I "
        "para. 2 ignores them. The model does not record whom a carer cares "
        "for: a carer benefit received by another member of the benefit unit "
        "is taken to be for caring for the claimant or partner, and carers "
        "outside the benefit unit are seen only through the residence bar."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/I/paragraph/1",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/I/paragraph/2",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/I/paragraph/3",
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/6",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.pension_credit.guarantee_credit.severe_disability
        person = benunit.members
        claimant_or_partner = person("is_claimant_or_partner", period)
        in_receipt = claimant_or_partner & person(
            "receives_pension_credit_severe_disability_qualifying_benefit", period
        )
        # Sch. I para. 1(2)(ba)-(bd) and (b): for head (b) only, a partner in
        # hospital is treated as in receipt. Reg. 6(5)(b) withholds the double
        # rate only where head (b) relies on para. 1(2)(b).
        treated_in_receipt_other_than_by_para_1_2_b = in_receipt | (
            claimant_or_partner
            & person(
                "would_receive_daily_living_disability_benefit_but_for_hospital_stay",
                period,
            )
        )
        treated_in_receipt = treated_in_receipt_other_than_by_para_1_2_b | (
            claimant_or_partner
            & person("would_receive_aa_or_dla_care_but_for_hospital_stay", period)
        )
        blind = claimant_or_partner & person("is_blind", period)
        # Carer benefit received by someone else in the benefit unit is taken
        # to be for caring for this claimant or partner. Nobody receives it
        # for caring for themselves.
        carer = person("receives_carer_benefit", period)
        cared_for = claimant_or_partner & (benunit.project(benunit.sum(carer)) > carer)

        claimants = benunit.sum(claimant_or_partner)
        has_partner = claimants > 1
        partners_cared_for = benunit.sum(cared_for)
        no_barring_resident = ~benunit(
            "has_non_exempt_adult_resident_for_pension_credit_severe_disability",
            period,
        )
        # Head (a): a claimant with no partner.
        head_a = ~has_partner & benunit.any(in_receipt) & (partners_cared_for == 0)
        # Head (b): both partners in receipt; a carer benefit for one of them
        # at most.
        head_b = (
            has_partner
            & (benunit.sum(treated_in_receipt) == claimants)
            & (partners_cared_for <= 1)
        )
        # Head (c): where head (b) does not apply, one partner in receipt and
        # not cared for by a carer benefit recipient, the other certified blind.
        other_partner_blind = benunit.project(benunit.sum(blind)) > blind
        head_c = (
            has_partner
            & ~head_b
            & benunit.any(in_receipt & ~cared_for & other_partner_blind)
        )
        treated_as_severely_disabled = no_barring_resident & (head_a | head_b | head_c)
        double_rate = (
            treated_as_severely_disabled
            & head_b
            & (benunit.sum(treated_in_receipt_other_than_by_para_1_2_b) == claimants)
            & (partners_cared_for == 0)
        )
        rate_multiple = where(double_rate, 2, treated_as_severely_disabled * 1)
        return rate_multiple * p.addition * WEEKS_IN_YEAR
