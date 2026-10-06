from policyengine_uk.model_api import *
from policyengine_uk.utils.uc_work_related_requirements import claimants


class UCWorkRelatedGroup(Enum):
    NO_REQUIREMENTS = "No work-related requirements"
    INTERVIEW_ONLY = "Work-focused interview requirement only"
    WORK_PREPARATION = "Work preparation requirement"
    ALL_REQUIREMENTS = "All work-related requirements"
    NOT_A_CLAIMANT = "Not a claimant"


class uc_work_related_group_apart_from_earnings(Variable):
    value_type = Enum
    possible_values = UCWorkRelatedGroup
    default_value = UCWorkRelatedGroup.NOT_A_CLAIMANT
    entity = Person
    label = "Universal Credit work-related group, apart from the earnings thresholds"
    documentation = (
        "The work-related group the claimant would fall within apart from "
        "regulations 62 and 90 of the Universal Credit Regulations 2013: "
        "before asking whether their earnings reach their threshold, or "
        "whether the minimum income floor treats them as having such "
        "earnings, either of which would put them in the group subject to no "
        "work-related requirements. This is the test for the minimum income "
        "floor (reg. 62(1)(b)) and for each claimant's individual threshold "
        "(reg. 90(2))."
    )
    reference = [
        dict(
            title="Welfare Reform Act 2012 ss. 19 to 22",
            href="https://www.legislation.gov.uk/ukpga/2012/5/part/1/chapter/2/crossheading/application-of-workrelated-requirements",
        ),
        dict(
            title="Universal Credit Regulations 2013 regs. 89 and 91",
            href="https://www.legislation.gov.uk/uksi/2013/376/part/8/chapter/1/crossheading/workrelated-groups",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 62(1)(b)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/62",
        ),
        dict(
            title="State Pension Credit Act 2002 s. 1(6)",
            href="https://www.legislation.gov.uk/ukpga/2002/16/section/1",
        ),
    ]
    definition_period = YEAR

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.universal_credit.work_requirements
        child_age = p.responsible_carer.child_age
        responsible_carer = person("uc_is_responsible_carer", period)
        youngest = person.benunit("uc_youngest_child_age", period)
        no_requirements = (
            # s. 19(2)(a): limited capability for work and work-related
            # activity.
            person("uc_limited_capability_for_WRA", period)
            # s. 19(2)(b) with reg. 30: regular and substantial caring
            # responsibilities for a severely disabled person. The same flag
            # covers the 35-hour carers of reg. 89(1)(b). It does not apply
            # reg. 30(3), under which a person who "derives earned income
            # from those caring responsibilities" is not such a carer, so a
            # carer paid for that care still counts here.
            | person("is_carer_for_benefits", period)
            # s. 19(2)(c): the responsible carer for a child under the age
            # of 1.
            | (responsible_carer & (youngest < child_age.no_requirements))
            # Reg. 89(1)(a): the claimant "has reached the qualifying age
            # for state pension credit". That is State Pension Credit Act
            # 2002 s. 1(6), the meaning the phrase has in Welfare Reform Act
            # 2012 s. 4(4), carried into the regulations by Interpretation
            # Act 1978 s. 11. A man born before 6 December 1953 reached it
            # before his own State Pension age of 65.
            | person("has_attained_state_pension_credit_qualifying_age", period)
            # Reg. 89(1)(c): 11 weeks before to 15 weeks after confinement.
            | person("uc_is_in_pregnancy_or_post_confinement_period", period)
            # Reg. 89(1)(d): an adopter in the 12 months after placement.
            | person("uc_is_adopter_in_first_year", period)
            # Reg. 89(1)(da) and (e): students.
            | person("uc_is_student_with_no_work_related_requirements", period)
            # Reg. 89(1)(f): the responsible foster parent of a child under 1.
            | person("uc_is_responsible_foster_parent_of_child_under_one", period)
        )
        interview_only = (
            # s. 20(1)(a): the responsible carer for a child aged 1 (before 3
            # April 2017, aged at least 1 and under the prescribed age).
            (responsible_carer & (youngest < child_age.interview_only))
            # Reg. 91(2): foster parents, and friend or family carers in
            # their first 12 months.
            | person("uc_is_foster_parent_or_new_friend_or_family_carer", period)
        )
        work_preparation = (
            # s. 21(1)(a): limited capability for work.
            person("uc_has_limited_capability_for_work", period)
            # s. 21(1)(aa): the responsible carer for a child aged 2 (from 28
            # April 2014 to 2 April 2017, reg. 91A: aged 3 or 4).
            | (responsible_carer & (youngest < child_age.work_preparation))
        )
        # The Act tests the groups in order: section 21 covers a claimant
        # who "does not fall within section 19 or 20", and section 22 one
        # "not falling within any of sections 19 to 21". The earnings routes
        # into section 19 (reg. 90) are left out: reg. 62(1)(b) and reg.
        # 90(2) ask where the claimant would otherwise fall.
        return select(
            [
                ~claimants(person, period),
                no_requirements,
                interview_only,
                work_preparation,
            ],
            [
                UCWorkRelatedGroup.NOT_A_CLAIMANT,
                UCWorkRelatedGroup.NO_REQUIREMENTS,
                UCWorkRelatedGroup.INTERVIEW_ONLY,
                UCWorkRelatedGroup.WORK_PREPARATION,
            ],
            default=UCWorkRelatedGroup.ALL_REQUIREMENTS,
        )
