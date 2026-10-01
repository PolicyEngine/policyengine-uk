"""Universal Credit work-related groups and the minimum income floor.

Welfare Reform Act 2012 ss. 19 to 22 sort claimants into four groups: no
work-related requirements (s. 19), the work-focused interview requirement only
(s. 20), the work preparation requirement (s. 21) and all work-related
requirements (s. 22). The minimum income floor of the Universal Credit
Regulations 2013 reg. 62 applies only to a claimant who "would, apart from this
regulation or regulation 90, fall within section 22", and the group sets each
claimant's individual threshold (reg. 90(2)).

A member of a couple is the responsible carer for a child only if the couple
nominate them (s. 19(6)(b)), and only one of them can be nominated (reg. 86(2)).
Several rules turn on that nomination: the group of the responsible carer of a
child under 3 (ss. 19(2)(c), 20(1)(a), 21(1)(aa)), the expected hours of the
responsible carer of a child under 13 (reg. 88(2)(aa) and (b)), and so each
partner's threshold and the couple threshold. Each rule is written here once,
as a function of the nomination. The variables call these functions with the
recorded nomination. The default nomination (uc_is_responsible_carer) calls
them with each member of the couple in turn and keeps the nomination that
leaves the couple the lower combined earned income.
"""

from policyengine_uk.model_api import *

# The groups in the order the Act tests them: section 21 covers a claimant
# who "does not fall within section 19 or 20", and section 22 one "not
# falling within any of sections 19 to 21".
NO_REQUIREMENTS = 0
INTERVIEW_ONLY = 1
WORK_PREPARATION = 2
ALL_REQUIREMENTS = 3
NOT_A_CLAIMANT = 4


def couple_members(person, period):
    """The claimant and any partner: at most two people in a benefit unit.

    A claim has at most two claimants. Where the data flag more (an adult
    child in the parents' benefit unit), the two eldest are the couple.
    """
    age = person("age", period)
    flagged = person("is_uc_claimant", period)
    return flagged & (person.get_rank(person.benunit, -age, condition=flagged) < 2)


def claimants(person, period):
    """The single claimant or the joint claimants.

    A partner who cannot be a joint claimant (reg. 3(3)) is a member of the
    couple but not a claimant: no work-related group or floor applies to them.
    """
    return couple_members(person, period) & ~person("uc_is_ineligible_partner", period)


def work_related_group(person, period, parameters, responsible_carer):
    """Each person's group apart from regs. 62 and 90, given the nomination.

    Regulation 90 puts a claimant whose earnings reach their threshold, and
    one treated as having the minimum income floor, in section 19. Regulation
    62(1)(b) asks where the claimant would fall apart from those routes, so
    neither is tested here.
    """
    p = parameters(period).gov.dwp.universal_credit.work_requirements
    child_age = p.responsible_carer.child_age
    youngest = person.benunit("uc_youngest_child_age", period)
    no_requirements = (
        # s. 19(2)(a): limited capability for work and work-related activity.
        person("uc_limited_capability_for_WRA", period)
        # s. 19(2)(b) with reg. 30: regular and substantial caring
        # responsibilities for a severely disabled person. The same flag
        # covers the 35-hour carers of reg. 89(1)(b).
        | person("is_carer_for_benefits", period)
        # s. 19(2)(c): the responsible carer for a child under the age of 1.
        | (responsible_carer & (youngest < child_age.no_requirements))
        # Reg. 89(1)(a): the qualifying age for State Pension Credit.
        | person("is_SP_age", period)
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
        # Reg. 91(2): foster parents, and friend or family carers in their
        # first 12 months.
        | person("uc_is_foster_parent_or_new_friend_or_family_carer", period)
    )
    work_preparation = (
        # s. 21(1)(a): limited capability for work.
        person("uc_has_limited_capability_for_work", period)
        # s. 21(1)(aa): the responsible carer for a child aged 2 (from 28
        # April 2014 to 2 April 2017, reg. 91A: aged 3 or 4).
        | (responsible_carer & (youngest < child_age.work_preparation))
    )
    return select(
        [
            ~claimants(person, period),
            no_requirements,
            interview_only,
            work_preparation,
        ],
        [NOT_A_CLAIMANT, NO_REQUIREMENTS, INTERVIEW_ONLY, WORK_PREPARATION],
        default=ALL_REQUIREMENTS,
    )


