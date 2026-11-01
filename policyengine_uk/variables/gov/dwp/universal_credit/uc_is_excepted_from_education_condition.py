from policyengine_uk.model_api import *


class uc_is_excepted_from_education_condition(Variable):
    value_type = bool
    entity = Person
    label = "Excepted from the Universal Credit condition of not receiving education"
    documentation = (
        "Whether this person does not have to meet the basic condition in the "
        "Welfare Reform Act 2012 s. 4(1)(d) (not receiving education), under "
        "the Universal Credit Regulations 2013 reg. 14(1) or the Universal "
        "Credit (Transitional Provisions) Regulations 2014 reg. 60. The model "
        "applies these limbs: (b) entitlement to Attendance Allowance "
        "(including Armed Forces Independence Payment, reg. 2), Disability "
        "Living Allowance or PIP with limited capability for work "
        "(uc_limited_capability_for_work); (c) responsibility for a child or "
        "qualifying young person in the benefit unit; (d) a single foster "
        "parent with whom a child is placed; (e)(ii) a member of a couple "
        "who both receive education, whose partner is such a foster parent; "
        "(f) the member of a mixed-age couple who has reached the qualifying "
        "age for State Pension Credit; and reg. 60(1), a member of a family "
        "that claims Universal Credit when DWP moves it off its legacy "
        "benefits (claims_uc_at_legacy_closure) and whom the education "
        "condition does not treat as a qualifying young person "
        "(is_qualifying_young_person_for_uc_education, which applies reg. 28 "
        "of the 2014 Regulations). Limb (e)(i) needs no rule of its own: the "
        "model places responsibility for a child on the benefit unit, so "
        "both members of the couple meet (c). Under (b), the decision maker "
        "must determine limited capability for work before the course "
        "starts. uc_limited_capability_for_work can derive from disability "
        "status (is_disabled_for_benefits) without an assessment. The model "
        "can therefore retain students who have never received a limited "
        "capability for work determination, as well as students assessed "
        "after their course began. The model does not infer the "
        "determination from an ESA award, so an ESA assessment reaches this "
        "limb only where a user sets uc_limited_capability_for_work or a "
        "dataset sets is_disabled_for_benefits. Not modelled: (a), a person "
        "under 21, or 21 having reached that age during the course, in "
        "non-advanced education without parental support, which the model "
        "does not observe; under (b), the other benefits it lists (Scottish "
        "disability assistance, constant attendance allowance and war "
        "pension attendance payments), which the model has no variables "
        "for; and reg. 60(2), which ends the transitional protection. The "
        "model identifies foster parents through either input, "
        "uc_is_responsible_foster_parent_of_child_under_one or "
        "uc_is_foster_parent_or_new_friend_or_family_carer. The second also "
        "holds a foster parent between placements, with no child placed, "
        "and a friend or family carer, who is responsible for the child and "
        "so meets (c) under the law. The Universal Credit Regulations "
        "(Northern Ireland) 2016 reg. 14(1) lists the same exceptions."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/14",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/2",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/28",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/60",
        "https://www.legislation.gov.uk/nisr/2016/216/regulation/14",
    )

    def formula(person, period, parameters):
        benunit = person.benunit
        claimant_or_partner = person("is_uc_assessed_claimant", period)
        in_couple = benunit.sum(claimant_or_partner) == 2
        # Reg. 14(1)(b): "entitled to attendance allowance, ... disability
        # living allowance, ... or personal independence payment", and the
        # decision maker has determined limited capability for work.
        disability_benefit = (
            (person("attendance_allowance", period) > 0)
            | (person("armed_forces_independence_payment", period) > 0)
            | (person("dla", period) > 0)
            | (person("pip", period) > 0)
        )
        disabled_with_limited_capability_for_work = disability_benefit & person(
            "uc_limited_capability_for_work", period
        )
        # Reg. 14(1)(c): "responsible for a child or a qualifying young
        # person".
        responsible_for_child = claimant_or_partner & benunit(
            "is_responsible_for_child_or_qualifying_young_person_for_universal_credit",
            period,
        )
        foster_parent = claimant_or_partner & (
            person("uc_is_responsible_foster_parent_of_child_under_one", period)
            | person("uc_is_foster_parent_or_new_friend_or_family_carer", period)
        )
        # Reg. 14(1)(d): "a single person and a foster parent with whom a
        # child is placed".
        single_foster_parent = foster_parent & ~in_couple
        # Reg. 14(1)(e)(ii): "a member of a couple, both of whom are
        # receiving education, and the other member is ... a foster parent
        # with whom a child is placed".
        both_receiving_education = (
            benunit.sum(claimant_or_partner & person("uc_receiving_education", period))
            == 2
        )
        partner_is_foster_parent = benunit.sum(foster_parent) - foster_parent > 0
        student_couple_with_foster_partner = (
            claimant_or_partner
            & in_couple
            & both_receiving_education
            & partner_is_foster_parent
        )
        # Reg. 14(1)(f): "has reached the qualifying age for state pension
        # credit" and "is a member of a couple the other member of which has
        # not reached that age".
        older_member_of_mixed_age_couple = (
            claimant_or_partner
            & person("has_attained_state_pension_credit_qualifying_age", period)
            & benunit("is_mixed_age_couple", period)
        )
        # SI 2014/1230 reg. 60(1): where a person who has made a qualifying
        # claim does not meet the condition "because the person is
        # undertaking a full-time course (see regulation 12(2) and 13 ...),
        # that condition is not to apply ... while they are continuing to
        # undertake that course". A qualifying young person receives
        # education under reg. 12(1A), not reg. 12(2); reg. 28 applies
        # first, so a person entitled to an existing benefit takes reg.
        # 12(2) and keeps the protection.
        migrated_student = (
            claimant_or_partner
            & benunit("claims_uc_at_legacy_closure", period)
            & ~person("is_qualifying_young_person_for_uc_education", period)
        )
        return (
            disabled_with_limited_capability_for_work
            | responsible_for_child
            | single_foster_parent
            | student_couple_with_foster_partner
            | older_member_of_mixed_age_couple
            | migrated_student
        )
