from policyengine_uk.model_api import *


class is_cared_for_by_carer_benefit_recipient(Variable):
    value_type = bool
    entity = Person
    label = "Someone receives a carer benefit for caring for this person"
    documentation = (
        "Someone is entitled to and in receipt of Carer's Allowance or Carer "
        "Support Payment in respect of caring for this person: the carer "
        "condition of the legacy severe disability premium (HB Regs 2006 Sch 3 "
        "para 14(2)(a)(iii) and (2)(b); IS, ESA and JSA alike) and of the "
        "Pension Credit severe disability addition (SPC Regs 2002 Sch I para "
        "1(1)). The data say who receives a carer benefit but not whom they "
        "care for, so each award is attributed. A carer benefit is paid for "
        "caring for a person who is severely disabled for Carer's Allowance "
        "(is_severely_disabled_for_carers_allowance), a carer has one award "
        "(SSCBA 1992 s.70(7)), and only one person is paid for caring for the "
        "same severely disabled person (s.70(7ZA) to (7ZC); both rules were "
        "in s.70(7) before 16 November 2023). No one is their own carer. A "
        "carer cares for someone in their own benefit unit if they can: a "
        "claimant or partner first, then another member such as a disabled "
        "child. Every other carer in the household, including one left over "
        "in their own unit, cares for a claimant or partner not yet cared for "
        "in another benefit unit if there is one, taking the units in "
        "descending order of their eldest member's age (ties in person order, "
        "the order people are listed in the input or dataset); otherwise the "
        "award is taken to be for someone outside the household. The data "
        "cannot say whether a carer cares for a claimant or partner or for "
        "another disabled member, such as a child, so putting claimants and "
        "partners first, and placing left-over carers only with claimants and "
        "partners of other units, is a choice: where the carer in fact cares "
        "for the child and the claimant or partner otherwise qualifies, it "
        "withholds a premium or addition the law would pay, or for a couple "
        "pays the single rate instead of the double rate. Where not "
        "everyone can have a carer, those who are not carers themselves come "
        "first, then person order; the number cared for in a benefit unit "
        "does not depend on that choice. Carers outside the household are not "
        "observed, and nor is a carer whose allowance runs on for up to eight "
        "weeks after the person they cared for has died (s.70(1A)). A "
        "Universal Credit award that includes the carer element also counts "
        "in law but is not attributed here: "
        "reading Universal Credit would be circular, because the Universal "
        "Credit non-dependant deduction exemption reads Pension Credit. Such a "
        "carer living in the household already bars both the premium and the "
        "addition through their residence conditions unless their presence "
        "is ignored. Receipt is receives_carer_benefit: a positive Carer's "
        "Allowance or Carer Support Payment after the overlapping-benefit "
        "adjustment. A carer whose award an overlapping benefit, such as a "
        "higher State Pension, reduces to nil is entitled but not in receipt, "
        "so is not attributed."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/4/section/70",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/14",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/I/paragraph/1",
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/2/paragraph/13",
        "https://www.legislation.gov.uk/uksi/2008/794/schedule/4/paragraph/6",
        "https://www.legislation.gov.uk/uksi/1996/207/schedule/1/paragraph/15",
    )

    def formula(person, period, parameters):
        claimant_or_partner = person("is_claimant_or_partner", period)
        could_be_cared_for = person("is_severely_disabled_for_carers_allowance", period)
        carer = person("receives_carer_benefit", period)
        age = person("age", period)
        # Who takes a carer when not everyone can: someone who is not a carer
        # themselves, then person order (get_rank breaks ties by position).
        priority = carer.astype(int)

        # Within the benefit unit: claimants and partners, then other members.
        cp_target = claimant_or_partner & could_be_cared_for
        cp_targets = person.benunit.sum(cp_target)
        targets = person.benunit.sum(could_be_cared_for)
        can_care_for_cp = carer & (cp_targets - cp_target > 0)
        can_care_within = carer & (targets - could_be_cared_for > 0)
        cp_cared_for_within = min_(cp_targets, person.benunit.sum(can_care_for_cp))
        cared_for_within = min_(targets, person.benunit.sum(can_care_within))
        cp_within = cp_target & (
            person.get_rank(person.benunit, priority, condition=cp_target)
            < cp_cared_for_within
        )
        other_target = could_be_cared_for & ~claimant_or_partner
        other_within = other_target & (
            person.get_rank(person.benunit, priority, condition=other_target)
            < cared_for_within - cp_cared_for_within
        )

        # Every carer not placed in their own unit cares for a claimant or
        # partner of another unit. Units take them in descending order of
        # their eldest member's age, each taking as many as it needs from the
        # carers of other units that are not yet placed.
        left_over = person.benunit.sum(carer) - cared_for_within
        eldest = person.get_rank(person.benunit, -age) == 0
        left_over_in_household = person.household.sum(where(eldest, left_over, 0))
        needed = cp_targets - cp_cared_for_within
        unit_order = person.benunit.max(
            where(eldest, person.get_rank(person.household, -age, condition=eldest), -1)
        )
        from_other_units = np.zeros_like(needed)
        placed_in_household = np.zeros_like(needed)
        for rank in range(int(np.max(unit_order, initial=-1)) + 1):
            available = max_(
                0,
                min_(
                    left_over_in_household - left_over,
                    left_over_in_household - placed_in_household,
                ),
            )
            taken = where(unit_order == rank, min_(needed, available), 0)
            from_other_units = from_other_units + taken
            placed_in_household = placed_in_household + person.household.sum(
                where(eldest, taken, 0)
            )
        cp_not_yet = cp_target & ~cp_within
        cp_from_other_units = cp_not_yet & (
            person.get_rank(person.benunit, priority, condition=cp_not_yet)
            < from_other_units
        )
        return cp_within | other_within | cp_from_other_units