def expected_hours(person, period, parameters, responsible_carer):
    """Expected hours of work each week (reg. 88), given the nomination.

    The number is 35 unless a lesser number applies. The regulation leaves
    each lesser number to the Secretary of State. The model takes the hours
    DWP says it uses for the responsible carer of a child under 13, and 35
    for everyone else: it has no rule for the hours of a relevant carer
    (reg. 88(2)(a)) or a claimant with an impairment (reg. 88(2)(c)), which
    uc_expected_hours can take as an input.
    """
    p = parameters(period)
    hours = p.gov.dwp.universal_credit.work_requirements
    carer_hours = hours.responsible_carer.expected_hours
    youngest = person.benunit("uc_youngest_child_age", period)
    under_limit = responsible_carer & (youngest < carer_hours.child_age_limit)
    of_school_age = p.gov.dfe.compulsory_school_age.calc(youngest)
    lesser = where(
        of_school_age,
        # Reg. 88(2)(b): a child of compulsory school age under 13.
        carer_hours.compulsory_school_age,
        # Reg. 88(2)(aa): a child who has not reached compulsory school age.
        carer_hours.below_compulsory_school_age,
    )
    return where(
        under_limit,
        min_(lesser, hours.default_expected_hours),
        hours.default_expected_hours,
    )


def threshold_hours(person, period, parameters, group, hours):
    """Weekly hours behind each person's amount in the couple threshold.

    Regulation 90(2) gives a claimant who would otherwise be in section 22
    their expected hours, and one who would otherwise be in section 20 or 21
    16 hours. It sets no threshold for a claimant in section 19 for a reason
    other than earnings; the parameter records the hours the model uses for
    such a partner (none). For a partner who is not a joint claimant, reg.
    90(3)(b)(ii) adds the pay for 35 hours.
    """
    p = parameters(period).gov.dwp.universal_credit
    work = p.work_requirements
    floor = p.means_test.minimum_income_floor
    ineligible_partner = couple_members(person, period) & person(
        "uc_is_ineligible_partner", period
    )
    return select(
        [
            ineligible_partner,
            group == ALL_REQUIREMENTS,
            (group == INTERVIEW_ONLY) | (group == WORK_PREPARATION),
            group == NO_REQUIREMENTS,
        ],
        [
            work.default_expected_hours,
            hours,
            work.interview_or_preparation_threshold_hours,
            floor.no_requirements_partner_hours,
        ],
        default=0,
    )


def gross_threshold(person, period, parameters, weekly_hours):
    """The reg. 90(2) or 90(3)(b)(ii) amount for the hours, over a year.

    Regulation 90(2) uses the rate "a person of the same age as the claimant
    would be paid" under the National Minimum Wage Regulations 2015 reg. 4 or
    4A(1)(a) to (c): the rate for their age, never the apprenticeship rate of
    reg. 4A(1)(d). Regulation 90(3)(b)(ii) uses "the hourly rate specified in
    regulation 4", the national living wage rate, whatever the partner's age.
    """
    wage = parameters(period).gov.hmrc.minimum_wage.non_apprentice
    ineligible_partner = person("uc_is_ineligible_partner", period)
    hourly_rate = where(
        ineligible_partner,
        # The scale's top rate: the national living wage (the adult rate
        # before 1 April 2016).
        wage.calc(np.full(person.count, 200.0)),
        wage.calc(person("age", period)),
    )
    # Regulation 6(1A)(a) disregards fractions of a pound only in amounts
    # calculated for reg. 90 itself. Floors DWP has issued keep the pence:
    # 1,642.72 a month for 2025-26 from a threshold of 1,851.85 (12.21 x
    # 35 x 52 / 12; University of Bath IPR, "Going it alone", 2025,
    # "information supplied by the DWP"), where a whole-pound threshold
    # would give 1,642.09. So the threshold here is not rounded.
    return hourly_rate * weekly_hours * WEEKS_IN_YEAR


def income_tax_on_threshold(person, period, parameters, threshold):
    """Income tax on the threshold as the person's only income.

    Regulation 62(4)(b) deducts "such amount for income tax ... as the
    Secretary of State considers appropriate". The model treats the threshold
    as the person's only income: only the standard personal allowance
    applies, and no other allowance or relief.
    """
    income_tax = parameters(period).gov.hmrc.income_tax
    taxable = max_(0, threshold - income_tax.allowances.personal_allowance.amount)
    return where(
        person("pays_scottish_income_tax", period),
        income_tax.rates.scotland.rates.calc(taxable),
        income_tax.rates.uk.calc(taxable),
    )


