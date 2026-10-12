from policyengine_uk.model_api import *


class uc_minimum_income_floor_gross(Variable):
    value_type = float
    entity = Person
    label = "Universal Credit minimum income floor individual threshold (gross)"
    documentation = (
        "The person's individual threshold before the deductions for income "
        "tax and National Insurance: the National Minimum Wage hourly rate "
        "for their age (never the apprenticeship rate) times a number of "
        "hours each week, over a year. The hours are the person's expected "
        "hours where they would otherwise be subject to all work-related "
        "requirements, and 16 where they would otherwise be subject to the "
        "work-focused interview requirement only or the work preparation "
        "requirement. The regulations set no threshold for a claimant "
        "subject to no work-related requirements for a reason other than "
        "earnings, who adds nothing to a couple threshold. A partner who "
        "cannot be a joint claimant has no threshold either; the amount here "
        "is what they add to the couple threshold, the pay for 35 hours at "
        "the national living wage."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Universal Credit Regulations 2013 reg. 90(2) and (3)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/90",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 88",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/88",
        ),
        dict(
            title="National Minimum Wage Regulations 2015 regs. 4 and 4A",
            href="https://www.legislation.gov.uk/uksi/2015/621/regulation/4A",
        ),
    ]

    def formula(person, period, parameters):
        p = parameters(period)
        work = p.gov.dwp.universal_credit.work_requirements
        floor = p.gov.dwp.universal_credit.means_test.minimum_income_floor
        wage = p.gov.hmrc.minimum_wage.non_apprentice
        group = person("uc_work_related_group_apart_from_earnings", period)
        groups = group.possible_values
        ineligible_partner = person("is_uc_assessed_claimant", period) & person(
            "uc_is_ineligible_partner", period
        )
        hours = select(
            [
                # Reg. 90(3)(b)(ii): a partner who is not a joint claimant
                # adds "the amount a person would be paid for 35 hours per
                # week" to the couple threshold.
                ineligible_partner,
                # Reg. 90(2)(b): "the expected number of hours per week in
                # the case of a claimant who would otherwise fall within
                # section 22".
                group == groups.ALL_REQUIREMENTS,
                # Reg. 90(2)(a): "16 hours per week, in the case of a
                # claimant who would otherwise fall within section 20 ... or
                # section 21".
                (group == groups.INTERVIEW_ONLY) | (group == groups.WORK_PREPARATION),
                # Reg. 90(2) sets no threshold for a claimant in section 19
                # for a reason other than earnings; the parameter holds the
                # hours the model uses for such a partner (none).
                group == groups.NO_REQUIREMENTS,
            ],
            [
                floor.ineligible_partner_hours,
                person("uc_expected_hours", period),
                work.interview_or_preparation_threshold_hours,
                floor.no_requirements_partner_hours,
            ],
            default=0,
        )
        # Reg. 90(2) uses the rate "a person of the same age as the claimant
        # would be paid" under NMW Regs reg. 4 or 4A(1)(a) to (c): the rate
        # for their age, never the apprenticeship rate of reg. 4A(1)(d). Reg.
        # 90(3)(b)(ii) uses "the hourly rate specified in regulation 4", the
        # national living wage rate, whatever the partner's age: the scale's
        # top rate (the adult rate before 1 April 2016).
        hourly_rate = where(
            ineligible_partner,
            wage.calc(np.full(person.count, 200.0)),
            wage.calc(person("age", period)),
        )
        # Reg. 6(1A)(a) disregards fractions of a pound only in amounts
        # calculated for reg. 90 itself. Floors DWP has issued keep the pence:
        # 1,642.72 a month for 2025-26 from a threshold of 1,851.85 (12.21 x
        # 35 x 52 / 12; University of Bath IPR, "Going it alone", 2025,
        # "information supplied by the DWP"), where a whole-pound threshold
        # would give 1,642.09. So the threshold here is not rounded.
        return hourly_rate * hours * WEEKS_IN_YEAR
