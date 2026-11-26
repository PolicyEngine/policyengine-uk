from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.universal_credit.uc_receiving_education import (
    undertakes_regulation_12_2_course,
)


class uc_is_excepted_from_education_condition(Variable):
    value_type = bool
    entity = Person
    label = "Excepted from the Universal Credit condition of not receiving education"
    documentation = (
        "Whether this person doesn't have to meet the basic condition in the "
        "Welfare Reform Act 2012 s. 4(1)(d) (not receiving education), under "
        "the Universal Credit Regulations 2013 reg. 14(1) or the Universal "
        "Credit (Transitional Provisions) Regulations 2014 reg. 60. The model "
        "applies these limbs: (b) entitlement to Attendance Allowance "
        "(including Armed Forces Independence Payment, reg. 2), Disability "
        "Living Allowance or PIP with limited capability for work "
        "(uc_limited_capability_for_work); (c) responsibility for a child or "
        "qualifying young person in the benefit unit; (d) a single foster "
        "parent with whom a child is placed; (e)(ii) a member of a couple, "
        "both of whom receive education, whose partner is such a foster "
        "parent; (f) the member of a mixed-age couple who has reached the "
        "qualifying age for State Pension Credit; and reg. 60(1), a member of "
        "a family that claims Universal Credit when DWP moves it off its "
        "legacy benefits (claims_uc_at_legacy_closure), which the model takes "
        "as the qualifying claim under reg. 48 of the 2014 Regulations, who "
        "didn't count as a qualifying young person for the condition on the "
        "migration day (is_qualifying_young_person_on_uc_migration_day, which "
        "applies reg. 28 of the 2014 Regulations to the award the claim "
        "ended), and who undertakes a full-time course that reg. 12(2) of the "
        "2013 Regulations covers: advanced education, or a course with a "
        "student loan or grant for their maintenance. Reg. 60(1) protects only "
        "a person who fails the condition on the migration day because of such "
        "a course, and only while they continue it; the model reads the "
        "model year's course inputs for both, so a person who leaves the "
        "course loses the protection that year, but a person who starts a "
        "course reg. 12(2) covers after the migration day, or moves to "
        "another such course, has it that year, which the law doesn't give. "
        "A young person whom reg. 28 alone kept outside the definition on the "
        "migration day, on a course reg. 12(2) doesn't cover, met the "
        "condition that day, so reg. 60(1) doesn't reach them. Where the "
        "claim ends that existing benefit before the award starts (a tax "
        "credit, reg. 8(2) of the 2014 Regulations), they count as a "
        "qualifying young person from the first day and receive education "
        "(reg. 12(1A)). Where it runs on past the first day (Income Support "
        "or Housing Benefit under reg. 8(2A), or income-related ESA under SI "
        "2019/1152 reg. 5), reg. 28 still excludes them that day, so they "
        "meet the condition, and reg. 5(5) of the 2013 Regulations then keeps "
        "them outside the definition while they receive Universal Credit "
        "(is_qualifying_young_person_for_uc_education). The model needs no rule of "
        "its own for limb (e)(i): it places responsibility for a child on the "
        "benefit unit, so both members of the couple meet (c). Under (b), the "
        "decision maker "
        "must determine limited capability for work before the course starts. "
        "The model can derive uc_limited_capability_for_work from disability "
        "status (is_disabled_for_benefits) without an assessment, so it can "
        "keep students who have never had a limited capability for work "
        "determination, as well as students assessed after their course began. "
        "The model doesn't infer limited capability for work from an ESA "
        "award: a user who wants an ESA assessment to count sets "
        "uc_limited_capability_for_work or uc_limited_capability_for_WRA, or a "
        "user or dataset sets is_disabled_for_benefits, from which the model "
        "derives limited capability for work. The model doesn't apply (a), for "
        "a person under 21, or 21 having reached that age during the course, "
        "in non-advanced education without parental support, since it has no "
        "input for parental support; the other benefits in (b) (Scottish "
        "disability assistance, constant attendance allowance and war pension "
        "attendance payments), since it has no variables for them; or reg. "
        "60(2), so it keeps the protection after transitional protection would "
        "have ended. The model identifies foster parents through either input, "
        "uc_is_responsible_foster_parent_of_child_under_one or "
        "uc_is_foster_parent_or_new_friend_or_family_carer. A user can also "
        "set the second for a foster parent between placements, with no child "
        "placed, and for a friend or family carer, who is responsible for the "
        "child and so meets (c) under the law. In Northern Ireland the "
        "decision maker applies the same exceptions under reg. 14(1) of the "
        "Universal Credit Regulations (Northern Ireland) 2016, with regs. 6 "
        "and 12(1) of those Regulations in place of regs. 5 and 12(1A), and "
        "the same protection under reg. 61 of the Universal Credit "
        "(Transitional Provisions) Regulations (Northern Ireland) 2016, with "
        "regs. 6, 29 and 49 of "
        "those Regulations in place of regs. 8, 28 and 48: a claim ends a "
        "rate rebate before the award starts (reg. 6(2)), and a rent rebate "
        "or allowance runs on (reg. 6(2A)), as income-related ESA does under "
        "SR 2019/152 reg. 4 in place of SI 2019/1152 reg. 5. The model "
        "doesn't apply reg. 61(2) either."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/14",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/2",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/5",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/12",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/8",
        "https://www.legislation.gov.uk/uksi/2019/1152/regulation/5",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/28",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/48",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/49",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/60",
        "https://www.legislation.gov.uk/nisr/2016/216/regulation/6",
        "https://www.legislation.gov.uk/nisr/2016/216/regulation/12",
        "https://www.legislation.gov.uk/nisr/2016/216/regulation/14",
        "https://www.legislation.gov.uk/nisr/2016/226/regulation/6",
        "https://www.legislation.gov.uk/nisr/2019/152/regulation/4",
        "https://www.legislation.gov.uk/nisr/2016/226/regulation/29",
        "https://www.legislation.gov.uk/nisr/2016/226/regulation/49",
        "https://www.legislation.gov.uk/nisr/2016/226/regulation/61",
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
        # first, so a person entitled to an existing benefit on the
        # migration day took reg. 12(2) and keeps the protection while they
        # continue the course, after that award has ended. A course reg.
        # 12(2) doesn't cover left them meeting the condition that day, so
        # the protection needs a course it covers.
        migrated_student = (
            claimant_or_partner
            & benunit("claims_uc_at_legacy_closure", period)
            & ~person("is_qualifying_young_person_on_uc_migration_day", period)
            & undertakes_regulation_12_2_course(person, period)
        )
        return (
            disabled_with_limited_capability_for_work
            | responsible_for_child
            | single_foster_parent
            | student_couple_with_foster_partner
            | older_member_of_mixed_age_couple
            | migrated_student
        )