def national_insurance_on_threshold(person, period, parameters, threshold):
    """National Insurance on the threshold as the person's only earnings.

    Class 2 and Class 4 on self-employed profits of that amount, as in DWP's
    figures, or primary Class 1 on pay of that amount where the parameter
    selects it (reg. 62(4)(b)).
    """
    p = parameters(period)
    ni = p.gov.hmrc.national_insurance
    # Primary Class 1 on pay equal to the threshold, with the annual
    # thresholds (weekly amounts times 52) the model uses for employees.
    class_1 = ni.class_1
    primary_threshold = class_1.thresholds.primary_threshold * WEEKS_IN_YEAR
    upper_earnings_limit = class_1.thresholds.upper_earnings_limit * WEEKS_IN_YEAR
    employee = class_1.rates.employee.main * max_(
        0, min_(threshold, upper_earnings_limit) - primary_threshold
    ) + class_1.rates.employee.additional * max_(0, threshold - upper_earnings_limit)
    # Class 2 and Class 4 on profits equal to the threshold.
    class_2 = (
        (threshold >= ni.class_2.small_profits_threshold)
        * ni.class_2.flat_rate
        * WEEKS_IN_YEAR
    )
    class_4 = ni.class_4
    class_4_amount = class_4.rates.main * max_(
        0,
        min_(threshold, class_4.thresholds.upper_profits_limit)
        - class_4.thresholds.lower_profits_limit,
    ) + class_4.rates.additional * max_(
        0, threshold - class_4.thresholds.upper_profits_limit
    )
    self_employed = class_2 + class_4_amount
    floor = p.gov.dwp.universal_credit.means_test.minimum_income_floor
    amount = where(floor.self_employed_national_insurance, self_employed, employee)
    # No primary Class 1, Class 2 or Class 4 is due from anyone the model
    # treats as not liable (under 16 or over State Pension age).
    return person("ni_liable", period) * amount


def net_threshold(person, period, parameters, gross):
    """The threshold converted to a net amount (reg. 62(4))."""
    deductions = income_tax_on_threshold(
        person, period, parameters, gross
    ) + national_insurance_on_threshold(person, period, parameters, gross)
    return max_(0, gross - deductions)


def floor_applies(person, period, group):
    """Whether reg. 62 applies to the person, given their group.

    Regulation 62(1): a claimant who is in gainful self-employment and would,
    apart from regs. 62 and 90, fall within section 22; reg. 62(5) leaves out
    start-up periods. A dependant, or a partner who is not a joint claimant,
    is in no group.
    """
    return (
        (group == ALL_REQUIREMENTS)
        & person("uc_is_in_gainful_self_employment", period)
        & ~person("uc_is_in_startup_period", period)
    )


def treated_earned_income(person, earned_income, threshold, applies, couple):
    """Earned income after the floor (reg. 62(2) and (3)).

    A single claimant below their threshold is treated as having the
    threshold (reg. 62(2)). A member of a couple is treated as having it only
    while the couple's combined earned income is also below the couple
    threshold, less any amount by which it and the partner's earned income
    would exceed that threshold (reg. 62(3)). For a single claimant the
    couple threshold is their own and reg. 62(3) reduces to reg. 62(2).
    Partners' earned income is their actual earned income: when both are
    below their thresholds each is treated as having their own, whichever
    partner's floor is applied first.
    """
    couple_earned_income = earned_income * couple
    partner_earned_income = (
        person.benunit.sum(couple_earned_income) - couple_earned_income
    )
    # Reg. 90(3): the sum of the joint claimants' individual thresholds, or
    # the claimant's threshold and the 35-hour amount for a partner who is
    # not a joint claimant.
    couple_threshold = person.benunit.sum(threshold * couple)
    below_individual_threshold = earned_income < threshold
    below_couple_threshold = earned_income + partner_earned_income < couple_threshold
    floor = threshold - max_(0, threshold + partner_earned_income - couple_threshold)
    return where(
        applies & couple & below_individual_threshold & below_couple_threshold,
        floor,
        earned_income,
    )


def combined_earned_income(person, period, parameters, responsible_carer):
    """The couple's combined earned income after the floor, for a nomination.

    Returned for each person's benefit unit.
    """
    couple = couple_members(person, period)
    group = work_related_group(person, period, parameters, responsible_carer)
    hours = expected_hours(person, period, parameters, responsible_carer)
    threshold = net_threshold(
        person,
        period,
        parameters,
        gross_threshold(
            person,
            period,
            parameters,
            threshold_hours(person, period, parameters, group, hours),
        ),
    )
    treated = treated_earned_income(
        person,
        person("uc_individual_earned_income_before_mif", period),
        threshold,
        floor_applies(person, period, group),
        couple,
    )
    return person.benunit.sum(treated * couple)
